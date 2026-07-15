#!/usr/bin/env bash
# deploy-site.sh — deploya la landing su wadachi.eliacinti.dev.
# La pill "PyPI · vX.Y.Z" viene allineata AUTOMATICAMENTE alla versione del
# package (wadachi/__init__.py): mai più pill stantie.
#
# Uso:  scripts/deploy-site.sh [--bump]
#   --bump  incrementa il cache-buster ?v=N (solo se hai toccato css/js)

set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEMO="$REPO/demo"
DEST="elia@178.104.95.126:/home/elia/engram/"
KEY="$HOME/.ssh/feynotes_deploy"

VERSION=$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$REPO/wadachi/__init__.py")
[ -n "$VERSION" ] || { echo "versione non trovata"; exit 1; }

# pill di versione allineata al package (edit in-place senza rename: sicura ovunque)
python3 - "$DEMO/index.html" "$VERSION" <<'EOF'
import re, sys
path, version = sys.argv[1], sys.argv[2]
t = open(path).read()
t2 = re.sub(r"PyPI · v[\d.]+", f"PyPI · v{version}", t)
open(path, "w").write(t2)
print(f"  pill → PyPI · v{version}" + ("" if t != t2 else " (già allineata)"))
EOF

if [ "${1:-}" = "--bump" ]; then
  python3 - "$DEMO/index.html" <<'EOF'
import re, sys
path = sys.argv[1]
t = open(path).read()
cur = int(re.search(r"styles\.css\?v=(\d+)", t).group(1))
t = t.replace(f"styles.css?v={cur}", f"styles.css?v={cur+1}")
t = t.replace(f"app.js?v={cur}", f"app.js?v={cur+1}")
open(path, "w").write(t)
print(f"  cache-buster → v={cur+1}")
EOF
fi

rsync -az -e "ssh -i $KEY" "$DEMO/index.html" "$DEMO/docs.html" "$DEMO/styles.css" "$DEMO/app.js" \
  "$DEMO/og.png" "$DEMO/fonts" "$DEST"
echo "  deploy ok → https://wadachi.eliacinti.dev"
curl -s -o /dev/null -w "  verifica: HTTP %{http_code}\n" --max-time 20 "https://wadachi.eliacinti.dev/"
