# Miden Agentic Template

A full-stack Miden development workspace combining smart contract development (Rust SDK) with a web frontend (React + @miden-sdk/react). Both templates are included as git submodules.

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
    integration/               # Integration tests and deployment scripts
  frontend-template/           # Miden web frontend (React + TypeScript)
    src/                       # React components, hooks, tests
    public/packages/           # Compiled contract artifacts (.masp files)
```

## Development Workflow

1. **Build contracts** in `project-template/contracts/`
2. **Test contracts** with `cd project-template && cargo test -p integration --release`
3. **Copy artifacts** from contract build output to `frontend-template/public/packages/`
4. **Build frontend** in `frontend-template/src/`
5. **Run frontend** with `cd frontend-template && yarn dev`

## AI Developer Experience

This template is designed for AI-assisted development. Open Claude Code (or Codex, Cursor) at the repository root and describe what you want to build.

- `CLAUDE.md` at root provides the monorepo overview and workflow
- Each sub-template has its own `CLAUDE.md` with detailed instructions
- Skills load automatically when working in either template
- Hooks verify contract builds and frontend type safety on every edit

### Skills

| Template | Skills |
|----------|--------|
| project-template | miden-concepts, rust-sdk-patterns, rust-sdk-pitfalls, rust-sdk-testing-patterns, rust-sdk-source-guide |
| frontend-template | miden-concepts, react-sdk-patterns, testing-patterns, frontend-pitfalls, vite-wasm-setup, signer-integration, frontend-source-guide |

### Hooks

| Trigger | Action |
|---------|--------|
| Edit contract file | Auto-build the modified contract |
| Edit frontend file | Type check + run affected tests |
| Task completion | Full verification (all tests + typecheck + build) |

## Updating Submodules

To pull the latest changes from both templates:

```bash
git submodule update --remote --merge
git add project-template frontend-template
git commit -m "Update submodules to latest"
```
