"""Build poster/poster.html (24 x 24 in) with every chart drawn from the data.

Reads data/results.json, data/lines.json, analysis/summary.json, analysis/rigor.json.
Run:  python3 poster/build_poster.py
Then print to PDF with headless Chrome (see README).
"""
import json, pathlib, html

R = pathlib.Path(__file__).resolve().parent.parent
S = json.loads((R / "analysis/summary.json").read_text())
G = json.loads((R / "analysis/rigor.json").read_text())
RES = json.loads((R / "data/results.json").read_text())
LINES = {l["id"]: l for l in json.loads((R / "data/lines.json").read_text())["lines"]}
URL = "https://jaideep-aher.github.io/me-or-the-machine-site/"

INK, MUTED, LINE, ACC, TWIN, TRACK = "#131A24", "#4D5968", "#C3CCD6", "#1F4FD8", "#B34E14", "#D9E0E8"
ACC_S, TWIN_S = "#DCE4FA", "#F6E1D3"
k, n = S["correct"], S["judgments"]
pct = lambda a, b: round(100 * a / b)


def waffle():
    cols, s, g = 16, 30, 7
    rows = -(-n // cols)
    out = [f'<svg viewBox="0 0 {cols*(s+g)} {rows*(s+g)}" width="100%">']
    for i in range(n):
        c, r = i % cols, i // cols
        out.append(f'<rect x="{c*(s+g)}" y="{r*(s+g)}" width="{s}" height="{s}" rx="4" fill="{"#FFFFFF" if i < k else "#3A4553"}"/>')
    half = n // 2
    hx, hy = (half % cols) * (s + g) - g / 2, (half // cols) * (s + g)
    out.append(f'<path d="M{hx} {hy-4} V{hy+s+g}" stroke="#F0A067" stroke-width="5"/>')
    out.append("</svg>")
    return "".join(out)


def bars():
    real, twin = S["real_counts"], S["twin_counts"]
    W = 560
    out = [f'<svg viewBox="0 0 720 250" width="100%">']
    for i, (lab, (a, b), col) in enumerate([("My real lines called “him”", real, ACC), ("Twin lines called “him”", twin, TWIN)]):
        y = 40 + i * 115
        out.append(f'<text x="0" y="{y}" font-size="30" fill="{INK}">{lab}: {a} of {b}</text>')
        out.append(f'<rect x="0" y="{y+16}" width="{W}" height="54" rx="6" fill="{TRACK}"/>')
        out.append(f'<rect x="0" y="{y+16}" width="{W*a/b:.0f}" height="54" rx="6" fill="{col}"/>')
        out.append(f'<text x="{W+24}" y="{y+60}" font-size="54" font-weight="700" font-family="Bricolage Grotesque" fill="{INK}">{pct(a,b)}%</text>')
    out.append(f'<line x1="{W/2}" x2="{W/2}" y1="44" y2="236" stroke="{INK}" stroke-width="3" stroke-dasharray="8 8"/>')
    out.append(f'<text x="{W/2+10}" y="246" font-size="24" fill="{MUTED}">50%</text></svg>')
    return "".join(out)


def judges():
    rows = []
    for r in RES:
        if r.get("score_only"):
            a, b = r["correct"], r["n"]
        else:
            b = len(r["answers"]); a = sum(x["real"] == x["guessedReal"] for x in r["answers"])
        rows.append((r["participant"] + (" girlfriend" if r["relationship"] == "partner" else ""), a, b, bool(r.get("score_only"))))
    W, L, Rm, rh = 760, 170, 70, 31
    H = len(rows) * rh + 60
    X = lambda p: L + (W - L - Rm) * p
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%">']
    for t in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{X(t)}" x2="{X(t)}" y1="6" y2="{H-44}" stroke="{INK if t==.5 else LINE}" stroke-width="{3 if t==.5 else 1.5}" {"stroke-dasharray=\"8 8\"" if t==.5 else ""}/>')
        out.append(f'<text x="{X(t)}" y="{H-12}" text-anchor="middle" font-size="24" fill="{MUTED}">{int(t*100)}%</text>')
    for i, (lab, a, b, so) in enumerate(rows):
        y, p = 28 + i * rh, a / b
        col = ACC if p > .5 else (TWIN if p < .5 else INK)
        out.append(f'<text x="0" y="{y+9}" font-size="26" fill="{INK}">{lab}</text>')
        out.append(f'<line x1="{X(.5)}" x2="{X(p)}" y1="{y}" y2="{y}" stroke="{LINE}" stroke-width="4"/>')
        out.append(f'<circle cx="{X(p)}" cy="{y}" r="13" fill="{"none" if so else col}" stroke="{col}" stroke-width="4"/>')
        out.append(f'<text x="{X(p)+(24 if p>=.5 else -24)}" y="{y+9}" text-anchor="{"start" if p>=.5 else "end"}" font-size="24" fill="{MUTED}">{a}/{b}</text>')
    out.append("</svg>")
    return "".join(out)


def grid():
    d = [r for r in RES if r.get("set") == "D"]
    votes = {}
    for r in d:
        for a in r["answers"]:
            votes.setdefault(a["line"], [a["real"], []])[1].append(a["guessedReal"])
    items = sorted(votes.items(), key=lambda x: (not x[1][0], x[0]))
    cw, ch, top, left = 50, 40, 44, 70
    W = left + len(items) * cw
    out = [f'<svg viewBox="0 0 {W} {top+len(d)*ch+8}" width="100%">']
    for ci, (line, (real, v)) in enumerate(items):
        x = left + ci * cw
        out.append(f'<rect x="{x+3}" y="4" width="{cw-6}" height="28" rx="5" fill="{ACC_S if real else TWIN_S}" stroke="{ACC if real else TWIN}" stroke-width="2"/>')
        out.append(f'<text x="{x+cw/2}" y="25" text-anchor="middle" font-size="18" font-weight="600" fill="{ACC if real else TWIN}">{"me" if real else "AI"}</text>')
        for ri, g in enumerate(v):
            out.append(f'<rect x="{x+3}" y="{top+ri*ch}" width="{cw-6}" height="{ch-6}" rx="5" fill="{ACC if g else TWIN}"/>')
        if len(set(v)) == 1:
            out.append(f'<rect x="{x-1}" y="{top-6}" width="{cw+2}" height="{len(v)*ch+6}" rx="7" fill="none" stroke="{INK}" stroke-width="4"/>')
    for ri in range(len(d)):
        out.append(f'<text x="0" y="{top+ri*ch+25}" font-size="22" fill="{MUTED}">F{ri+1}</text>')
    out.append("</svg>")
    return "".join(out)


ICONS = {
    "mic": '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v4"/>',
    "leak": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M9 15l2 2 4-4"/>',
    "chip": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>',
    "msg": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M8 9h8M8 13h5"/>',
}
icon = lambda name, col=INK: f'<svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="{col}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'

pw, pm = G["power"]["min_detectable_accuracy_80pct_power"], G["equivalence_tost"]["p"]
bf, kap, mb = G["bayes_factor_01"], G["fleiss_kappa_set_d"]["kappa"], G["machine_baseline"]
lo, hi = S["accuracy_ci95"]
jl = S["judge_level_saved"]
d = S["set_d"]
biryani = html.escape(LINES[62]["text"])

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Me or the Machine poster</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Instrument+Sans:wght@400;500;600&display=swap">
<style>
/* Generated by poster/build_poster.py. 24 x 24 in at 96 px per inch. Tokens match DESIGN.md. */
@page {{ size: 24in 24in; margin: 0 }}
*{{box-sizing:border-box}}
html,body{{margin:0;width:2304px;height:2304px;background:#EEF1F4;color:{INK};font-family:"Instrument Sans","Helvetica Neue",sans-serif;font-size:27px;line-height:1.38;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:2304px;height:2304px;padding:64px 96px 56px;display:grid;grid-template-rows:auto auto 1fr auto;gap:30px}}
h1,h2,h3{{font-family:"Bricolage Grotesque",sans-serif;margin:0}}
h1{{font-weight:800;font-size:86px;line-height:.95;letter-spacing:-.03em}}
.kick{{font-family:"Bricolage Grotesque";font-weight:700;font-size:34px;color:{ACC};margin-bottom:10px}}
.pend{{display:grid;grid-template-columns:54px 1fr;gap:16px;background:#fff;border:2px solid {LINE};border-radius:14px;padding:18px 20px;font-size:23px;color:{MUTED};line-height:1.3}}
.pend b{{display:block;font-family:"Bricolage Grotesque";font-size:30px;color:{INK};line-height:1.15;margin-bottom:4px}}
h2{{font-weight:700;font-size:46px;line-height:1.05;margin-bottom:16px;letter-spacing:-.01em}}
h3{{font-weight:700;font-size:30px;line-height:1.15;margin-bottom:4px}}
p{{margin:0 0 12px}}
.muted{{color:{MUTED}}}
.head{{display:grid;grid-template-columns:1fr 760px 200px;gap:44px;align-items:end;padding-bottom:24px;border-bottom:5px solid {INK}}}
.q{{font-family:"Bricolage Grotesque",sans-serif;font-weight:500;font-size:32px;line-height:1.15}}
.by{{font-size:24px;color:{MUTED};margin-top:16px}}
.qr{{text-align:center;font-size:20px;color:{MUTED}}}
.qr #qr{{background:#fff;padding:12px;border-radius:8px;border:2px solid {INK};margin-bottom:8px}}
.row{{display:grid;gap:56px;min-height:0}}
.r1{{grid-template-columns:600px 1fr 560px}}
.r2{{grid-template-columns:1fr 1fr 1fr;align-items:start}}
.card{{background:#fff;border:2px solid {LINE};border-radius:10px;padding:28px}}
.hero{{background:{INK};color:#fff;border-radius:10px;padding:34px 40px;display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center}}
.hero .big{{font-family:"Bricolage Grotesque";font-weight:800;font-size:230px;line-height:.8;letter-spacing:-.05em}}
.hero .cap{{font-size:34px;line-height:1.25;margin:18px 0 10px}}
.hero .sub{{font-size:22px;color:#B9C4D2}}
.chain{{display:grid;gap:0}}
.chain>div{{display:grid;grid-template-columns:70px 1fr;gap:14px;padding:16px 0;border-top:3px solid {INK}}}
.chain>div:last-child{{border-top-color:{TWIN}}}
.chain p{{margin:0;font-size:24px;color:{MUTED}}}
.figs{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:18px}}
.figs b{{display:block;font-family:"Bricolage Grotesque";font-weight:800;font-size:50px;line-height:1}}
.figs span{{font-size:19px;color:{MUTED};line-height:1.3;display:block;margin-top:6px}}
.phone{{background:#fff;border:2px solid {LINE};border-radius:40px;padding:28px 26px}}
.who{{display:flex;gap:14px;align-items:center;padding-bottom:18px;border-bottom:2px solid {LINE};margin-bottom:22px}}
.av{{width:54px;height:54px;border-radius:50%;background:{ACC};color:#fff;display:grid;place-items:center;font:700 26px "Bricolage Grotesque"}}
.bub{{background:#E2E7ED;border-radius:26px 26px 26px 8px;padding:18px 22px;font-size:30px;line-height:1.35;margin-bottom:20px}}
.vote{{display:flex;justify-content:space-between;font-size:24px;color:{MUTED};padding:14px 12px;border-top:2px dashed {LINE}}}
.vote b{{color:{ACC}}}
.ans{{background:{TWIN_S};border-radius:16px;padding:18px 22px;font-size:26px;line-height:1.35}}
.ans b{{color:{TWIN}}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 24px;font-size:21px;color:{MUTED};margin-top:12px}}
.legend i{{display:inline-block;width:20px;height:20px;border-radius:4px;margin-right:8px;vertical-align:-3px}}
.rig{{width:100%;border-collapse:collapse;font-size:25px}}
.rig td{{padding:13px 8px;border-top:2px solid {LINE};vertical-align:top}}
.rig tr:first-child td{{border-top:0}}
.rig td:first-child{{color:{MUTED};width:44%}}
ul{{margin:0;padding-left:30px}} li{{margin-bottom:10px}}
.pts div{{padding:8px 0;border-top:2px solid {LINE}}} .pts div:first-child{{border-top:0;padding-top:0}}
.pts p{{margin:0;font-size:21px;color:{MUTED}}}
.foot{{display:grid;grid-template-columns:1fr 1.2fr .8fr;gap:44px;border-top:5px solid {INK};padding-top:26px;font-size:20px;color:{MUTED};line-height:1.35}}
.foot b{{color:{INK}}}
.jshot{{margin:14px 0 0}} .jshot img{{display:block;width:100%;border:2px solid {LINE};border-radius:10px}} .jshot figcaption{{font-size:21px;line-height:1.3;color:{MUTED};margin-top:8px}} .jshot b{{color:{INK}}}
.scare{{border:2px solid {TWIN};background:{TWIN_S};border-radius:10px;padding:14px 18px;font-family:"Bricolage Grotesque";font-weight:500;font-size:25px;line-height:1.3}}
.holds{{margin-top:18px;display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.holds .hh{{grid-column:1/3;font-size:28px;margin-bottom:4px}}
.holds div{{background:#fff;border:2px solid {LINE};border-radius:8px;padding:10px 14px;font-size:21px;line-height:1.25}}
.leaks{{display:grid;gap:12px}}
.leaks div{{display:grid;grid-template-columns:78px 1fr;gap:12px;font-size:21px;line-height:1.3;color:{MUTED}}}
.leaks b{{font-family:"Bricolage Grotesque";font-weight:800;font-size:28px;color:{TWIN};line-height:1.05}}
.leaks i{{font-style:normal;font-weight:600;color:{INK}}}
.advice{{background:{INK};color:#EEF1F4;border-radius:12px;padding:20px 24px;margin-top:18px}}
.advice h3{{color:#fff;font-size:28px;margin-bottom:8px}}
.advice div{{font-size:21px;line-height:1.3;padding:5px 0 5px 22px;position:relative}}
.advice div::before{{content:"";position:absolute;left:0;top:14px;width:10px;height:10px;border-radius:50%;background:#F0A067}}
.nsteps{{margin:0;padding-left:0;list-style:none;counter-reset:n;display:grid;gap:0}}
.nsteps li{{counter-increment:n;display:grid;grid-template-columns:50px 1fr;gap:6px;padding:10px 0;border-top:2px solid {LINE};font-size:22px;line-height:1.28;color:{MUTED}}}
.nsteps li:first-child{{border-top:0;padding-top:4px}}
.nsteps li::before{{content:counter(n);font-family:"Bricolage Grotesque";font-weight:800;font-size:40px;line-height:1;color:{ACC}}}
.nsteps b{{color:{INK}}}
.next ol{{margin:6px 0 0;padding-left:26px;columns:2;column-gap:34px;font-size:21px;color:{INK}}} .next li{{margin-bottom:4px;break-inside:avoid}}
.next>b{{font-family:"Bricolage Grotesque";font-size:30px}}

</style></head><body><div class="page">

<header class="head">
  <div><div class="kick">Me or the Machine</div><h1>I've been recorded 24/7 for 7 weeks. Now an AI can be me.</h1>
  <div class="by">Jaideep Aher, Duke University, AIPI 590 Responsible AI, fall 2026</div></div>
  <div><div class="pend">{icon("mic", ACC)}<div><b>It only needed 48 of my sentences.</b>A Bee pendant has recorded nearly everything I have said since 2 October. An AI read 48 lines from it and wrote 47 more in my voice.</div></div>
  <div class="q" style="margin-top:18px">My girlfriend scored 50% at telling us apart, on her third try. So would a coin.</div></div>
  <div class="qr"><div id="qr"></div>Take the test, see the charts</div>
</header>

<section class="row r1">
  <div>
    <div class="scare">Its AI summaries had picked up my finances and private health information. I never thought of those talks as recorded. It scared me.</div>
    <figure class="jshot"><img src="jarvis-memory-strip.jpg" alt=""><figcaption><b>Jarvis, the AI I built and gave my life to:</b> 7,273 things from 11 sources, including 3 Gmail accounts and the Bee pendant. It also tracks my location, every app I open and my patterns.</figcaption></figure>
    <div>
      <h2 style="margin-top:34px">How the test worked</h2>
      <p style="font-size:24px">I took <b style="color:{ACC}">48 real lines</b> from the pendant, after removing anything private. A language model read them and wrote <b style="color:{TWIN}">47 twin lines</b>. Ten people who know me judged one shuffled line at a time: "really him" or "AI twin". All knew some were fake.</p>
    </div>
    <div style="margin-top:30px">
    <h2>Twin lines passed as often</h2>
    <div class="card">{bars()}</div>
    <p class="muted" style="margin-top:12px;font-size:23px">Sensitivity d′ = {S["signal_detection"]["d_prime"]:.2f} (0 = cannot tell apart). Friends said "him" {S["said_real_rate"]*100:.1f}% of the time, which helps an impostor.</p>
    </div>

  </div>

  <div style="display:grid;gap:28px;align-content:start">
    <div class="hero">
      <div><div class="big">{pct(k,n)}%</div><div class="cap">of {n} saved judgments were right. A coin flip.</div>
      <div class="sub">{k} of {n}, 95% interval {lo*100:.0f}% to {hi*100:.0f}%, p = {S["p_vs_chance"]:.2f}. Per judge: mean {jl["mean_accuracy"]*100:.0f}%. With three reported 30-line scores: {S["all_correct"]} of {S["all_judgments"]} ({S["all_accuracy"]*100:.0f}%).</div></div>
      <div>{waffle()}<div class="legend" style="color:#B9C4D2"><span><i style="background:#fff"></i>Right ({k})</span><span><i style="background:#3A4553"></i>Wrong ({n-k})</span><span><i style="background:#F0A067;width:6px"></i>50% mark</span></div></div>
    </div>
    <div>    <h2>Evidence of no skill, not too little data</h2>
    <div class="card"><table class="rig">
      <tr><td>Could this sample catch real skill?</td><td><b>Yes.</b> A true accuracy of {pw*100:.0f}% would show 80% of the time.</td></tr>
      <tr><td>Accuracy within 50% ± 10?</td><td><b>Yes.</b> Equivalence test p = {pm:.3f}.</td></tr>
      <tr><td>Guessing or some ability?</td><td><b>Guessing</b>, about {bf:.0f} times more likely (Bayes factor).</td></tr>
      <tr><td>Can a style detector do better?</td><td><b>No.</b> {mb["accuracy"]*100:.0f}% on all 95 lines, p = {mb["permutation_p"]:.2f}.</td></tr>
    </table></div>
    </div>
  </div>

  <div>
    <h2>One line, four friends</h2>
    <div class="phone">
      <div class="who"><div class="av">J</div><div><b style="font-size:28px">Jaideep</b><br><span class="muted" style="font-size:21px">one line, no context</span></div></div>
      <div class="bub">{biryani}</div>
      <div class="vote"><span>Four friends judged it</span><b>4 of 4: "it's him"</b></div>
      <div class="ans"><b>The AI twin wrote it.</b> It was the only line all four agreed on, and they were all wrong.</div>
    </div>
    <h2 style="margin-top:30px">Friends didn't agree</h2>
    <div class="card">{grid()}<div class="legend"><span><i style="background:{ACC}"></i>Said "him"</span><span><i style="background:{TWIN}"></i>Said "AI"</span><span>Columns: the 20 shared lines</span></div></div>
    <p class="muted" style="margin-top:14px">Agreement was below chance (Fleiss' κ = {kap:.2f}); their majority vote was right on only {d["majority_right"]} of 20.</p>

  </div>
</section>

<section class="row r2">
  <div>
    <h2>Next steps</h2>
    <ol class="nsteps">
      <li><div><b>A twin that knows nothing about me.</b> The missing control: does personal data matter at all?</div></li>
      <li><div><b>A twin fed all seven weeks.</b> How much do the recordings themselves add to the risk?</div></li>
      <li><div><b>Real conversations and a cloned voice,</b> where shared memories should help friends.</div></li>
      <li><div><b>Can people learn?</b> The live test now gives instant feedback; those rounds show if accuracy rises.</div></li>
      <li><div><b>Test the defence:</b> does a family check question stop a twin?</div></li>
      <li><div><b>Audit AI recorders:</b> what each stores, for how long, and who can see it.</div></li>
    </ol>
  </div>

  <div>
    <h2>Nobody was reliably good</h2>
    <p class="muted" style="font-size:23px;margin-top:-6px">Each dot is one judge. Only one scored above 50% (14 of 20, not significant alone).</p>
    <div class="card">{judges()}<div class="legend"><span><i style="background:{ACC};border-radius:50%"></i>Above 50%</span><span><i style="background:{TWIN};border-radius:50%"></i>Below</span><span><i style="border:3px solid {MUTED};border-radius:50%"></i>Reported score, not saved</span></div></div>
  </div>

  <div>
    <h2>Leaks are not hypothetical</h2>
    <div class="leaks">
      <div><b>2023</b><span><i>Amazon, now Bee's owner,</i> paid $25M for keeping kids' Alexa voice recordings after deletion requests.</span></div>
      <div><b>2023</b><span><i>23andMe:</i> genetic data of 6.9M people stolen, unnoticed for months.</span></div>
      <div><b>2025</b><span><i>DeepSeek</i> left users' chat logs online with no password.</span></div>
    </div>
    <p class="muted" style="font-size:22px;margin:12px 0 0">Leaked pendant data could be used to impersonate you, blackmail you, guess your security answers, find you, and expose everyone you talk to.</p>
    <div class="advice"><h3>Should you wear one? Think hard. If you do:</h3>
      <div>Assume it leaks one day; mute it for private talk</div><div>Delete transcripts often; prefer on-device processing</div><div>Strong password, two-factor login, few connected apps</div><div>Agree a family check question; never pay because of a text</div>
    </div>
  </div>
</section>

<footer class="foot">
  <div><b>Limits.</b> Ten judges; three 30-line scores were reported, not saved. Twin lines were written with my real lines in view, the best case for the twin. Real lines keep speech-to-text errors.</div>
  <div><b>Ethics.</b> Judges knew some lines were AI-written; nothing was sent as me. <b>Related work.</b> Turing (1950), Computing Machinery and Intelligence. Jones and Bergen (2025), Large Language Models Pass the Turing Test. Park et al. (2024), Generative Agent Simulations of 1,000 People.</div>
  <div><b>Links.</b> {URL.replace("https://","").rstrip("/")} (page, live test, report). Code and data: private repository shared with instructors.</div>
</footer>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script>
<script>const q=qrcode(0,"M");q.addData("{URL}");q.make();document.getElementById("qr").innerHTML=q.createSvgTag({{scalable:true,margin:0}});</script>
</body></html>
"""
(R / "poster/poster.html").write_text(page)
print("wrote poster/poster.html")
