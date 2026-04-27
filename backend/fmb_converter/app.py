"""
app.py - FMB PDF to DXF Web App
Single file upload → DXF download
"""
import os, io, uuid, traceback
from flask import Flask, request, jsonify, send_file, render_template_string

app   = Flask(__name__)
store = {}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FMB Converter — Tamil Nadu</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#060609;--card:#0f0f18;--border:#1c1c2e;
  --accent:#6c63ff;--green:#00d4aa;--red:#ff4466;
  --text:#e0e0f0;--muted:#5a5a7a;--yellow:#f5c518
}
body{background:var(--bg);color:var(--text);
     font-family:'Space Grotesk',sans-serif;
     min-height:100vh;display:flex;flex-direction:column}

header{
  padding:20px 40px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:16px
}
.logo{
  width:42px;height:42px;border-radius:10px;
  background:linear-gradient(135deg,var(--accent),var(--green));
  display:grid;place-items:center;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:14px
}
.title{font-size:18px;font-weight:700}
.sub{color:var(--muted);font-size:12px;margin-top:2px}

main{flex:1;max-width:700px;margin:60px auto;padding:0 20px;width:100%}

.card{
  background:var(--card);border:1px solid var(--border);
  border-radius:16px;padding:40px;margin-bottom:24px
}

.zone{
  border:2px dashed var(--border);border-radius:12px;
  padding:50px 30px;text-align:center;cursor:pointer;
  transition:all .2s;position:relative
}
.zone:hover,.zone.drag{
  border-color:var(--accent);
  background:rgba(108,99,255,.05)
}
.zone input{position:absolute;inset:0;opacity:0;cursor:pointer;z-index:2}
.zone-icon{font-size:48px;margin-bottom:16px}
.zone-title{font-size:20px;font-weight:700;margin-bottom:8px}
.zone-sub{color:var(--muted);font-size:14px;margin-bottom:20px;line-height:1.6}

.btn{
  padding:13px 28px;border-radius:10px;border:none;
  font-size:15px;font-weight:600;cursor:pointer;
  font-family:inherit;transition:all .15s
}
.btn-primary{
  background:linear-gradient(135deg,var(--accent),#9b7dff);
  color:#fff;box-shadow:0 4px 20px rgba(108,99,255,.3)
}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 6px 28px rgba(108,99,255,.45)}
.btn-primary:disabled{opacity:.4;cursor:not-allowed;transform:none}
.btn-green{background:var(--green);color:#000;font-weight:700}
.btn-green:hover{transform:translateY(-1px)}

#selected-file{
  display:none;margin-top:16px;padding:14px 18px;
  background:var(--bg);border:1px solid var(--border);
  border-radius:10px;display:flex;align-items:center;gap:12px
}
.file-name{flex:1;font-family:'JetBrains Mono',monospace;font-size:13px}
.file-size{color:var(--muted);font-size:12px}

#convert-btn{width:100%;margin-top:20px;padding:16px;font-size:16px}

.progress{
  margin-top:16px;height:4px;background:var(--border);
  border-radius:2px;overflow:hidden;display:none
}
.progress-bar{
  height:100%;width:0%;
  background:linear-gradient(90deg,var(--accent),var(--green));
  transition:width .3s;animation:indeterminate 1.5s infinite
}
@keyframes indeterminate{
  0%{width:0%;margin-left:0}
  50%{width:60%;margin-left:20%}
  100%{width:0%;margin-left:100%}
}

#result{display:none;margin-top:24px}
.result-card{
  background:var(--card);border:1px solid var(--border);
  border-radius:14px;padding:24px;
  border-left:3px solid var(--green)
}
.result-sf{
  font-family:'JetBrains Mono',monospace;
  font-size:24px;font-weight:700;color:var(--accent);margin-bottom:4px
}
.result-loc{color:var(--muted);font-size:13px;margin-bottom:20px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px}
.stat{background:var(--bg);border-radius:8px;padding:12px 14px}
.stat-label{font-size:10px;text-transform:uppercase;letter-spacing:1px;
            color:var(--muted);margin-bottom:4px}
.stat-val{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700}
.layers{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px}
.layer{font-size:11px;font-family:'JetBrains Mono',monospace;
       padding:3px 9px;border-radius:4px;border:1px solid}
