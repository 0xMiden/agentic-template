# Disposable counter node

Run from the repository root after `bash scripts/journey.sh contracts`:

```bash
MIDEN_ALLOW_LOCAL=1 bash scripts/journey.sh local
```

This starts a new fee-free loopback chain, executes the counter's publish/consume
flow with local proving, checks both commitments and the final count, then
stops only its own uniquely named Docker Compose project. It preserves all
existing state. Docker and the project's Rust nightly are required.

Node components and the genesis utility are digest-pinned v0.17.0 images;
Rust client/store are pinned 0.17.2. This node version is the resolution in
[rust-sdk v0.17.2's Cargo.lock](https://github.com/0xMiden/rust-sdk/blob/v0.17.2/Cargo.lock).
The startup sequence follows its
[released helper](https://github.com/0xMiden/rust-sdk/blob/v0.17.2/scripts/start-test-node.sh)
and the node's v0.17.0 genesis utility. Public insecure storage-key fixtures
are documented in `fixtures/README.md`; use only disposable chains.

RPC58291 and HTTP health58292 bind only to 127.0.0.1. Other component ports
stay inside the container. To select other ports or inject a failure:

```bash
python3 scripts/local_node.py --rpc-port 59291 --health-port 59292
python3 scripts/local_node.py --expected-count 2
```

The second command intentionally returns nonzero after confirming both commits,
because one increment produces 1. The Rust binary also rejects external RPC,
existing client state and fee-charging chains. Unavailable RPC returns nonzero.

Each run writes `local-node-runs/<id>/report.json`, `validator.log` and
`node.log`. JSON fields include `kind: real-local-node`, `node_ready`,
`validator_exit_code`, `node_error_count`, `node_stopped` and `passed`.
Containers, networks, chain state and client keys remain for inspection.
Use the recorded Compose project ID for cleanup under your own cleanup policy;
this runner stops services but never deletes state.

Verified on arm64 Docker: publication and consumption committed, counter=1,
exit0, node_error_count=0, node stopped. Injected expected2 returned exit1;
external/unavailable RPC and existing state returned exit1. Startup warnings
about thread priority, disabled admission and temporarily unreachable
ntx-builder occur while components bind; no ERROR-level events were recorded
in the successful acceptance run.

This evidence covers this public fee-free counter. It does not establish
fee-funded admission, private-note transport, browser/wallet use, Playground
USDCx minting or network account upgrades. Genesis creates only disposable
local assets; no mainnet/testnet or valuable transactions are involved.
