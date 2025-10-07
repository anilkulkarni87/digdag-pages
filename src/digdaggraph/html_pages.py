
from pathlib import Path
from html import escape
from .html_theme import dark_base_css, workflow_page_css
from .constants import DEFAULT_ZOOM_MIN, DEFAULT_ZOOM_MAX, DEFAULT_ZOOM_STEP, SCHEDULE_INDEX_FILE

def _esc(s: str) -> str:
    return escape(s, quote=False)

def _esca(s: str) -> str:
    return escape(s, quote=True)

def zoom_controls_script() -> str:
    return (
        "<script>(function(){"
        "const wrap=document.getElementById('graph-wrap');"
        "const stage=document.getElementById('svg-stage');"
        "const btnIn=document.getElementById('zoom-in');"
        "const btnOut=document.getElementById('zoom-out');"
        "const btnReset=document.getElementById('zoom-reset');"
        "const btnFit=document.getElementById('zoom-fit');"
        f"let zoom=1;const MIN={DEFAULT_ZOOM_MIN},MAX={DEFAULT_ZOOM_MAX},STEP={DEFAULT_ZOOM_STEP};"
        "function applyZoom(){stage.style.transform='scale('+zoom.toFixed(3)+')';"
        "btnOut.disabled=zoom<=MIN+1e-6;btnIn.disabled=zoom>=MAX-1e-6;}"
        "function getSvgSize(){const svg=stage.querySelector('svg');if(!svg)return{w:0,h:0};"
        "const vb=svg.getAttribute('viewBox');if(vb){const p=vb.trim().split(/\s+/).map(Number);"
        "if(p.length===4&&p[2]>0&&p[3]>0)return{w:p[2],h:p[3]};}"
        "const w=parseFloat(svg.getAttribute('width'))||0;"
        "const h=parseFloat(svg.getAttribute('height'))||0;"
        "if(w&&h)return{w,h};const r=svg.getBoundingClientRect();return{w:r.width,h:r.height};}"
        "function zoomIn(){zoom=Math.min(MAX,zoom+STEP);applyZoom();}"
        "function zoomOut(){zoom=Math.max(MIN,zoom-STEP);applyZoom();}"
        "function zoomReset(){zoom=1;applyZoom();}"
        "function zoomFit(){const s=getSvgSize();if(!s.w||!s.h)return;"
        "const availW=wrap.clientWidth-24;const availH=wrap.clientHeight-24;"
        "const scaleW=availW/s.w;const scaleH=availH/s.h;"
        "zoom=Math.max(MIN,Math.min(MAX,Math.min(scaleW,scaleH)));applyZoom();}"
        "btnIn.addEventListener('click',zoomIn);btnOut.addEventListener('click',zoomOut);"
        "btnReset.addEventListener('click',zoomReset);btnFit.addEventListener('click',zoomFit);"
        "wrap.addEventListener('wheel',e=>{if(!(e.ctrlKey||e.metaKey))return;e.preventDefault();"
        "const before=zoom;zoom=Math.min(MAX,Math.max(MIN,zoom+(e.deltaY<0?STEP:-STEP)));"
        "if(zoom!==before)applyZoom();},{passive:false});"
        "function fitWhenReady(a=0){const s=getSvgSize();if((s.w&&s.h)||a>10){zoomFit();}"
        "else{requestAnimationFrame(()=>setTimeout(()=>fitWhenReady(a+1),16));}}"
        "applyZoom();fitWhenReady();"
        "let t=null;window.addEventListener('resize',()=>{clearTimeout(t);t=setTimeout(()=>zoomFit(),150);});"
        "})();</script>"
    )

def write_workflow_html_inline(svg_text: str, html_path: str, project: str, workflow: str) -> None:
    head = (
        "<!doctype html><html lang='en'><head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{_esc(project)} / {_esc(workflow)}</title>"
        f"<style>{workflow_page_css()}</style>"
        "</head><body>"
    )
    body = (
        "<header><div class='wrap hdr'>"
        f"<h1>{_esc(project)} <span class='muted'>/</span> {_esc(workflow.replace('.dig',''))}</h1>"
        "<div class='muted'>Workflow graph</div>"
        "</div></header>"
        "<main class='wrap'>"
        "<div class='toolbar'>"
        "<button class='btn' id='zoom-out'>−</button>"
        "<button class='btn' id='zoom-in'>+</button>"
        "<button class='btn' id='zoom-reset'>100%</button>"
        "<button class='btn' id='zoom-fit'>Fit</button>"
        "</div>"
        "<div class='card stage'>"
        "<div class='graph-wrap' id='graph-wrap'>"
        f"<div id='svg-stage'>{svg_text}</div>"
        "</div></div></main>"
        f"<a class='btn-back' href='../../{SCHEDULE_INDEX_FILE}' title='Back to schedules'>← Back</a>"
        f"{zoom_controls_script()}"
        "</body></html>"
    )
    Path(html_path).write_text(head + body, encoding="utf-8")

def write_sql_page(project: str, querypath: str, src_sql: str, back_href_rel: str, out_html_abs: Path) -> None:
    escaped_sql = _esc(src_sql)
    doc = (
        "<!doctype html><html lang='en'><head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{_esc(project)} / {_esc(Path(querypath).name)}</title>"
        "<link rel='stylesheet' href='https://unpkg.com/prismjs/themes/prism-tomorrow.css'>"
        f"<style>{dark_base_css()}"
        "pre{white-space:pre;overflow:auto;max-height:75vh;padding:12px;border-radius:12px;"
        "border:1px solid var(--border);background:#0f1117}"
        ".meta{color:var(--muted);font-size:12px;margin-top:8px}"
        "</style></head><body>"
        "<header><div class='wrap'>"
        f"<h1>{_esc(project)} <span class='muted'>/</span> {_esc(querypath)}</h1>"
        "<div class='muted'>SQL source</div>"
        "</div></header>"
        "<main class='wrap'><div class='card' style='padding:16px 18px'>"
        f"<pre><code class='language-sql'>{escaped_sql}</code></pre>"
        "<div class='meta'>Generated by digdaggraph</div>"
        "</div></main>"
        f"<a class='btn-back' href='{_esca(back_href_rel)}' title='Back to workflow'>← Back</a>"
        "<script src='https://unpkg.com/prismjs/components/prism-core.min.js'></script>"
        "<script src='https://unpkg.com/prismjs/components/prism-clike.min.js'></script>"
        "<script src='https://unpkg.com/prismjs/components/prism-sql.min.js'></script>"
        "</body></html>"
    )
    out_html_abs.write_text(doc, encoding="utf-8")
