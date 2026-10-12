# Build a first Miden app with an agent — v0.17

Start with the counter in this workspace, prove its state transition, then reuse
that flow for your app. The automated checks and remaining runtime gates are
listed below.

## 1. Acquire matching context

Clone recursively and preserve the checked-in submodule pins and lockfiles
until you deliberately migrate.

```bash
git clone --recurse-submodules https://github.com/0xMiden/agentic-template.git
cd agentic-template
```

This guide targets the dependency pins below. If your checkout differs, inspect
the release context before applying these commands.

| Resource | Read it for |
| --- | --- |
| Root `AGENTS.md` and `CLAUDE.md` | Agent entry, pinned context, gates and evidence |
| `project-template/README.md`, `CLAUDE.md`, `.claude/skills/` | Rust contracts, client, MockChain and local-node patterns |
| `frontend-template/AGENTS.md`, `CLAUDE.md` | Browser app flow and installed SDK guidance |
| Installed `@miden-sdk/*/AGENTS.md` and synced skills | APIs matching the installed browser packages |
| [Agent tools](https://github.com/0xMiden/agent-tools) | Shared protocol/MASM/review guidance; follow its install instructions |
| [Migration guide](https://docs.miden.xyz/next/builder/migration/) | Migration details; confirm the page displays v0.17, since `/next` can advance |
| [Release dashboard](https://brianseong99.github.io/miden-release-dashboard/?release=0.17) | Dependency/release status and documentation publication |

Frontend install already syncs ten SDK skills via `@miden-sdk/create@0.17.0`.
Do not duplicate those skills manually. Its `prepare` tolerates errors; check
`.claude/skills/` and run `yarn miden-skills sync` if synchronization failed.
Claude-specific slash commands/hooks are not guaranteed to execute in other
agents: run the journey commands explicitly and read their output.

| Layer | Reviewed baseline |
| --- | --- |
| Project submodule | `e941949b1cb244f1557ace1c58dca0dc7a898da8` |
| Frontend submodule | `71fb5bb0a205224d04a7d0264fad2cecc8d4478d` |
| Miden channel / compiler / guest SDK | `0.17.0` / `0.11.0` / `0.15.0` |
| Protocol / Rust client and store / VM | `0.17.1` / `0.17.2` / `0.35.0` |
| Browser core / React, adapters, tooling | `0.17.1` / `0.17.0` |
| Rust contract toolchain | `nightly-2026-09-01`, from the checked-in file |

These versions differ intentionally. A release called v0.17 does not mean
changing every dependency to 0.17.0. Use the checked-in resolution.

## 2. Diagnose, install, build and test

Install Rust/rustup, current manifest-compatible midenup, Node 18+ and Yarn
Classic 1. The script diagnoses prerequisites without installing them:

```bash
bash scripts/journey.sh doctor
bash setup.sh
bash scripts/journey.sh contracts
bash scripts/journey.sh frontend
```

The setup installs the channel in `project-template/miden-toolchain.toml`
instead of mutable `stable`, preserves the frontend lockfile, and compiles
contracts from their directories. Contract tests run from `integration`, since
helpers resolve `../contracts` relative to their working directory. The test
builds both packages and asserts the MockChain counter transition.

Ask your agent: “Read AGENTS.md and the installed version-matched guidance.
Explain the counter account, increment note and two transactions from source.
Run doctor, then the authorized build/test stages. Report exact evidence and
blocked gates before changing behavior.”

## 3. Testnet counter → browser handoff

Use a fresh clone/worktree and a fresh browser profile for this demo. Preserve
existing keys and stores; do not reset them as an error recovery shortcut.
The binary creates `project-template/keystore/` and `store.sqlite3`.

```bash
MIDEN_ALLOW_TESTNET=1 bash scripts/journey.sh testnet
```

This explicitly opts into testnet submissions. The binary prints counter and
sender IDs; request public funding notes for both from the
[testnet faucet](https://faucet.testnet.miden.io/) while it waits. It publishes
then consumes the increment note, waits for both commitments and asserts
`Verified committed counter value: 1`. It can report account registration is
required; follow that chain's admission process rather than bypassing it.
The public counter uses NoAuth + BasicWallet: anyone can act on it. Test tokens
only; this is a demonstration, not an authenticated application design.

```bash
bash scripts/journey.sh artifacts
# Set VITE_MIDEN_COUNTER_ADDRESS=<printed counter ID> in frontend-template/.env.local
(cd frontend-template && yarn dev)
```

The script copies rebuilt format-7 packages under the hyphenated filenames the
frontend expects. Open the Vite URL (normally localhost:5173) and confirm the
count reads 1 and becomes 2 after publish/consume commitments. The browser
uses its local WebClient and testnet remote proving; this counter needs no
wallet extension. Custom RPCs require explicitly matching faucet/prover
configuration. Restart Vite after changing environment variables.

## 4. Extend the app and earn the remaining gates

Define state invariants and expected failures, implement contracts, add
MockChain assertions, then validate your app against a real local node before
claiming the full build workflow is complete. Neither `validate_local.rs` nor
its Cargo target ships at these pins. The old `miden-node bundled start` command
is not the pinned skill's v0.17 recipe.

Use `project-template/.claude/skills/local-node-validation/SKILL.md` and the
[released rust-sdk v0.17.2 helper](https://github.com/0xMiden/rust-sdk/blob/v0.17.2/scripts/start-test-node.sh).
Create an app-specific localhost client/binary with separate state, matching
genesis and split validator/sequencer/prover/ntx-builder services. Verify
publication, consumption, commitment, final assertions and component logs.
Private-note delivery additionally needs the matching transport service and
explicit delivery checks. Follow your environment’s service-isolation policy when starting a node.
The journey script does not launch services automatically.

Before adding a UI, copy fresh packages and mirror the proven Rust transaction
flow. Serialize direct WASM access via `runExclusive`; avoid nesting SDK hooks
that already acquire that lock. Validate real signers separately if your app
adds wallet integration. Review authentication and account upgrades from the
pinned skills; MockChain coverage alone does not establish network upgrade
consumption.

## Recover from a failed stage

| Symptom | Check and next action |
| --- | --- |
| Missing binary / source directory | Initialize pinned submodules; do not run absent `validate_local` |
| Old midenup rejects manifest or migration | Upgrade midenup; preserve existing home/state. A fresh task-local `MIDENUP_HOME` avoids destructive reset |
| Rust MSRV error using stable | Run from `project-template/integration`, so the checked-in nightly applies; keep lockfile |
| Package parse/version error | Rebuild under channel 0.17.0 and copy both fresh format-7 MASPs |
| Counter unconfigured/not found | Supply deployed public compatible ID on the same chain; restart Vite |
| Funding wait / expired challenge | Inspect account registration, funding note ID and sync state; bounded timeout is not cancellation |
| Browser recursive WASM error | Serialize direct calls; do not wrap mutation hooks in nested locks |
| RPC version/genesis rejection | Align client/node/prover/transport and fresh disposable state; do not overwrite real keys |
| Hook says checks passed | Inspect every stage; unit/build success does not prove browser or local-node completion |

## What the evidence establishes

Merged [agent-tools PR18](https://github.com/0xMiden/agent-tools/pull/18),
[project PR67](https://github.com/0xMiden/project-template/pull/67) and
[frontend PR31](https://github.com/0xMiden/frontend-template/pull/31) report
counter validation. The commands above were checked against the pinned baseline:
1 MockChain counter test, 53 frontend tests, typecheck, production build and
6 stage-runner tests passed. Run the stage-runner tests with
`python3 -m unittest discover -s tests -v`.
Fresh testnet funding, browser interaction, wallet-extension use, complete
local-node setup and network account-upgrade consumption are separate gates.

[Playground PR669](https://github.com/walnuthq/miden-playground/pull/669) records
faster faucet PoW and a successful request returning a note ID; its wallet
tutorial checkboxes remain unchecked. That does not establish USDCx mint,
consume and balance update end to end. Bobbin's later mint concern remains
unresolved by this evidence. Verify the deployed flow before recommending it
as the primary successful first-app path.
