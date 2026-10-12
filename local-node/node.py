"""Fee-free node from released v0.17.0 binaries; public insecure test fixtures only."""
import http.server
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request

DATA = Path('/data')
CHILDREN = []

def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def start(*args):
    child = subprocess.Popen(args)
    CHILDREN.append(child)
    return child

def stop(*_):
    for child in CHILDREN:
        if child.poll() is None:
            child.terminate()
    for child in CHILDREN:
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
    sys.exit(0)

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

try:
    # No reset path: Docker must receive a new disposable directory each run.
    for name in ['usdcx', 'genesis', 'accounts', 'validator', 'node', 'ntx']:
        (DATA / name).mkdir()
    distributor = ''
    config = {'accounts': {'owner': distributor, 'attest_admins': [], 'pausers': [], 'unpausers': [], 'blocklist_managers': []},
              'faucet': {'seed': '0x55534443582d4641554345540000000000000000000000000000000000000000',
                         'token_supply': 1000000000000000, 'domain': 10007, 'min_burn_amount': 1,
                         'verification_base_fee': 0, 'attesters': []}}
    # Genesis utility writes its accounts into its current working directory.
    import os
    os.chdir(DATA / 'usdcx')
    output = run('miden-usdcx-genesis', 'new-distributor')
    distributor = next(line.split('hex:')[1].strip() for line in output.splitlines() if line.strip().startswith('hex:'))
    config['accounts']['owner'] = distributor
    Path('config.json').write_text(json.dumps(config))
    print(run('miden-usdcx-genesis', 'faucet'))
    print(run('miden-usdcx-genesis', 'prefund'))
    signing = '9cbcf0fc18b2a4afeff56ef43ad96af92e804fae64615c9802cff2a182e9cae2'
    pubkey = run('miden-validator', 'pubkey', '--signing-key.hex', signing).strip()
    print(run('miden-validator', 'genesis', '--genesis-block-directory', str(DATA / 'genesis'),
              '--accounts-directory', str(DATA / 'accounts'), '--native-faucet', str(DATA / 'usdcx/usdcx-faucet.mac'),
              '--funding-account', str(DATA / 'usdcx/distributor.genesis.mac'), '--verification-base-fee', '0',
              '--timestamp', str(int(time.time())), '--validator.key', pubkey))
    for binary, directory in [('miden-validator', 'validator'), ('miden-node', 'node'), ('miden-ntx-builder', 'ntx')]:
        print(run(binary, 'bootstrap', '--data-directory', str(DATA / directory), '--genesis', str(DATA / 'genesis/genesis.dat')))
    start('miden-validator', 'start', '--listen', '127.0.0.1:50101', '--data-directory', str(DATA / 'validator'),
          '--signing-key.hex', signing, '--encryption-key.hex', '9964dbb2590adeb415d3291b64a0a9991fbcac5adacb05ee17efee5296d081d7',
          '--storage-key.epoch', '09' * 32, '--storage-key.setup-context', '/fixtures/setup-context.wire',
          '--storage-key.public-key-set', '/fixtures/public-key-set.wire', '--storage-key.secret-share', '/fixtures/secret-share.wire')
    for attempt in range(30):
        if CHILDREN[0].poll() is not None:
            raise RuntimeError('Validator exited before readiness')
        try:
            socket.create_connection(('127.0.0.1', 50101), timeout=1).close()
            break
        except OSError:
            time.sleep(1)
    else:
        raise RuntimeError('Validator readiness timeout')
    print(run('miden-node', 'fee-collector', 'create', '--data-directory', str(DATA / 'node')))
    print(run('miden-node', 'fee-collector', 'deploy', '--data-directory', str(DATA / 'node'), '--validator.url', 'http://127.0.0.1:50101'))
    start('miden-node', 'sequencer', '--rpc.listen', '0.0.0.0:57291', '--data-directory', str(DATA / 'node'),
          '--validator.url', 'http://127.0.0.1:50101', '--ntx-builder.url', 'http://127.0.0.1:50301',
          '--rpc.network-tx-auth-header-value', 'local-counter-only', '--batch.builder.wallet-account-id', '0xcc0000000000dd010000ee000000ff',
          '--disable-account-allowlist', '--block.interval', '3s', '--batch.interval', '1s')
    start('miden-remote-prover', '--kind=transaction', '--port=50051', '--timeout', '300s', '--capacity', '8')
    time.sleep(2)
    start('miden-ntx-builder', 'start', '--listen', '127.0.0.1:50301', '--rpc.url', 'http://127.0.0.1:57291',
          '--rpc.auth-header-value', 'local-counter-only', '--tx-prover.url', 'http://127.0.0.1:50051', '--tx-prover.timeout', '300s',
          '--max-cycles', str(1 << 18), '--data-directory', str(DATA / 'ntx'))

    class Health(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                if self.path != '/healthz' or any(c.poll() is not None for c in CHILDREN):
                    raise RuntimeError('Node component unavailable')
                with urllib.request.urlopen('http://127.0.0.1:57291/', timeout=2) as reply:
                    reply.read()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'healthy')
            except Exception:
                self.send_response(503)
                self.end_headers()
        def log_message(self, *_):
            pass
    server = http.server.ThreadingHTTPServer(('0.0.0.0', 8080), Health)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    while all(c.poll() is None for c in CHILDREN):
        time.sleep(1)
    raise RuntimeError('Node component exited')
except Exception as error:
    print(f'Local node failed: {error}', file=sys.stderr)
    if isinstance(error, subprocess.CalledProcessError):
        print(error.stdout, error.stderr, file=sys.stderr)
    for child in CHILDREN:
        child.terminate()
    sys.exit(1)
