import csv,json,datetime,urllib.request,urllib.parse,io,re,os
from pathlib import Path
out={"generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"indicators":{},"errors":{}}
def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; Fondo3Dashboard/1.0)","Accept":"application/json,text/csv,*/*"})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode("utf-8-sig")
def put(k,v,date,source,history=None):
 v=float(v)
 if v==v and abs(v)<1e10:out["indicators"][k]={"value":v,"date":date,"src":source,"h":history or []}
for k,code in [("vix","VIXCLS"),("us10y","DGS10")]:
 try:
  s=fetch("https://fred.stlouisfed.org/graph/fredgraph.csv?id="+code+"&cosd="+(datetime.date.today()-datetime.timedelta(days=120)).isoformat())
  rows=list(csv.DictReader(io.StringIO(s))); hist=[]
  for row in rows:
   v=row.get(code,".")
   if v not in (".",""):
    hist.append({"date":row.get("DATE") or row.get("observation_date"),"value":float(v)})
  if hist:put(k,hist[-1]["value"],hist[-1]["date"],"FRED · "+code,hist[-65:])
 except Exception as e:out["errors"][k]=str(e)
for k,symbol in [("sp500","%5EGSPC"),("emerging","EEM")]:
 try:
  j=json.loads(fetch("https://query1.finance.yahoo.com/v8/finance/chart/"+symbol+"?range=3mo&interval=1d"))
  r=j["chart"]["result"][0];closes=r["indicators"]["quote"][0]["close"];hist=[]
  for t,v in zip(r["timestamp"],closes):
   if v is not None:hist.append({"date":datetime.datetime.fromtimestamp(t,datetime.timezone.utc).date().isoformat(),"value":float(v)})
  if hist:put(k,hist[-1]["value"],hist[-1]["date"],"Yahoo Finance · "+symbol,hist[-65:])
 except Exception as e:out["errors"][k]=str(e)
try:
 codes=["PD12912AM","PD38048AM","PD38049AM"]
 j=json.loads(fetch("https://estadisticas.bcrp.gob.pe/estadisticas/series/api/"+"-".join(codes)+"/json"))
 months={"ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,"jul":7,"ago":8,"set":9,"sep":9,"oct":10,"nov":11,"dic":12,"jan":1,"apr":4,"aug":8,"dec":12}
 for i,k in enumerate(["inflation","gdp","fx"]):
  for p in reversed(j.get("periods",[])):
   try:
    v=float(str(p["values"][i]).replace(",","."))
    name=p["name"].lower();y=re.search(r"20\d{2}|\d{2}$",name)
    if not y:continue
    year=y.group();year="20"+year if len(year)==2 else year
    m=months.get(name[:3])
    if not m:continue
    put(k,v,f"{year}-{m:02d}-01","BCRP · "+p["name"]);break
   except (ValueError,TypeError,IndexError,KeyError):continue
except Exception as e:out["errors"]["bcrp"]=str(e)
# La tabla SBS requiere validación de columnas; no inventar valores cuota.
out["errors"]["sbs"]="Pendiente de integración verificada con fuente SBS/Profuturo"
Path("data.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("Actualizados:",list(out["indicators"]),"Errores:",out["errors"])
