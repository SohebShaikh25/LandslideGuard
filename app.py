from flask import Flask, render_template, jsonify, request, Response
import sqlite3, os, csv, io, json, urllib.request, urllib.parse
from datetime import datetime, timezone

app = Flask(__name__)
ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "data", "landslideguard.db")
LOCATIONS = [
 {"slug":"guwahati","name":"Guwahati","state":"Assam","lat":26.1445,"lon":91.7362},
 {"slug":"itanagar","name":"Itanagar","state":"Arunachal Pradesh","lat":27.0844,"lon":93.6053},
 {"slug":"shillong","name":"Shillong","state":"Meghalaya","lat":25.5788,"lon":91.8933},
 {"slug":"imphal","name":"Imphal","state":"Manipur","lat":24.8170,"lon":93.9368},
 {"slug":"aizawl","name":"Aizawl","state":"Mizoram","lat":23.7271,"lon":92.7176},
 {"slug":"kohima","name":"Kohima","state":"Nagaland","lat":25.6751,"lon":94.1086},
 {"slug":"gangtok","name":"Gangtok","state":"Sikkim","lat":27.3389,"lon":88.6065},
 {"slug":"agartala","name":"Agartala","state":"Tripura","lat":23.8315,"lon":91.2868},
]
# SIMULATED demo values only. Never interpret as actual weather observations.
DEMO = {
 "guwahati":(22,6,18,29,78),"itanagar":(96,28,58,23,91),
 "shillong":(74,19,32,20,88),"imphal":(18,4,12,27,72),
 "aizawl":(48,14,27,24,84),"kohima":(34,8,22,22,81),
 "gangtok":(112,38,72,15,93),"agartala":(12,2,9,30,70)
}

def db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS assessments(id INTEGER PRIMARY KEY,slug TEXT,name TEXT,state TEXT,score INTEGER,risk_level TEXT,source TEXT,rain_24h REAL,created_at TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY,slug TEXT,location TEXT,state TEXT,risk_level TEXT,score INTEGER,reason TEXT,source TEXT,status TEXT DEFAULT 'New',created_at TEXT)")
        if c.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]==0:
            c.executemany("INSERT INTO alerts(slug,location,state,risk_level,score,reason,source,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",[
            ("itanagar","Itanagar","Arunachal Pradesh","High",63,"Demo seed alert: sample rainfall indicators crossed a prototype threshold.","Simulated demo data","Acknowledged","2026-10-12T07:30:00Z"),
            ("shillong","Shillong","Meghalaya","Moderate",42,"Demo seed alert: elevated sample rainfall value; verify official sources.","Simulated demo data","New","2026-10-12T09:00:00Z")])
init_db()

def weather(lat,lon):
    try:
        q=urllib.parse.urlencode({"latitude":lat,"longitude":lon,"current":"temperature_2m,relative_humidity_2m,rain","hourly":"precipitation","forecast_days":2,"timezone":"Asia/Kolkata"})
        req=urllib.request.Request("https://api.open-meteo.com/v1/forecast?"+q,headers={"User-Agent":"LandslideGuardNE-Student-Project/1.0"})
        with urllib.request.urlopen(req,timeout=4) as r: d=json.loads(r.read().decode())
        h=d.get("hourly",{}); vals=h.get("precipitation",[]); times=h.get("time",[])
        now=d.get("current",{}).get("time"); i=times.index(now) if now in times else min(len(vals),24)
        cur=d.get("current",{})
        return {"rain_24h":round(sum(x or 0 for x in vals[max(0,i-23):i+1]),1),"rain_3h":round(sum(x or 0 for x in vals[max(0,i-2):i+1]),1),"forecast_24h":round(sum(x or 0 for x in vals[i+1:i+25]),1),"temperature":cur.get("temperature_2m"),"humidity":cur.get("relative_humidity_2m"),"source":"Open-Meteo weather API","updated_at":now or "API response"}
    except Exception: return None

