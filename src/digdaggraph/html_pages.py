# src/digdaggraph/html_pages.py
from __future__ import annotations

from pathlib import Path
from html import escape as _escape_html
from typing import Optional, Dict

from .html_theme import _dark_base_css  # shared dark CSS


def write_workflow_html_inline(svg_text: str, html_path: str, project: str, workflow: str) -> None:
    """
    Inline the SVG and add zoom controls + bigger layout with reliable Fit.
    """
    DEFAULT_ZOOM_MIN = 0.25
    DEFAULT_ZOOM_MAX = 3.0
    DEFAULT_ZOOM_STEP = 0.1

    def _workflow_page_css() -> str:
        return _dark_base_css() + """
        /* wider page */
        .wrap{max-width:100%; margin:0 auto; padding:16px 20px}
        .stage{padding:10px}
        .graph-wrap{height:90vh; overflow:auto; border:1px solid var(--border);
                     border-radius:12px; background:#0f1117; position:relative}
        .toolbar{display:flex; gap:8px; align-items:center; justify-content:flex-end;
                  padding:6px 0 10px 0; color:var(--muted)}
        .btn{background:#1f2937; border:1px solid #2c3342; color:var(--text);
              padding:6px 10px; border-radius:8px; cursor:pointer; font-size:12px}
        .btn:disabled{opacity:.5; cursor:default}
        #svg-stage{transform-origin:top left; width:max-content}
        #svg-stage svg{display:block}
        """

    def _zoom_controls_script() -> str:
        return f"""
<script>
(function() {{
  const wrap = document.getElementById('graph-wrap');
  const stage = document.getElementById('svg-stage');
  const btnIn = document.getElementById('zoom-in');
  const btnOut = document.getElementById('zoom-out');
  const btnReset = document.getElementById('zoom-reset');
  const btnFit = document.getElementById('zoom-fit');

  let zoom = 1;
  const MIN = {DEFAULT_ZOOM_MIN}, MAX = {DEFAULT_ZOOM_MAX}, STEP = {DEFAULT_ZOOM_STEP};

  function applyZoom() {{
    stage.style.transform = 'scale(' + zoom.toFixed(3) + ')';
    btnOut.disabled = zoom <= MIN + 1e-6;
    btnIn.disabled  = zoom >= MAX - 1e-6;
  }}

  function getSvgSize() {{
    const svg = stage.querySelector('svg');
    if (!svg) return {{w:0, h:0}};
    const vb = svg.getAttribute('viewBox');
    if (vb) {{
      const p = vb.trim().split(/\\s+/).map(Number);
      if (p.length === 4 && p[2] > 0 && p[3] > 0) return {{w:p[2], h:p[3]}};
    }}
    const w = parseFloat(svg.getAttribute('width')) || 0;
    const h = parseFloat(svg.getAttribute('height')) || 0;
    if (w && h) return {{w, h}};
    const r = svg.getBoundingClientRect();
    return {{w: r.width, h: r.height}};
  }}

  function zoomIn()  {{ zoom = Math.min(MAX, zoom + STEP); applyZoom(); }}
  function zoomOut() {{ zoom = Math.max(MIN, zoom - STEP); applyZoom(); }}
  function zoomReset() {{ zoom = 1; applyZoom(); }}

  function zoomFit() {{
    const s = getSvgSize();
    if (!s.w || !s.h) return;
    const availW = wrap.clientWidth - 24;
    const availH = wrap.clientHeight - 24;
    const scaleW = availW / s.w;
    const scaleH = availH / s.h;
    zoom = Math.max(MIN, Math.min(MAX, Math.min(scaleW, scaleH)));
    applyZoom();
  }}

  btnIn.addEventListener('click', zoomIn);
  btnOut.addEventListener('click', zoomOut);
  btnReset.addEventListener('click', zoomReset);
  btnFit.addEventListener('click', zoomFit);

  wrap.addEventListener('wheel', (e) => {{
    if (!(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    const before = zoom;
    zoom = Math.min(MAX, Math.max(MIN, zoom + (e.deltaY < 0 ? STEP : -STEP)));
    if (zoom !== before) applyZoom();
  }}, {{ passive: false }});

  function fitWhenReady(attempts=0) {{
    const s = getSvgSize();
    if ((s.w && s.h) || attempts > 10) {{
      zoomFit();
    }} else {{
      requestAnimationFrame(() => setTimeout(() => fitWhenReady(attempts+1), 16));
    }}
  }}

  applyZoom();
  fitWhenReady();

  let resizeTimer = null;
  window.addEventListener('resize', () => {{
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => zoomFit(), 150);
  }});
}})();
</script>
"""

    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{_escape_html(project)} · {_escape_html(workflow)}</title>
  <style>{_workflow_page_css()}</style>