.l-r{color:#ff6680;border-color:#ff446630}
.l-g{color:#00d4aa;border-color:#00d4aa30}
.l-b{color:#6aabff;border-color:#6aabff30}
.l-y{color:#f5c518;border-color:#f5c51830}
.l-w{color:#ccc;border-color:#ccc3}
.l-p{color:#c088ff;border-color:#c088ff30}

#error{
  display:none;margin-top:16px;padding:14px 18px;
  background:#1a0508;border:1px solid var(--red);
  border-radius:10px;color:var(--red);font-size:14px
}
</style>
</head>
<body>
<header>
  <div class="logo">FMB</div>
  <div>
    <div class="title">FMB Converter</div>
    <div class="sub">Tamil Nadu Survey Department · PDF → DXF</div>
  </div>
</header>

<main>
  <div class="card">
    <div class="zone" id="zone">
      <input type="file" id="file-input" accept=".pdf">
      <div class="zone-icon">📐</div>
      <div class="zone-title">Upload FMB PDF</div>
      <div class="zone-sub">
        Government FMB PDF from eservices.tn.gov.in<br>
        Converts to DXF with exact measurements
      </div>
      <button class="btn btn-primary"
              onclick="event.stopPropagation();document.getElementById('file-input').click()">
        Select PDF
      </button>
    </div>

    <div id="selected-file" style="display:none">
      <span style="font-size:20px">📄</span>
      <span class="file-name" id="fname"></span>
      <span class="file-size" id="fsize"></span>
    </div>

    <button class="btn btn-primary" id="convert-btn"
            disabled onclick="convert()">
      Convert to DXF →
    </button>

    <div class="progress" id="prog">
      <div class="progress-bar" id="prog-bar"></div>
    </div>

    <div id="error"></div>
  </div>

  <div id="result">
    <div class="result-card">
      <div class="result-sf" id="r-sf"></div>
      <div class="result-loc" id="r-loc"></div>
      <div class="stats">
        <div class="stat">
          <div class="stat-label">Scale</div>
          <div class="stat-val" id="r-scale"></div>
        </div>
        <div class="stat">
          <div class="stat-label">Boundary Pts</div>
          <div class="stat-val" id="r-bpts"></div>
        </div>
        <div class="stat">
          <div class="stat-label">Measurements</div>
          <div class="stat-val" id="r-meas"></div>
        </div>
      </div>
      <div class="layers">
        <span class="layer l-r">BOUNDARY</span>
        <span class="layer l-w">SEPARATION_LINE</span>
        <span class="layer l-b">CHAIN_LINES</span>
        <span class="layer l-g">SUBDIVISION_LINES</span>
        <span class="layer l-y">BOUNDARY_DIMENSIONS</span>
        <span class="layer l-w">DIMENSIONS</span>
        <span class="layer l-b">CHAINLINE_DIMENSIONS</span>
        <span class="layer l-p">SUBDIVISION</span>
        <span class="layer l-w">STONES</span>
        <span class="layer l-r">SURVEY_NUMBER</span>
      </div>
      <button class="btn btn-green" onclick="download()" id="dl-btn">
        ⬇ Download DXF
      </button>
    </div>
  </div>
</main>

<script>
let file = null;
let dxf_id = null;

const zone  = document.getElementById('zone');
const input = document.getElementById('file-input');
const btn   = document.getElementById('convert-btn');
const prog  = document.getElementById('prog');
const errEl = document.getElementById('error');
const resEl = document.getElementById('result');

zone.addEventListener('dragover', e=>{e.preventDefault();zone.classList.add('drag')});
zone.addEventListener('dragleave', ()=>zone.classList.remove('drag'));
zone.addEventListener('drop', e=>{
  e.preventDefault();zone.classList.remove('drag');
  const f=e.dataTransfer.files[0];
  if(f&&f.name.endsWith('.pdf')) setFile(f);
});
input.addEventListener('change', ()=>{
  if(input.files[0]) setFile(input.files[0]);
});

function setFile(f){
  file=f;
  document.getElementById('fname').textContent=f.name;
  document.getElementById('fsize').textContent=(f.size/1024).toFixed(0)+' KB';
  document.getElementById('selected-file').style.display='flex';
  btn.disabled=false;
  errEl.style.display='none';
  resEl.style.display='none';
}

async function convert(){
  if(!file) return;
  btn.disabled=true;
  prog.style.display='block';
  errEl.style.display='none';
  resEl.style.display='none';

  try{
    const fd=new FormData();
    fd.append('pdf',file);
    const res=await fetch('/convert',{method:'POST',body:fd});
    const data=await res.json();

    if(data.ok){
      dxf_id=data.id;
      const inf=data.info;
      document.getElementById('r-sf').textContent='SF No. '+inf.sf_no;
      document.getElementById('r-loc').textContent=
        inf.district+' · '+inf.taluk+' · '+inf.village;
      document.getElementById('r-scale').textContent='1:'+inf.scale;
      document.getElementById('r-bpts').textContent=inf.boundary_pts;
      document.getElementById('r-meas').textContent=inf.measurements;
      resEl.style.display='block';
    } else {
      showErr(data.error);
    }
  } catch(e){
    showErr(e.message);
  } finally {
    prog.style.display='none';
    btn.disabled=false;
  }
}

function showErr(msg){
  errEl.textContent='❌ '+msg;
  errEl.style.display='block';
}

function download(){
  const a=document.createElement('a');
  a.href='/download/'+dxf_id;
  a.download='FMB_SF'+
    document.getElementById('r-sf').textContent.replace('SF No. ','')+'.dxf';
  a.click();
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/convert", methods=["POST"])
def convert_route():
    try:
        from converter import convert
        pdf_bytes = request.files["pdf"].read()
        dxf_bytes, info = convert(pdf_bytes, ANTHROPIC_API_KEY)
        fid = str(uuid.uuid4())
        store[fid] = dxf_bytes
        return jsonify({"ok": True, "id": fid, "info": info})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})


@app.route("/download/<fid>")
def download(fid):
    b = store.get(fid)
    if not b:
        return "Not found", 404
    return send_file(
        io.BytesIO(b),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="fmb_output.dxf"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)