def assess(x):
    score=0; reasons=[]; missing=[]
    for key, bands, label in [
      ("rain_24h",[(150,40),(80,28),(30,14)],"24-hour rainfall"),
      ("rain_3h",[(50,30),(25,20),(10,10)],"short-period rainfall"),
      ("forecast_24h",[(100,30),(50,20),(20,10)],"forecast rainfall")]:
        v=x.get(key)
        if v is None: missing.append(label+" unavailable"); continue
        try: v=float(v)
        except (ValueError,TypeError): missing.append(label+" unavailable"); continue
        if v<0: missing.append(label+" invalid"); continue
        for threshold,points in bands:
            if v>=threshold: score+=points; reasons.append(label+" indicator elevated"); break
    score=min(100,int(score))
    level="Low" if score<25 else "Moderate" if score<50 else "High" if score<75 else "Very High"
    advice={"Low":"Continue monitoring official weather updates; a low demo score does not mean no risk.","Moderate":"Stay alert during prolonged rain; check local advisories and avoid unstable slopes.","High":"Increase caution. Check official advisories and avoid steep cut slopes and vulnerable roads.","Very High":"This is only a prototype risk flag. Follow local authorities and move away from visibly unstable slopes if safe."}[level]
    return {"score":score,"risk_level":level,"reasons":reasons or ["No rainfall trigger crossed in available inputs"],"missing_inputs":missing,"advice":advice,"confidence_note":"Illustrative rainfall-only score, not a calibrated probability or official warning."}

def dashboard_data(live=False):
    out=[]
    for loc in LOCATIONS:
        w=weather(loc["lat"],loc["lon"]) if live else None
        if w is None:
            a,b,c,t,h=DEMO[loc["slug"]]
            w={"rain_24h":a,"rain_3h":b,"forecast_24h":c,"temperature":t,"humidity":h,"source":"Simulated demo data","updated_at":"Demo dataset"}
        item={**loc,**w,**assess(w)}
        out.append(item)
        with db() as conn:
            conn.execute("INSERT INTO assessments(slug,name,state,score,risk_level,source,rain_24h,created_at) VALUES(?,?,?,?,?,?,?,?)",(item["slug"],item["name"],item["state"],item["score"],item["risk_level"],item["source"],item.get("rain_24h"),datetime.now(timezone.utc).isoformat()))
            if item["risk_level"] in ("High","Very High"):
                recent=conn.execute("SELECT id FROM alerts WHERE slug=? AND status!='Resolved' AND created_at >= datetime('now','-6 hours')",(item["slug"],)).fetchone()
                if not recent:
                    conn.execute("INSERT INTO alerts(slug,location,state,risk_level,score,reason,source,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(item["slug"],item["name"],item["state"],item["risk_level"],item["score"],"; ".join(item["reasons"]),item["source"],"New",datetime.now(timezone.utc).isoformat()))
    with db() as c: alerts=[dict(r) for r in c.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50")]
    counts={k:sum(1 for l in out if l["risk_level"]==k) for k in ["Low","Moderate","High","Very High"]}
    return {"locations":out,"alerts":alerts,"stats":{"monitored":len(out),"attention":sum(x["risk_level"] in ("High","Very High") for x in out),"active_alerts":sum(a["status"]!="Resolved" for a in alerts),"risk_counts":counts},"mode":"live" if live else "demo","generated_at":datetime.now(timezone.utc).isoformat()}

@app.route("/")
def index(): return render_template("index.html")
@app.route("/api/dashboard")
def api_dashboard(): return jsonify(dashboard_data(request.args.get("mode")=="live"))
@app.route("/api/alerts/<int:alert_id>",methods=["POST"])
def update_alert(alert_id):
    status=(request.get_json(silent=True) or {}).get("status")
    if status not in {"New","Acknowledged","Resolved"}: return jsonify({"error":"Invalid status"}),400
    with db() as c: c.execute("UPDATE alerts SET status=? WHERE id=?",(status,alert_id))
    with db() as c: alerts=[dict(r) for r in c.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50")]
    return jsonify({"ok":True,"alerts":alerts})
@app.route("/api/history")
def history():
    slug=request.args.get("slug","")
    with db() as c: rows=[dict(r) for r in c.execute("SELECT score,risk_level,source,rain_24h,created_at FROM assessments WHERE slug=? ORDER BY id DESC LIMIT 20",(slug,))]
    return jsonify(rows)
@app.route("/api/export.csv")
def export_csv():
    s=io.StringIO(); w=csv.writer(s); w.writerow(["name","state","latitude","longitude","note"])
    for l in LOCATIONS:w.writerow([l["name"],l["state"],l["lat"],l["lon"],"Reference location, not a hazard observation"])
    return Response(s.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=monitoring_locations.csv"})
@app.route("/health")
def health(): return jsonify({"status":"ok","app":"LandslideGuard NE"})
if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=True)
