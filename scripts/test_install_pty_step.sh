#!/usr/bin/env bash
# Known-positive for the rewritten PTY step in install_all.sh.
#
# The point of the rewrite is that a failing patch must be LOUD and must fail the
# install. Reading the case statement is not evidence of that. This extracts the real
# block from install_all.sh, stubs the interpreter to return each exit code in turn,
# and asserts what the operator actually sees and what `failed` ends up as.

set -u
SRC="$(cd "$(dirname "$0")/.." && pwd)/install_all.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# extract the block: from 'pty_script=' through the closing 'esac'
awk '/^  pty_script=/{f=1} f{print} f&&/^  esac$/{exit}' "$SRC" > "$WORK/block.sh"
if [ ! -s "$WORK/block.sh" ]; then echo "FAIL: could not extract block"; exit 1; fi
echo "extracted $(wc -l < "$WORK/block.sh") lines"

run_case() {
  local rc="$1" expect_failed="$2" expect_text="$3"
  mkdir -p "$WORK/opt/venv-a0/bin"
  cat > "$WORK/opt/venv-a0/bin/python3" <<EOF
#!/usr/bin/env bash
echo "  a0 ver   : v2.9"
case $rc in
  0) echo "  already patched - no-op" ;;
  2) echo "  MISSING target: /nope.py" ;;
  3) echo "  ABORT: anchor not found" ; echo "boom" >&2 ;;
  4) echo "  ABORT: patched source does not compile" ;;
  9) echo "Traceback (most recent call last):" >&2 ; echo "RuntimeError: kaboom" >&2 ;;
esac
exit $rc
EOF
  chmod +x "$WORK/opt/venv-a0/bin/python3"

  out="$(
    cd "$WORK" || exit 1
    failed=0
    SCRIPT_DIR="$WORK"
    log_warn() { echo "    WARN $1"; }
    log_err()  { echo "    ERR  $1"; }
    # shellcheck disable=SC1090
    PATH="$WORK/opt/venv-a0/bin:$PATH"
    # the block calls /opt/venv-a0/bin/python3 by absolute path, so shim it
    mkdir -p /tmp/ptytest && :
    sed "s|/opt/venv-a0/bin/python3|$WORK/opt/venv-a0/bin/python3|" "$WORK/block.sh" > "$WORK/block_run.sh"
    . "$WORK/block_run.sh"
    echo "FAILED_COUNT=$failed"
  )"

  got_failed="$(echo "$out" | sed -n 's/^FAILED_COUNT=//p')"
  local ok=1
  [ "$got_failed" = "$expect_failed" ] || ok=0
  echo "$out" | grep -q "$expect_text" || ok=0
  if [ "$ok" = "1" ]; then
    echo "  PASS rc=$rc -> failed=$got_failed, operator sees '$expect_text'"
  else
    echo "  FAIL rc=$rc -> failed=$got_failed (expected $expect_failed), looking for '$expect_text'"
    echo "$out" | sed 's/^/       /'
  fi
}

echo "=== install_all.sh PTY step behaviour ==="
run_case 0 0 "already patched"
run_case 2 0 "target missing"
run_case 3 1 "ANCHORS MISSING"
run_case 4 1 "failed to compile"
run_case 9 1 "unexpected exit 9"
