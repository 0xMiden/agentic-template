#!/usr/bin/env python3
"""Run the app-specific counter on a new loopback Docker chain; preserve all state."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time
import uuid
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def new_state(directory):
    directory.mkdir()  # FileExistsError is intentional: never reset a store.
    return directory

def local_endpoint(value):
    match = re.fullmatch(r'http://127\.0\.0\.1:([0-9]+)', value)
    if not match or not 1 <= int(match[1]) <= 65535:
        raise ValueError('Only http://127.0.0.1:<nonzero-port> is accepted')
    return int(match[1])

def run_validator(command, output=None):
    if output is None:
        return subprocess.run(command, timeout=200).returncode
    with output.open('w') as log:
        result = subprocess.run(command, timeout=200, stdout=log, stderr=subprocess.STDOUT)
    print(output.read_text(), flush=True)
    return result.returncode

def free_port(port):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', port))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rpc-port', type=int, default=58291)
    parser.add_argument('--health-port', type=int, default=58292)
    parser.add_argument('--expected-count', type=int, default=1, help='Set 2 to inject a final-state assertion failure')
    args = parser.parse_args()
    rpc = f'http://127.0.0.1:{args.rpc_port}'
    local_endpoint(rpc)
    local_endpoint(f'http://127.0.0.1:{args.health_port}')
    if args.rpc_port == args.health_port:
        raise ValueError('RPC and health ports must differ')
    free_port(args.rpc_port)
    free_port(args.health_port)
    # Nothing is started or written before port validation.
    run_id = uuid.uuid4().hex[:12]
    runs = ROOT / 'local-node-runs'
    runs.mkdir(exist_ok=True)
    run_dir = new_state(runs / run_id)
    node_state = new_state(run_dir / 'node')
    env = dict(os.environ, MIDEN_LOCAL_NODE_STATE=str(node_state),
               MIDEN_LOCAL_RPC_PORT=str(args.rpc_port), MIDEN_LOCAL_HEALTH_PORT=str(args.health_port))
    compose = ['docker', 'compose', '-p', f'miden-counter-{run_id}', '-f', str(ROOT / 'local-node/compose.yml')]
    report = {'run_id': run_id, 'rpc': rpc, 'state': str(run_dir), 'node_version': '0.17.0',
              'client_version': '0.17.2', 'expected_count': args.expected_count,
              'kind': 'real-local-node', 'passed': False}
    code = 1
    started = False

    def terminate(signum, _frame):
        nonlocal code
        code = 128 + signum
        report['passed'] = False
        report['error'] = 'Interrupted by SIGTERM'
        raise SystemExit(code)

    signal.signal(signal.SIGTERM, terminate)
    try:
        # Pinned Rust nightly and Cargo.lock, separate from the guest compiler pin.
        target = ROOT / 'tools/local-counter-target'
        build_env = dict(env, CARGO_TARGET_DIR=str(target))
        subprocess.run(['cargo', '+nightly-2026-09-01', 'build', '--release', '--locked',
                        '--manifest-path', str(ROOT / 'examples/local-counter/Cargo.toml')], check=True, env=build_env)
        subprocess.run(compose + ['build'], check=True, env=env)
        started = True
        subprocess.run(compose + ['up', '-d'], check=True, env=env)
        ready = False
        for _ in range(120):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{args.health_port}/healthz', timeout=2) as reply:
                    ready = reply.status == 200
                if ready:
                    break
            except OSError:
                pass
            time.sleep(1)
        if not ready:
            raise RuntimeError('Local-node HTTP health did not become ready within 120 attempts')
        report['node_ready'] = True
        command = [str(target / 'release/local-counter-validation'), rpc, str(run_dir / 'client'),
                   str(ROOT / 'project-template/contracts'), str(args.expected_count)]
        report['validator_command'] = command
        print(f'EVIDENCE {run_dir}', flush=True)
        code = run_validator(command, run_dir / "validator.log")
        report["validator_log"] = "validator.log"
        report['validator_exit_code'] = code
        report['passed'] = code == 0
    except subprocess.CalledProcessError as error:
        code = error.returncode
        report['error'] = str(error)
    except Exception as error:
        report['error'] = str(error)
        print(str(error), file=sys.stderr)
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if started:
            with (run_dir / 'node.log').open('w') as log:
                logs = subprocess.run(compose + ['logs', '--no-color'], env=env, stdout=log, stderr=subprocess.STDOUT)
            node_log = (run_dir / 'node.log').read_text()
            report['node_error_count'] = None if logs.returncode else len(re.findall(r'\bERROR\b', node_log))
            if (logs.returncode or report['node_error_count']) and code == 0:
                code = 1
                report['passed'] = False
            # Stop only this owned project. Containers/state remain for review.
            stopped = subprocess.run(compose + ['stop'], env=env)
            report['node_stopped'] = stopped.returncode == 0
            if stopped.returncode != 0 and code == 0:
                code = stopped.returncode
                report['passed'] = False
        (run_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report), flush=True)
    return code

if __name__ == '__main__':
    sys.exit(main())
