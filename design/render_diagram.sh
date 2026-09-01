#!/usr/bin/env bash
# Renders the main architecture diagram (first mermaid block of design.md)
# to architecture.png. Reproducible: bash design/render_diagram.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build
awk '/^```mermaid$/{f=1;n++;next} /^```$/{f=0} f&&n==1' design.md > build/arch.mmd
cat > build/arch.html <<'HEAD'
<!doctype html>
<html><head><meta charset="utf-8">
<style>body{margin:0;padding:24px;background:#fff}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:"neutral",
  themeVariables:{fontSize:"18px"}, flowchart:{useMaxWidth:false}});</script>
</head><body><pre class="mermaid">
HEAD
cat build/arch.mmd >> build/arch.html
printf '</pre></body></html>\n' >> build/arch.html
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --virtual-time-budget=15000 --window-size=3500,760 \
  --screenshot="$PWD/architecture.png" "file://$PWD/build/arch.html" 2>/dev/null
ls -la architecture.png