</head>
<body>

<header>
  <div class="wrap hdr">
    <h1>{_escape_html(project)} <span class="muted">/</span> {_escape_html(workflow.replace('.dig',''))}</h1>
    <div class="muted">Workflow graph</div>
  </div>
</header>

<main class="wrap">
  <div class="toolbar">
    <button class="btn" id="zoom-out">−</button>
    <button class="btn" id="zoom-in">+</button>
    <button class="btn" id="zoom-reset">100%</button>
    <button class="btn" id="zoom-fit">Fit</button>
  </div>
  <div class="card stage">
    <div class="graph-wrap" id="graph-wrap">
      <div id="svg-stage">{svg_text}</div>
    </div>
  </div>
</main>

<a class="btn-back" href="../../scheduled_workflows.html" title="Back to schedules">← Back</a>

{_zoom_controls_script()}

</body>
</html>"""
    Path(html_path).write_text(doc, encoding="utf-8")


def write_sql_page(
    project: str,
    querypath: str,
    sql_text: str,
    back_href: str,
    out_html_abs: Path,
    td_meta: Optional[Dict] = None,
    td_links: Optional[Dict[str, str]] = None,
) -> None:
    """
    Write a Prism-highlighted SQL page, with optional Treasure Data meta & console links.

    Arguments match graph_generate.py's call-site. Older call styles that passed
    positional args will still work because we keep the order stable.
    """
    td_meta = td_meta or {}
    td_links = td_links or {}

    # Build meta block (if any)
    meta_rows = []
    for k in ("database", "engine", "priority", "retry", "timezone", "result_connection"):
        v = td_meta.get(k)
        if v is not None:
            meta_rows.append(f"<div><b>{_escape_html(k)}</b>: {_escape_html(str(v))}</div>")
    meta_html = (
        f"<div class='card' style='padding:12px;margin-bottom:12px'>{''.join(meta_rows)}</div>"
        if meta_rows
        else ""
    )

    # Build console links (if any)
    links_html = ""
    if td_links:
        parts = []
        for label, href in td_links.items():
            parts.append(
                f"<a href='{_escape_html(href)}' target='_blank' rel='noopener'>{_escape_html(label)}</a>"
            )
        links_html = " • ".join(parts)

    links_block = (
        f"<div class='card' style='padding:12px;margin-bottom:12px'>{links_html}</div>"
        if links_html
        else ""
    )

    escaped_sql = _escape_html(sql_text)

    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{_escape_html(project)} · {_escape_html(querypath)}</title>
  <link rel="stylesheet" href="https://unpkg.com/prismjs/themes/prism-tomorrow.css">
  <style>{_dark_base_css()}
    pre{{white-space:pre;overflow:auto;max-height:75vh;padding:12px;border-radius:12px;
        border:1px solid var(--border);background:#0f1117}}
    .meta{{color:var(--muted);font-size:12px;margin-top:8px}}
  </style>
</head>
<body>

<header>
  <div class="wrap">
    <h1>{_escape_html(project)} <span class="muted">/</span> {_escape_html(querypath)}</h1>
    <div class="muted">SQL source</div>
  </div>
</header>

<main class="wrap">
  {links_block}
  {meta_html}
  <div class="card" style="padding:16px 18px">
    <pre><code class="language-sql">{escaped_sql}</code></pre>
    <div class="meta">Generated by digdag-pages</div>
  </div>
</main>

<a class="btn-back" href="{_escape_html(back_href)}" title="Back to workflow">← Back</a>

<script src="https://unpkg.com/prismjs/components/prism-core.min.js"></script>
<script src="https://unpkg.com/prismjs/components/prism-clike.min.js"></script>
<script src="https://unpkg.com/prismjs/components/prism-sql.min.js"></script>
</body>
</html>"""
    out_html_abs.write_text(doc, encoding="utf-8")
