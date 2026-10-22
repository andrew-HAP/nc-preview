#!/usr/bin/env python3
"""Issue locked, per-person copies of the preview.

For each copy: put the phone patch and the protection layer (watermark with the copy ID,
expiry, view-only blocks) into the export's page template, gzip it, encrypt it with that
copy's own access code, and write copies/<ID>.json. Also writes index.html from gate.html.

Switch a copy off: delete copies/<ID>.json and push. The register of who holds which code
lives outside this public repo (REGISTER below).

Usage: python3 issue.py <page.html> <expires YYYY-MM-DD> <ID>=<who>[|<two-word code>[|general]] ...
       (general: run general.py first; the gate shows general terms and the watermark drops "Noot")
       python3 issue.py --suggest 30      (print candidate codes; pick pleasant ones, the list has some odd words)
"""
import base64, csv, datetime, json, os, re, secrets, sys
from build import lock

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTER = os.path.expanduser("~/.claudeclaw/projects/happy-days/noot-central/copies.csv")
FONT = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-assistant0001x@gmail.com/My Drive/ClaudeClaw Projects/"
                          "Happy Days/02 — Design System/Claude plugin/source/skills/happy-days-house-style/assets/fonts/OpticianSans.woff2")
# Two plain words from the EFF large word list (letters only, 3 to 8 long: about 6,200 words, 38m pairs),
# kept outside this public repo. Easy to type on a phone; the gate ignores case, extra spaces and hyphens.
WORDLIST = os.path.expanduser("~/.claudeclaw/projects/happy-days/noot-central/eff_large_wordlist.txt")

def code():
    words = [l.split()[1] for l in open(WORDLIST) if l.strip()]
    words = [w for w in words if w.isalpha() and w.islower() and 3 <= len(w) <= 8 and not w.endswith(('ly', 'ed', 'ing'))]
    return " ".join(secrets.SystemRandom().sample(words, 2))

def strip_comments(s):
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)

def page_for(src, copy_id, exp_iso, exp_text, variant=""):
    t = open(src).read()
    m = re.search(r'(<script type="__bundler/template">)(.*?)(</script>)', t, re.S)
    tpl = json.loads(m.group(2))
    add = strip_comments(open(os.path.join(HERE, "mobile-patch.html")).read() + open(os.path.join(HERE, "protect.html")).read())
    if variant == "general":
        old = "'Noot · Happy Days · Confidential preview · '"
        assert old in add, "watermark label not found"
        add = add.replace(old, "'Happy Days · Confidential preview · '")
    add = add.replace("__COPY_ID__", copy_id).replace("__EXPIRES_ISO__", exp_iso).replace("__EXPIRES_TEXT__", exp_text)
    i = tpl.rindex("</body>"); tpl = tpl[:i] + add + tpl[i:]
    return (t[:m.start(2)] + "\n" + json.dumps(tpl).replace("</", "<\\u002F") + "\n" + t[m.end(2):]).encode()

if __name__ == "__main__":
    if sys.argv[1] == "--suggest":
        for _ in range(int(sys.argv[2])): print(code())
        sys.exit()
    src, exp = sys.argv[1], sys.argv[2]
    d = datetime.date.fromisoformat(exp)
    exp_iso = f"{exp}T23:59:59Z"
    exp_text = f"{d.day} {d.strftime('%B %Y')}"
    os.makedirs(os.path.join(HERE, "copies"), exist_ok=True)
    gate = open(os.path.join(HERE, "gate.html")).read().replace("__OPTICIAN_WOFF2__", base64.b64encode(open(FONT, "rb").read()).decode())
    open(os.path.join(HERE, "index.html"), "w").write(gate)
    new = not os.path.exists(REGISTER)
    with open(REGISTER, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["copy_id", "for", "access_code", "expires", "issued", "link"])
        for arg in sys.argv[3:]:
            cid, who = arg.split("=", 1)
            who, _, rest = who.partition("|")
            c, _, variant = rest.partition("|")
            c = " ".join(c.lower().split()) or code()
            data = lock(page_for(src, cid, exp_iso, exp_text, variant), c)
            data.update({"x": exp_iso, "xt": exp_text})
            if variant: data["v"] = variant
            json.dump(data, open(os.path.join(HERE, "copies", cid + ".json"), "w"))
            link = f"https://andrew-hap.github.io/nc-preview/?c={cid}"
            w.writerow([cid, who, c, exp_text, datetime.date.today().isoformat(), link])
            print(cid, who, c, link)
