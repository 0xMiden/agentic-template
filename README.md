# Miden Agentic Template

A full-stack Miden development workspace AND an expert Miden companion in one repo. Build Miden dApps end-to-end (Rust smart contracts + React frontend), or use the same setup as a Miden wizard for architecture, debugging, MASM, and design decisions — anything you're working on in the Miden ecosystem.

## Two ways to use this repo

**Build Miden dApps.** Scaffold for the full pipeline: write contracts in `project-template/`, validate them with MockChain tests, gate on local-node validation against a real Miden node, then build a React frontend in `frontend-template/` that talks to them. Hooks verify your work on every edit.

**Your Miden wizard.** A senior-level Miden expert wired into your terminal. Architecture decisions, design reviews, debugging existing contracts or frontends, MASM-level questions, planning a new app, picking the right SDK pattern — anything Miden-related, ask here. Backed by the full `0xMiden/agent-tools` skill surface plus the app-developer skills in both submodules, with a hard "verify in source or say so" factuality rule. It's a co-thinker, not an FAQ.

Both modes share the same skills, slash commands, and verification hooks. Pick the mode that fits the task, or move between them in the same session.

## Getting Started

### Prerequisites

- [Rust](https://rustup.rs/) (stable toolchain)
- [midenup](https://github.com/0xMiden/midenup) toolchain (provides `cargo-miden`)
- [Node.js](https://nodejs.org/) (v18+)
- [Yarn](https://yarnpkg.com/) (v1)

### Clone

```bash
git clone --recurse-submodules https://github.com/0xMiden/agentic-template.git
cd agentic-template
```

If you already cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

### Install Dependencies

```bash
# Checks prerequisites, installs the Miden toolchain, runs yarn install, and pre-builds contracts
bash setup.sh
```

`setup.sh` auto-installs Rust, midenup, and Yarn v1 (via npm, when Node and npm are available) if missing; Yarn v2+ is rejected. Node.js v18+ must be installed manually if missing.

## Structure

```
agentic-template/
  project-template/           # Miden smart contracts (Rust SDK)
    contracts/                 # Account components, note scripts, tx scripts
    integration/               # MockChain tests + local-node validation binaries
  frontend-template/           # Miden web frontend (React + TypeScript)
    src/                       # React components, hooks, tests
    public/packages/           # Compiled contract artifacts (.masp files)
```

## Build mode: contracts → validation → frontend

Contracts first, validate against a real local node, then frontend. Frontend work is gated on local-node validation passing.

1. **Build contracts** in `project-template/contracts/` (compile to `.masp` packages).
2. **MockChain tests** in `project-template/integration/tests/` — validate state transitions, note lifecycle, output notes.
3. **Local-node validation** (gate): run a Rust client binary in `project-template/integration/src/bin/` against a local Miden node. Both must be clean before frontend work begins.
4. **Copy artifacts** — drop `.masp` files into `frontend-template/public/packages/`.
5. **Build the frontend** in `frontend-template/src/`. Mirror the validated Rust binary flow; TDD recommended.

Quick reference:

```bash
# Build a single contract
cargo miden build --manifest-path project-template/contracts/<name>/Cargo.toml --release

# Run all MockChain integration tests
cd project-template && cargo test -p integration --release

# Start a local Miden node
cd project-template && miden-node bundled start --data-directory local-node-data --rpc.url http://0.0.0.0:57291

# Run local-node validation
cd project-template && cargo run --bin validate_local --release

# Start the frontend
cd frontend-template && yarn dev
```

See `CLAUDE.md` at the root for full exit criteria and the per-step skill map.

## Wizard mode: ask anything Miden

No build pipeline required. Open Claude Code (or Codex) at the repository root and ask. The same skills the build mode uses are available here, just composed differently:

- **Concepts & basics** — actor model, accounts/notes/transactions, P2ID/P2IDE/SWAP, Felt/Word semantics → `miden-concepts`
- **Writing or reviewing contracts** → `rust-sdk-patterns`, `rust-sdk-pitfalls`, `rust-sdk-testing-patterns`
- **Writing or reviewing a frontend** → `react-sdk-patterns`, `frontend-pitfalls`, `web-client-usage`, `signer-integration`, `vite-wasm-setup`
- **MASM authoring or debugging** → the MASM family in `0xMiden/agent-tools` (`masm-formatting`, `masm-doc-comments`, `masm-padding`, …)
- **Architecture / planning** — compose multiple skills; reference the `examples/miden-bank` app in `0xMiden/tutorials`
- **Going deeper than the skills cover** → `rust-sdk-source-guide` or `frontend-source-guide` to verify against the actual `miden-base`, `miden-client`, `compiler`, and `tutorials` source

Hard rule, encoded in `CLAUDE.md`: any answer must be grounded in skill content or verified in source. "Probably" and "should be" are not acceptable.

See `## Research and Q&A Workflows` in `CLAUDE.md` for the per-mode workflow detail.

## AI Tooling

The AI experience is the core of this template. Skills, hooks, and slash commands are wired in at the repo root, so a single session at this directory gets all of it.

### Skills (three sources)

| Source | Skills | Notes |
|---|---|---|
| `project-template/.claude/skills/` | 7 — `miden-concepts`, `rust-sdk-patterns`, `rust-sdk-pitfalls`, `rust-sdk-testing-patterns`, `rust-sdk-source-guide`, `local-node-validation`, `miden-client-cli` | App-developer skills, tailored for this template. |
| `frontend-template/.claude/skills/` | 8 — `miden-concepts`, `react-sdk-patterns`, `signer-integration`, `web-client-usage`, `vite-wasm-setup`, `frontend-pitfalls`, `testing-patterns`, `frontend-source-guide` | App-developer skills for the React / web SDK side. |
| [`0xMiden/agent-tools`](https://github.com/0xMiden/agent-tools) | 22 upstream (13 mirrored above + 9 upstream-only: MASM family ×6, contributor-focused ×3) | Fallback when a topic is not covered downstream; canonical for MASM and `miden-client` internals. |

**Precedence:** when the same skill exists in a submodule and in `agent-tools`, prefer the submodule version (it carries app-developer context). Fall back to `agent-tools` for what is not covered downstream.

**Install `agent-tools` once at the user level** so Claude Code auto-discovers both skills and slash commands across all projects:

```bash
git clone https://github.com/0xMiden/agent-tools.git ~/agent-tools

# Ensure user-level Claude Code surfaces exist
mkdir -p ~/.claude/skills ~/.claude/commands

# Skills
ln -sf ~/agent-tools/skills/* ~/.claude/skills/

# Slash commands
ln -sf ~/agent-tools/commands/*.md ~/.claude/commands/
```

### Slash Commands

Five cross-cutting commands from `agent-tools/commands/` are useful at the parent root (require the `agent-tools` install above):

| Command | When to invoke |
|---|---|
| `/review-plan <path>` | Critical review of a design doc or implementation plan. |
| `/review-security <path>` | Web3 / WASM / Rust / TS security audit. |
| `/tech-debt <focus>` | Quantified debt analysis with a prioritized remediation roadmap. |
| `/deps-audit <focus>` | Cargo + npm dependency scan in one report. |
| `/pr-enhance <pr or req>` | PR description + review checklist for a multi-submodule change. |

### Hooks

| Trigger | Action |
|---|---|
| Edit contract file | Auto-build the modified contract (`cargo miden build`) |
| Edit frontend file | Type check + run affected tests |
| Task completion | Full verification: contract tests + frontend tests + typecheck + build |

## Updating Submodules

To pull the latest changes from both templates:

```bash
git submodule update --remote --merge
git add project-template frontend-template
git commit -m "Update submodules to latest"
```
