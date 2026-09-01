#!/usr/bin/env bash
# Renders a markdown file to PDF (defaults: design.md -> design.pdf).
# Usage: bash design/render_pdf.sh [input.md] [output.pdf]
# Needs: pandoc, Google Chrome, network for the mermaid.js CDN.
set -euo pipefail
cd "$(dirname "$0")"
SRC="${1:-design.md}"
OUT="${2:-design.pdf}"
BUILD=build
mkdir -p "$BUILD"

# -tex_math_dollars: price text like "($1 / $5 per MTok)" must never parse
# as TeX math (it silently mangles the whole span).
pandoc "$SRC" -f gfm-tex_math_dollars -t html --syntax-highlighting=none -o "$BUILD/body.html"

# Pandoc wraps mermaid fences as <pre class="mermaid"><code>...</code></pre>
# with entities escaped; mermaid.js wants a bare <pre class="mermaid"> with
# raw text. Unwrap and decode (amp last).
perl -0777 -pe '
  s{<pre class="mermaid"><code[^>]*>(.*?)</code></pre>}{
    my $t = $1;
    $t =~ s/&lt;/</g; $t =~ s/&gt;/>/g; $t =~ s/&quot;/"/g;
    $t =~ s/&#39;/\x27/g; $t =~ s/&amp;/&/g;
    "<pre class=\"mermaid\">$t</pre>"
  }gse' "$BUILD/body.html" > "$BUILD/body2.html"

cat > "$BUILD/design.html" <<'HEAD'
<!doctype html>
<html><head><meta charset="utf-8"><title>Emergent Scope Sentinel</title>
<style>
  @page { size: A4; margin: 17mm 16mm; }
  body { font: 10.5pt/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif;
         color: #111; margin: 0; }
  h1 { font-size: 1.55em; margin: 0 0 .2em; }
  h2 { font-size: 1.22em; margin: 1.2em 0 .4em; break-after: avoid; }
  h3 { font-size: 1.03em; margin: 1em 0 .3em; break-after: avoid; }
  p, li { orphans: 3; widows: 3; }
  ul, ol { margin: .3em 0 .6em; padding-left: 1.4em; }
  li { margin: .15em 0; }
  code { font: 8.8pt ui-monospace, Menlo, monospace; }
  pre { font: 8.8pt ui-monospace, Menlo, monospace; background: #f6f6f6;
        padding: 6px 8px; white-space: pre-wrap; break-inside: avoid; }
  table { border-collapse: collapse; width: 100%; font-size: 9.3pt;
          break-inside: avoid; }
  th, td { border: .5pt solid #999; padding: 3px 6px; text-align: left;
           vertical-align: top; }
  th { background: #efefef; }
  blockquote { margin: .5em 0; padding-left: .8em; border-left: 2px solid #bbb; }
  hr { border: 0; border-top: .5pt solid #bbb; margin: 1em 0; }
  .mermaid { text-align: center; break-inside: avoid; background: none;
             padding: 2px 0; }
  .mermaid svg { max-width: 100%; height: auto; }
  h2[id^="appendix-a"] { break-before: page; }
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({ startOnLoad: true, theme: "neutral",
    themeVariables: { fontSize: "18px" },
    flowchart: { useMaxWidth: true },
    sequence: { useMaxWidth: true, actorFontSize: 20, messageFontSize: 18,
                noteFontSize: 16 } });
</script>
</head><body>
HEAD
cat "$BUILD/body2.html" >> "$BUILD/design.html"
printf '</body></html>\n' >> "$BUILD/design.html"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --disable-gpu --hide-scrollbars \
  --virtual-time-budget=25000 --no-pdf-header-footer \
  --print-to-pdf="$PWD/$OUT" "file://$PWD/$BUILD/design.html" 2>/dev/null

mdls -name kMDItemNumberOfPages "$OUT" 2>/dev/null || true
ls -la "$OUT"
