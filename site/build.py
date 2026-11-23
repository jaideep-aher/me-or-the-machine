"""Fill site/template.html with numbers from data/ and write site/index.html.
Run: python3 site/build.py"""
import json, pathlib
R = pathlib.Path(__file__).resolve().parent.parent
res = json.loads((R/"data/results.json").read_text())
judges=[]
for r in res:
    if r.get("score_only"): k,n=r["correct"],r["n"]
    else: n=len(r["answers"]); k=sum(a["real"]==a["guessedReal"] for a in r["answers"])
    lab=r["participant"]+(" partner" if r["relationship"]=="partner" else "")
    judges.append(dict(label=lab,k=k,n=n))
d=[r for r in res if r.get("set")=="D"]
lines={}
for r in d:
    for a in r["answers"]: lines.setdefault(a["line"],{"real":a["real"],"votes":[]})["votes"].append(a["guessedReal"])
grid=[dict(line=l,real=v["real"],votes=v["votes"],unanimous=len(set(v["votes"]))==1) for l,v in sorted(lines.items(), key=lambda x:(not x[1]["real"], x[0]))]
S=json.loads((R/"analysis/summary.json").read_text())
items=sorted(S["items_seen_by_2_or_more"],key=lambda x:-x["called_him"]/x["judges"])
items=items[:5]+items[-5:]
data=dict(judges=judges,grid=grid,saved=dict(k=S["correct"],n=S["judgments"]),items=items)
t=(R/"site/template.html").read_text().replace("__DATA__",json.dumps(data))
(R/"site/index.html").write_text(t)
print(len(judges),"judges",len(grid),"lines",sum(g["unanimous"] for g in grid),"unanimous")
