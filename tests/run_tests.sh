#!/usr/bin/env bash
# Regenerates the test pages and captures headless-Firefox screenshots into tmp/.
# Results: read tmp/gt-test.png (PASS/FAIL panel in the top-left corner).
set -e
cd "$(dirname "$0")/.."

python3 tests/inject_tests.py

mkdir -p tmp/ffprof-t1 tmp/ffprof-t2 tmp/ffprof-t3 tmp/ffprof-t4
firefox --no-remote --headless --profile "$PWD/tmp/ffprof-t1" \
  --window-size=1500,2300 --screenshot "$PWD/tmp/gt-test.png" \
  "file://$PWD/tmp/index-test.html" 2>/dev/null
firefox --no-remote --headless --profile "$PWD/tmp/ffprof-t2" \
  --window-size=1500,1200 --screenshot "$PWD/tmp/gt-scenario.png" \
  "file://$PWD/tmp/index-scenario.html" 2>/dev/null
firefox --no-remote --headless --profile "$PWD/tmp/ffprof-t3" \
  --window-size=1500,1200 --screenshot "$PWD/tmp/gt-flash.png" \
  "file://$PWD/tmp/index-flash.html" 2>/dev/null
firefox --no-remote --headless --profile "$PWD/tmp/ffprof-t4" \
  --window-size=1500,1200 --screenshot "$PWD/tmp/gt-default.png" \
  "file://$PWD/index.html" 2>/dev/null
rm -rf tmp/ffprof-t1 tmp/ffprof-t2 tmp/ffprof-t3 tmp/ffprof-t4

ls -la tmp/*.png
