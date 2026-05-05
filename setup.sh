#!/usr/bin/env bash
#
# setup.sh -- one-command prerequisite installer for the agentic-template.
#
# Detects Rust, midenup, Node.js, and Yarn. Installs Rust (rustup) and
# midenup if missing. Detect-only for Node and Yarn major version (does
# not auto-install Node, refuses Yarn v2+). Runs `yarn install` in
# frontend-template and pre-builds every contract under
# project-template/contracts/.
#
# Safe to re-run. Does not modify shell rc files and never escalates privileges.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

REQUIRED_NODE_MAJOR=18
MIDENUP_GIT_URL="https://github.com/0xMiden/midenup"

info()   { printf "%s\n" "$*"; }
header() { printf "\n[%s/6] %s\n" "$1" "$2"; }
fail()   { printf "setup.sh: %s\n" "$*" >&2; exit 1; }
have()   { command -v "$1" >/dev/null 2>&1; }

# Source ~/.cargo/env so freshly-installed tools land on PATH for this run.
source_cargo_env() {
  if [ -f "$HOME/.cargo/env" ]; then
    # shellcheck source=/dev/null
    . "$HOME/.cargo/env"
  fi
}

check_or_install_rust() {
  if have cargo && have rustc; then
    info "Rust found: $(rustc --version)"
    return 0
  fi
  info "Rust not found. Installing via rustup (non-interactive, --no-modify-path)."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --default-toolchain stable --no-modify-path \
    || fail "step 1/6: rustup installer failed"
  source_cargo_env
  have cargo || fail "step 1/6: cargo not on PATH after rustup install (expected ~/.cargo/bin)"
  info "Rust installed: $(rustc --version)"
}

check_or_install_midenup() {
  # Step 2a: ensure midenup binary exists. midenup is published on crates.io
  # as 0.2.0, but the latest channel manifest support and recent fixes only
  # land on origin/main; per the midenup README, install from --git until a
  # newer release ships.
  if ! have midenup; then
    info "midenup not found. Installing via 'cargo install --git $MIDENUP_GIT_URL midenup'."
    cargo install --git "$MIDENUP_GIT_URL" midenup \
      || fail "step 2/6: cargo install --git $MIDENUP_GIT_URL midenup failed"
    source_cargo_env
    have midenup || fail "step 2/6: midenup not on PATH after install"
    info "midenup installed at $(command -v midenup)"
  else
    info "midenup found at $(command -v midenup)"
  fi

  # Step 2b: ensure 'midenup init' has produced the 'miden' symlink in
  # $CARGO_HOME/bin. Safe to rerun: midenup init is idempotent.
  if ! have miden; then
    info "miden symlink not on PATH; running 'midenup init'."
    midenup init || fail "step 2/6: midenup init failed"
    source_cargo_env
    have miden || fail "step 2/6: miden still not on PATH after midenup init (ensure ~/.cargo/bin is in PATH)"
  fi

  # Step 2c: ensure a toolchain is installed. 'midenup show active-toolchain'
  # prints the active channel name to stdout when a toolchain is available;
  # install stable only when no name is shown. Capture stdout so a non-zero
  # exit (e.g. transient symlink warning) does not abort detection.
  local active
  active="$(midenup show active-toolchain 2>/dev/null | head -n1 || true)"
  if [ -n "$active" ]; then
    info "midenup toolchain already active: $active"
  else
    info "No midenup toolchain active; installing stable."
    midenup install stable || fail "step 2/6: midenup install stable failed"
  fi
}

check_node() {
  if ! have node; then
    fail "step 3/6: Node.js not found. Install Node v$REQUIRED_NODE_MAJOR+ from https://nodejs.org/ or via your preferred version manager (nvm, fnm, asdf), then re-run setup.sh."
  fi
  local version major
  version="$(node --version)"
  major="${version#v}"
  major="${major%%.*}"
  if [ "$major" -lt "$REQUIRED_NODE_MAJOR" ]; then
    fail "step 3/6: Node.js $version is too old. Install Node v$REQUIRED_NODE_MAJOR+ from https://nodejs.org/, then re-run setup.sh."
  fi
  info "Node.js found: $version"
}

check_or_install_yarn() {
  if have yarn; then
    local version major
    version="$(yarn --version)"
    major="${version%%.*}"
    if [ "$major" != "1" ]; then
      fail "step 4/6: agentic-template requires Yarn v1; you have $version. See https://classic.yarnpkg.com/ for v1 install instructions."
    fi
    info "Yarn found: $version"
    return 0
  fi
  if ! have npm; then
    fail "step 4/6: npm is required to install Yarn but was not found. Re-install Node.js v$REQUIRED_NODE_MAJOR+ to provide it."
  fi
  info "Yarn not found. Installing Yarn v1 via 'npm install -g yarn'."
  npm install -g yarn || fail "step 4/6: npm install -g yarn failed"
  info "Yarn installed: $(yarn --version)"
}

install_frontend_deps() {
  local fe_dir="$SCRIPT_DIR/frontend-template"
  if [ ! -d "$fe_dir" ]; then
    fail "step 5/6: $fe_dir not found. Did you clone with --recurse-submodules?"
  fi
  ( cd "$fe_dir" && yarn install ) \
    || fail "step 5/6: yarn install failed in frontend-template"
}

build_contracts() {
  local contracts_dir="$SCRIPT_DIR/project-template/contracts"
  if [ ! -d "$contracts_dir" ]; then
    fail "step 6/6: $contracts_dir not found. Did you clone with --recurse-submodules?"
  fi
  if ! have miden; then
    fail "step 6/6: miden command not found on PATH. Run 'midenup init' to create the symlink, and ensure ~/.cargo/bin is on PATH."
  fi
  # Build from inside each contract directory so rustup picks up the
  # project-template/rust-toolchain.toml pin (cargo searches upward from cwd,
  # not from --manifest-path).
  local pkg_dir pkg built=0
  for pkg_dir in "$contracts_dir"/*/; do
    [ -f "${pkg_dir}Cargo.toml" ] || continue
    pkg="$(basename "$pkg_dir")"
    info "Building contract: $pkg"
    ( cd "$pkg_dir" && miden build --release ) \
      || fail "step 6/6: miden build failed for $pkg"
    built=$((built + 1))
  done
  if [ "$built" -eq 0 ]; then
    fail "step 6/6: no contracts found under $contracts_dir"
  fi
  info "Built $built contract(s)."
}

print_path_advice_if_needed() {
  case ":$PATH:" in
    *":$HOME/.cargo/bin:"*) return 0 ;;
  esac
  printf "\nNote: ~/.cargo/bin is not in your PATH. Add this line to your shell rc to make miden available in new shells:\n  export PATH=\"\$HOME/.cargo/bin:\$PATH\"\n"
}

main() {
  header 1 "Checking Rust toolchain"
  check_or_install_rust
  header 2 "Checking midenup"
  check_or_install_midenup
  header 3 "Checking Node.js"
  check_node
  header 4 "Checking Yarn"
  check_or_install_yarn
  header 5 "Installing frontend dependencies"
  install_frontend_deps
  header 6 "Building contracts"
  build_contracts
  print_path_advice_if_needed
  printf "\nsetup.sh: complete\n"
}

main "$@"
