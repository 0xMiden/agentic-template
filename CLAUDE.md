# Miden Agentic Template

This monorepo contains two Miden development templates as git submodules:

- `project-template/` -- Miden smart contracts (Rust SDK). Account components, note scripts, transaction scripts, and integration tests.
- `frontend-template/` -- Miden web frontend (React + TypeScript + @miden-sdk/react). Browser-based UI that interacts with Miden contracts.

Each sub-template has its own CLAUDE.md with detailed instructions, skills for domain-specific patterns, and hooks for automated verification. These load automatically when you start working in either directory.

## Development Workflow

**Contracts first, validate against local node, then frontend.** Frontend work is gated on local-node validation passing.

1. Build smart contracts in `project-template/`
   - Write account components, note scripts, and tx scripts in `project-template/contracts/`
   - Contracts compile to `.masp` package files

2. Validate with MockChain tests
   - Write and run MockChain integration tests in `project-template/integration/tests/`
   - Validate state transitions, note lifecycle, and expected outputs
   - Exit criteria: all MockChain tests pass with explicit assertions

3. Local-node validation **(GATE -- must pass before frontend)**
   - Write Rust client binaries in `project-template/integration/src/bin/` that exercise the full contract flow against a local Miden node
   - Start local node: `miden-node bundled start --data-directory local-node-data --rpc.url http://0.0.0.0:57291`
   - Run: `cd project-template && cargo run --bin validate_local --release`
   - Verify: transaction success/failure paths, state transitions, note lifecycle, clean node logs
   - See the `local-node-validation` skill for the full checklist and setup guide
   - Exit criteria: all state assertions pass, node logs are clean

4. Copy artifacts and deploy
   - Deploy contracts to testnet using integration binaries
   - Copy `.masp` files from `project-template/masm-output/` (or the contract's `target/` directory) into `frontend-template/public/packages/`
   - The frontend loads these at runtime via the Miden SDK

5. Build the frontend in `frontend-template/`
   - React components use `@miden-sdk/react` hooks to interact with contracts
   - Mirror the validated Rust binary flow as closely as possible
   - TDD workflow: write tests first, then implement
   - Automated hooks verify type safety and test coverage on every edit

## Which Directory to Work In

| Task | Directory |
|------|-----------|
| Write or edit smart contracts | `project-template/contracts/` |
| Write or edit integration tests | `project-template/integration/tests/` |
| Validate contracts against local node | `project-template/integration/src/bin/` |
| Deploy contracts to testnet | `project-template/integration/src/bin/` |
| Write or edit frontend components | `frontend-template/src/` |
| Write or edit frontend tests | `frontend-template/src/__tests__/` |

## Automated Verification

Hooks run automatically on every file edit:
- Editing files in `project-template/contracts/` triggers `cargo miden build` on the modified contract
- Editing files in `frontend-template/src/` triggers TypeScript type checking and affected test runs

On task completion, a full verification runs: contract integration tests + frontend tests + typecheck + build.

## Quick Reference

**Build a contract:**
```
cargo miden build --manifest-path project-template/contracts/<name>/Cargo.toml --release
```

**Run contract integration tests:**
```
cd project-template && cargo test -p integration --release
```

**Start local Miden node:**
```
cd project-template && miden-node bundled start --data-directory local-node-data --rpc.url http://0.0.0.0:57291
```

**Run local-node validation:**
```
cd project-template && cargo run --bin validate_local --release
```

**Start frontend dev server:**
```
cd frontend-template && yarn dev
```

**Run frontend tests:**
```
cd frontend-template && npx vitest --run
```
