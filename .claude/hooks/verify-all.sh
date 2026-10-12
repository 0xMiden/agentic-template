#!/bin/bash
# Stop hook: runs full verification for both templates on task completion.
# Checks which templates are set up (dependencies installed) and verifies each.

FAILED=0

# --- Project Template: contract integration tests ---
PROJECT_DIR="$CLAUDE_PROJECT_DIR/project-template"
if [[ -d "$PROJECT_DIR/contracts" ]]; then
  echo "=== Verifying project-template contracts ==="
  cd "$PROJECT_DIR/integration" || exit 2

  if cargo test -p integration --release --locked 2>&1; then
    echo "project-template: integration tests passed"
  else
    echo "project-template: integration tests FAILED"
    FAILED=1
  fi

  echo "Local-node gate requires separate app-specific assertions and node-log evidence."

  # Advisory: remind about local-node validation
  if [[ -f "$PROJECT_DIR/integration/src/bin/validate_local.rs" ]]; then
    echo "=== Note: local-node validation binary exists ==="
    echo "Ensure 'cargo run --bin validate_local --release' has been run against a local node before proceeding to frontend."
  fi
fi

if [[ ! -d "$CLAUDE_PROJECT_DIR/frontend-template/node_modules" ]]; then
  >&2 echo "frontend-template: dependencies missing; verification incomplete"
fi

if [[ ! -d "$PROJECT_DIR/contracts" ]]; then
  >&2 echo "project-template: submodule missing; verification incomplete"
fi

# --- Frontend Template: tests + typecheck + build ---
FRONTEND_DIR="$CLAUDE_PROJECT_DIR/frontend-template"
if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "=== Verifying frontend-template ==="
  cd "$FRONTEND_DIR" || exit 2

  if npx vitest --run 2>&1; then
    echo "frontend-template: tests passed"
  else
    echo "frontend-template: tests FAILED"
    FAILED=1
  fi

  if npx tsc -b --noEmit 2>&1; then
    echo "frontend-template: type check passed"
  else
    echo "frontend-template: type check FAILED"
    FAILED=1
  fi

  if yarn build 2>&1; then
    echo "frontend-template: build passed"
  else
    echo "frontend-template: build FAILED"
    FAILED=1
  fi
fi

if [[ $FAILED -eq 0 ]]; then
  echo '{"hookSpecificOutput": {"additionalContext": "Available automated checks passed; local-node and browser gates require separate evidence"}}'
  >&2 echo "verify-all.sh: AUTOMATED CHECKS PASS"
  exit 0
else
  echo '{"hookSpecificOutput": {"additionalContext": "Full verification FAILED. Check output above for details."}}'
  >&2 echo "verify-all.sh: FAIL"
  exit 2
fi
