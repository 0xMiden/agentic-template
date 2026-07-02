# Miden Agentic Template

This monorepo contains two Miden development templates as git submodules:

- `project-template/` -- Miden smart contracts (Rust SDK). Account components, note scripts, transaction scripts, and integration tests.
- `frontend-template/` -- Miden web frontend (React + TypeScript + @miden-sdk/react). Browser-based UI that interacts with Miden contracts.

Each sub-template has its own CLAUDE.md with detailed instructions, skills for domain-specific patterns, and hooks for automated verification. These load automatically when you start working in either directory.

## Usage Modes

This template supports two modes.

**Build a Miden dapp (primary).** Follow the build pipeline below: write contracts in `project-template/`, validate them with MockChain tests, gate on local-node validation, copy artifacts, then build the frontend in `frontend-template/`. Frontend work is gated on local-node validation passing. See `## Development Workflow` and `## Quick Reference`.

**Research, Q&A, application planning (additive).** Use the parent root as a Miden knowledge entry point: load skills from the sources documented in `## Skill Sources`, follow the per-mode guidance in `## Research and Q&A Workflows`. No build pipeline required to answer questions or plan an application. This mode is additive and does not exempt build agents from the `## Development Workflow` gates.

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

## Skill Sources

Three skill sources are available to agents launched at the parent root. Every name below was verified against the actual `SKILL.md` file (submodules) or the live `0xMiden/agent-tools` GitHub directory listing.

**Precedence rule.** When the same skill exists in a submodule and in `agent-tools`, prefer the submodule version: it is tailored for the app-developer template context and may carry sections specific to this template's flow. Fall back to `agent-tools` only when the topic is not covered downstream.

### `project-template/.claude/skills/` (7 skills, app-developer)

| Skill | When to load it |
|---|---|
| `miden-concepts` | foundational Miden questions: actor model, accounts, notes, transactions, assets, privacy, P2ID/P2IDE/SWAP, Felt/Word semantics. |
| `rust-sdk-patterns` | writing or reviewing Miden contract code (`#[component]`, `#[note]`, `#[tx_script]`), storage, native functions, asset handling, P2ID output notes, cross-component calls. |
| `rust-sdk-pitfalls` | debugging contract code or asking about felt arithmetic, comparison ops, 4-Word arg limits, storage naming, no-std, P2ID roots, NoteType ctors, note-to-component boundaries, note input immutability. |
| `rust-sdk-testing-patterns` | writing MockChain integration tests: account / note creation, storage verification, multi-tx tests, output-note assertions, asset-bearing notes. |
| `rust-sdk-source-guide` | advanced multi-contract patterns or exploring `protocol`, `compiler`, `rust-sdk`, `tutorials` source repos. Documents Plan Mode and verification-driven dev for contract work. |
| `local-node-validation` | MockChain tests pass and the contract needs to be validated against a real local Miden node before the frontend phase. |
| `miden-client-cli` | installing or using the `miden client` CLI via midenup or direct `cargo install`; canonical command and config reference. Project-template only. |

### `frontend-template/.claude/skills/` (8 skills, app-developer)

| Skill | When to load it |
|---|---|
| `miden-concepts` | same triggers as the project-template version; prefer the project-template copy when both are available. |
| `react-sdk-patterns` | building a Miden frontend with `@miden-sdk/react`: MidenProvider, query hooks, mutation hooks, transaction stages, signer integration, utilities. |
| `signer-integration` | wiring Para, Turnkey, MidenFi wallet adapter, or building a custom signer (`SignerContextValue`). |
| `web-client-usage` | using the raw web SDK (`@miden-sdk/miden-sdk`) for things hooks do not cover: custom contracts, private-note transport, lazy init, `compile`, `keystore`, sync ordering. |
| `vite-wasm-setup` | configuring Vite for Miden: `midenVitePlugin()`, COOP/COEP headers, dev and production deployment headers, TypeScript compatibility. |
| `frontend-pitfalls` | debugging a frontend bug: WASM init race, recursive WASM access, COOP/COEP misconfig, BigInt mismatch, Bech32 network mismatch, IndexedDB state loss, auto-sync side effects, StrictMode double-init. |
| `testing-patterns` | writing Vitest + testing-library tests for Miden React components (`@miden-sdk/react` mock factory, fixtures, transaction-stage simulation). |
| `frontend-source-guide` | advanced frontend patterns or exploring `web-sdk` source for custom hooks, custom signers, raw `WasmWebClient` usage. |

### `0xMiden/agent-tools` (22 skills upstream, fallback)

Repository: `https://github.com/0xMiden/agent-tools`. 13 of the 22 skills are mirrored in the submodules above (use the submodule version per the precedence rule). The other 9 are upstream-only and not present in either submodule.

**MASM family (6, upstream-only).** Reach for these whenever the topic is MASM authoring, formatting, or debugging.

