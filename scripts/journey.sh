#!/usr/bin/env bash
# Explicit stages; never submit network transactions or start services implicitly.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail() { printf '%s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null || fail "Missing $1; see docs/agent-first-v017.md"; }
case "${1:-doctor}" in
  doctor)
    need git
    for item in 'project-template e941949b1cb244f1557ace1c58dca0dc7a898da8' 'frontend-template 71fb5bb0a205224d04a7d0264fad2cecc8d4478d'; do
      read -r dir expected <<< "$item"
      [ "$(git -C "$dir" rev-parse HEAD)" = "$expected" ] || fail "$dir pin differs; inspect before updating submodules"
    done
    need cargo; need midenup; need miden; need node; need yarn
    [[ "$(yarn --version)" == 1.* ]] || fail 'Use Yarn Classic 1'
    node -e 'if (+process.versions.node.split(".")[0] < 18) process.exit(1)'
    (cd project-template && midenup show active-toolchain)
    printf '%s\n' 'Source pins/prerequisites checked. Builds, local node and browser are separate gates.'
    ;;
  contracts)
    need cargo; need miden
    # Test helpers use ../contracts relative to the integration directory.
    (cd project-template/integration && cargo test -p integration --release --locked)
    ;;
  frontend)
    need yarn
    [ -d frontend-template/node_modules ] || fail 'Install locked dependencies first'
    (cd frontend-template && yarn test && yarn build)
    ;;
  artifacts)
    for name in counter-account increment-note; do
      source_path="project-template/contracts/$name/target/miden/release/out.masp"
      [ -s "$source_path" ] || fail "Missing $source_path; run contracts first"
    done
    for name in counter-account increment-note; do
      cp "project-template/contracts/$name/target/miden/release/out.masp" "frontend-template/public/packages/$name.masp"
    done
    printf '%s\n' 'Packages copied. Review submodule changes; configure your deployed counter ID.'
    ;;
  local)
    [ "${MIDEN_ALLOW_LOCAL:-}" = 1 ] || fail 'Explicitly set MIDEN_ALLOW_LOCAL=1; starts disposable Docker node and local client state'
    python3 scripts/local_node.py
    ;;
  testnet)
    [ "${MIDEN_ALLOW_TESTNET:-}" = 1 ] || fail 'Explicitly set MIDEN_ALLOW_TESTNET=1; this creates accounts, keys, store and submits testnet transactions'
    (cd project-template/integration && cargo run --bin increment_count --release --locked)
    ;;
  *) fail 'Usage: bash scripts/journey.sh doctor|contracts|frontend|artifacts|local|testnet' ;;
esac
