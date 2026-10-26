"""Makes the printable wall posters: one QR code per mission station.

Usage: python make_qr.py [base_url]   (needs: pip install segno)
"""
import html
import json
import sys

import segno

from paths import CONTENT, DOCS

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://plateliai.lt/game/").rstrip("/") + "/"
codes = json.loads((CONTENT / "qr_codes.json").read_text(encoding="utf-8"))
quest = json.loads((CONTENT / "quest.lt.json").read_text(encoding="utf-8"))
titles = {str(m["n"]): m["title"] for m in quest["missions"]}

out = DOCS / "qr"
out.mkdir(parents=True, exist_ok=True)
pages = []
for n, code in codes.items():
    url = f"{BASE}#/unlock/{code}"
    qr = segno.make(url, error="h")
    qr.save(out / f"mission-{n}.svg", scale=10, border=2, dark="#0e1411")
    pages.append(f"""<section class="poster">
  <p class="kicker">OPERACIJA DVINA · MISIJA {n} / MISSION {n}</p>
  <h1>{html.escape(titles[n])}</h1>
  <img src="mission-{n}.svg" alt="QR: {html.escape(url)}">
  <p class="hint">Nuskenuok telefonu ir atrakink misiją · Scan with your phone to unlock the mission</p>
  <p class="url">{html.escape(url)}</p>
</section>""")

(out / "posters.html").write_text(f"""<!doctype html>
<html lang="lt"><head><meta charset="utf-8"><title>Operacija Dvina: QR posters</title>
<style>
  @page {{ size: A4; margin: 0; }}
  body {{ margin: 0; font-family: Inter, system-ui, sans-serif; color: #0e1411; background: #fff; }}
  .poster {{ height: 297mm; width: 210mm; box-sizing: border-box; padding: 24mm 20mm; display: flex; flex-direction: column;
            align-items: center; justify-content: center; text-align: center; page-break-after: always; }}
  .kicker {{ font: 600 14pt monospace; letter-spacing: .15em; color: #8a6d1f; margin: 0; }}
  h1 {{ font-size: 30pt; margin: 8mm 0 12mm; }}
  img {{ width: 120mm; height: 120mm; }}
  .hint {{ font-size: 15pt; margin: 12mm 0 4mm; }}
  .url {{ font: 9pt monospace; color: #666; }}
</style></head><body>
{chr(10).join(pages)}
</body></html>
""", encoding="utf-8", newline="\n")
print(f"{len(codes)} posters for {BASE} in {out}")
