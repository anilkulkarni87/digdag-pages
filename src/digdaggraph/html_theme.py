
def dark_base_css() -> str:
    return (
        ":root{--bg:#0b0c10;--panel:#16171d;--text:#e6e6e6;--muted:#9aa0a6;"
        "--accent:#7aa2ff;--border:#24262d;--shadow:0 8px 30px rgba(0,0,0,.35);}"
        "*{box-sizing:border-box}"
        "html,body{margin:0;height:100%;background:var(--bg);color:var(--text);"
        "font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial,sans-serif}"
        "a{color:var(--accent);text-decoration:none}"
        "a:hover{text-decoration:underline}"
        "header{position:sticky;top:0;z-index:2;background:var(--panel);"
        "border-bottom:1px solid var(--border);box-shadow:var(--shadow)}"
        ".wrap{max-width:1100px;margin:0 auto;padding:16px 20px}"
        "h1{font-size:18px;margin:0}"
        ".muted{color:var(--muted)}"
        "main{padding:18px 20px}"
        ".card{background:var(--panel);border:1px solid var(--border);"
        "border-radius:12px;box-shadow:var(--shadow)}"
        ".btn-back{position:fixed;left:16px;bottom:16px;background:#1f2937;border:1px solid #2c3342;"
        "color:var(--text);padding:8px 10px;border-radius:10px}"
    )

def workflow_page_css() -> str:
    return dark_base_css() + (
        ".wrap{max-width:100%;margin:0 auto;padding:16px 20px}"
        ".stage{padding:10px}"
        ".graph-wrap{height:90vh;overflow:auto;border:1px solid var(--border);"
        "border-radius:12px;background:#0f1117;position:relative}"
        ".toolbar{display:flex;gap:8px;align-items:center;justify-content:flex-end;"
        "padding:6px 0 10px 0;color:var(--muted)}"
        ".btn{background:#1f2937;border:1px solid #2c3342;color:var(--text);"
        "padding:6px 10px;border-radius:8px;cursor:pointer;font-size:12px}"
        ".btn:disabled{opacity:.5;cursor:default}"
        "#svg-stage{transform-origin:top left;width:max-content}"
        "#svg-stage svg{display:block}"
    )