- `masm-formatting` -- orchestrator: capitalization (`UPPER_SNAKE_CASE` for Words, lower for felts), `(N)` span family, `Cycles:` section, chained `u32assert2` guards.
- `masm-inline-comments` -- inline `# => [...]` stack-state comments, lowercase, do-not-overcomment.
- `masm-doc-comments` -- procedure doc blocks: Description, Inputs, Outputs, Where, Panics if, Invocation.
- `masm-padding` -- `pad(N)` rules for `call` vs `exec`, stack depth floor of 16.
- `masm-constants` -- constant placement, error code organization, memory pointer naming.
- `masm-file-structure` -- section ordering for `.masm` files, header format.

**Contributor-focused (3, upstream-only).** Useful when working inside the `miden-client` codebase itself rather than building on top of it.

- `rust-client-patterns` -- conventions for the `miden-client` Rust crates (`rust-client`, `sqlite-store`, `idxdb-store`, `web-client`).
- `idxdb-patterns` -- IndexedDB / Dexie persistence layer in `miden-client/idxdb-store`.
- `wasm-bridge` -- Rust to JS WASM boundary in `miden-client/web-client`.

### Deployment

`agent-tools` is not bundled with this template. The cleanest path is to install it once at the user level so Claude Code auto-discovers both skills and slash commands across all projects:

```
git clone https://github.com/0xMiden/agent-tools.git ~/agent-tools

# Ensure user-level Claude Code surfaces exist (no-op if they already do)
mkdir -p ~/.claude/skills ~/.claude/commands

# Skills: link the skills directory into Claude Code's user-level skills
ln -sf ~/agent-tools/skills/* ~/.claude/skills/

# Slash commands: link the command files into Claude Code's user-level commands
ln -sf ~/agent-tools/commands/*.md ~/.claude/commands/
```

Skills and slash commands live in different upstream subdirectories (`agent-tools/skills/` vs `agent-tools/commands/`) and Claude Code discovers them from different user-level paths (`~/.claude/skills/` vs `~/.claude/commands/`), so both symlink lines are required: the skills link does not make commands available, and vice versa. The `mkdir -p` step guarantees both target directories exist on a fresh machine.

`agent-tools` skills and slash commands are only available if the user has run the install step or an equivalent. Guidance below that depends on `agent-tools` (the MASM family, contributor-focused skills, the slash commands in `## Optional Slash Commands`) is conditional on that install.

## Optional Slash Commands

Five cross-cutting slash commands from `0xMiden/agent-tools/commands/` are useful at the parent root. They install via the second symlink line in `## Skill Sources` (`agent-tools/commands/*.md` into `~/.claude/commands/`) and are only available if that step has been run.

| Command | When to invoke |
|---|---|
| `/review-plan <path>` | critical review of a design doc or implementation plan: consistency, feasibility, API quality, completeness, breaking changes, codebase alignment. |
| `/review-security <path>` | web3, WASM, Rust, TS security audit: input validation, key material, transaction safety, WASM boundary, state, RPC, supply chain. |
| `/tech-debt <focus>` | debt analysis with quantified impact and a prioritized remediation roadmap across both submodules. |
| `/deps-audit <focus>` | multi-language dependency scan covering Cargo and npm under one report. |
| `/pr-enhance <pr or req>` | PR description and review-checklist generator for a complex multi-submodule change. |

Skipped from this list (still installable, just not parent-routing relevant):

- `/tdd-cycle` -- single-language TDD orchestrator; better invoked at the submodule level.
- `/debug-trace` -- single-process debug-tooling setup.
- `/standup-notes` -- personal-productivity tool (Obsidian + Jira); no template relevance.

## Research and Q&A Workflows

Per-mode guidance for non-implementation work. These workflows do not exempt build agents from the `## Development Workflow` gates.

- **Q&A.** Load the most-relevant single skill plus `miden-concepts` (from `project-template/.claude/skills/`, the canonical copy) for grounding. Answer from the loaded skill content.
- **Architecture research.** Compose multiple skills across both submodules (for a wallet-integrated dapp, that is `miden-concepts` + `rust-sdk-patterns` + `react-sdk-patterns` + `signer-integration`). Reach for `agent-tools` when the topic is not covered, especially MASM-level topics.
- **Application planning.** Reference the `examples/miden-bank` app inside `0xMiden/tutorials` and the broader tutorials examples as canonical projects builders can study or extend.
- **Debugging existing Miden code.** Load the relevant `*-pitfalls` skill plus the matching `*-patterns` skill (`frontend-pitfalls` + `react-sdk-patterns`; `rust-sdk-pitfalls` + `rust-sdk-patterns`). For MASM-level debugging, fall back to the `agent-tools` MASM family.
- **Factuality is required.** Any answer in Q&A or research mode must be correct and grounded in source. If a question exceeds what the loaded skills cover, the agent must verify against the actual source repositories using `rust-sdk-source-guide` (for contract or Rust topics) or `frontend-source-guide` (for frontend or web SDK topics) -- those skills map the relevant repos (`protocol`, `compiler`, `rust-sdk`, `web-sdk`, `tutorials`). Speculation, "probably", or "should be" answers are not acceptable. Verify in source, or say "not covered, would need to check X".
