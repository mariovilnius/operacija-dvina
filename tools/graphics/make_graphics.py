"""Draws the quest's figures as SVG into app/img/.

- range-map.svg: R-12 range from Plokštinė, azimuthal equidistant projection centred on the base,
  so the 2 000 km range [S1] is an exact circle. Country outlines: Natural Earth via world-atlas
  (public domain), data/geo/countries-50m.json.
- base-plan.svg: schematic plan (not to scale): control block, 4 shafts, 6 fence lines, military
  town 500 m away, 2.5 km water pipe to Lake Plateliai [S1][S2].
- shaft-section.svg: shaft 27 m deep [S1], about 5 m across [S3], R-12 23 m = 19 m + 4 m [S1],
  with a 1.8 m person for scale.
Labels are numbers only; the app adds a translated caption.
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "img"
OUT.mkdir(parents=True, exist_ok=True)

BG, LAND, BORDER, ACCENT, RED, TEXT, MUTED = "#0e1411", "#1d2722", "#33423a", "#d6b25e", "#ef7d6b", "#e9ece6", "#9aa69f"
MONO = "font-family=\"IBM Plex Mono, ui-monospace, monospace\""

# Plokštinė missile base (Šaltojo karo ekspozicija, OSM node 410889888)
LAT0, LON0 = math.radians(56.032266), math.radians(21.906289)
EARTH_KM = 6371.0
TARGETS = {"Norway", "United Kingdom", "Spain", "Germany", "Turkey"}  # S1; Germany drawn with today's borders


def project(lon: float, lat: float) -> tuple[float, float] | None:
    """Azimuthal equidistant projection centred on the base; returns km east/north."""
    lon, lat = math.radians(lon), math.radians(lat)
    cos_c = math.sin(LAT0) * math.sin(lat) + math.cos(LAT0) * math.cos(lat) * math.cos(lon - LON0)
    c = math.acos(max(-1.0, min(1.0, cos_c)))
    if c > math.radians(60):  # far side of the globe: not on this map
        return None
    k = c / math.sin(c) if c else 1.0
    x = k * math.cos(lat) * math.sin(lon - LON0)
    y = k * (math.cos(LAT0) * math.sin(lat) - math.sin(LAT0) * math.cos(lat) * math.cos(lon - LON0))
    return x * EARTH_KM, y * EARTH_KM


def range_map() -> None:
    topo = json.loads((ROOT / "data" / "geo" / "countries-50m.json").read_text(encoding="utf-8"))
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        points = []
        for dx, dy in arc:
            x, y = x + dx, y + dy
            points.append((x * sx + tx, y * sy + ty))
        arcs.append(points)

    size, view_km = 1000, 2700
    scale = (size / 2 - 20) / view_km

    def ring(indices: list[int]) -> str:
        pts = []
        for i in indices:
            arc = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(arc[1:] if pts else arc)
        out, last = [], None
        for lon, lat in pts:
            p = project(lon, lat)
            if p is None:
                return ""
            px, py = size / 2 + p[0] * scale, size / 2 - p[1] * scale
            if last and abs(px - last[0]) + abs(py - last[1]) < 1.2:
                continue
            out.append(f"{px:.1f},{py:.1f}")
            last = (px, py)
        return "M" + "L".join(out) + "Z" if len(out) > 2 else ""

    land, targets = [], []
    for g in topo["objects"]["countries"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
        d = "".join(ring(r) for poly in polys for r in poly)
        if d:
            (targets if g["properties"]["name"] in TARGETS else land).append(d)

    r2000 = 2000 * scale
    c = size / 2
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" aria-label="R-12 range map">
<defs><clipPath id="v"><circle cx="{c}" cy="{c}" r="{c - 20}"/></clipPath></defs>
<rect width="{size}" height="{size}" fill="{BG}"/>
<g clip-path="url(#v)">
  <circle cx="{c}" cy="{c}" r="{c - 20}" fill="#0b1310"/>
  <path d="{''.join(land)}" fill="{LAND}" stroke="{BORDER}" stroke-width="0.8" fill-rule="evenodd"/>
  <path d="{''.join(targets)}" fill="{ACCENT}" fill-opacity="0.45" stroke="{ACCENT}" stroke-width="1.2" fill-rule="evenodd"/>
  <circle cx="{c}" cy="{c}" r="{r2000:.1f}" fill="{RED}" fill-opacity="0.06" stroke="{RED}" stroke-width="3" stroke-dasharray="12 8"/>
  <circle cx="{c}" cy="{c}" r="{1000 * scale:.1f}" fill="none" stroke="{RED}" stroke-opacity="0.35" stroke-width="1.5" stroke-dasharray="4 8"/>
</g>
<circle cx="{c}" cy="{c}" r="{c - 20}" fill="none" stroke="{BORDER}" stroke-width="2"/>
<circle cx="{c}" cy="{c}" r="9" fill="{RED}"/><circle cx="{c}" cy="{c}" r="18" fill="none" stroke="{RED}" stroke-width="2"/>
<text x="{c + 26}" y="{c + 6}" fill="{TEXT}" font-size="22" {MONO} font-weight="600">PLOKŠTINĖ</text>
<text x="{c}" y="{c - r2000 - 10:.1f}" fill="{RED}" font-size="24" {MONO} font-weight="600" text-anchor="middle">2000 km</text>
<text x="{c}" y="{c - 1000 * scale - 8:.1f}" fill="{RED}" fill-opacity="0.7" font-size="18" {MONO} text-anchor="middle">1000 km</text>
</svg>"""
    (OUT / "range-map.svg").write_text(svg, encoding="utf-8")


def base_plan() -> None:
    w, h = 1000, 700
    cx, cy = 360, 350
    fences = "".join(
        f'<rect x="{cx - 120 - i * 22}" y="{cy - 120 - i * 22}" width="{240 + i * 44}" height="{240 + i * 44}" rx="{18 + i * 8}" '
        f'fill="none" stroke="{MUTED}" stroke-opacity="{0.35 + i * 0.1:.2f}" stroke-width="2" stroke-dasharray="{"6 6" if i % 2 else "2 6"}"/>'
        for i in range(6))
    shafts = "".join(
        f'<circle cx="{cx + dx}" cy="{cy + dy}" r="26" fill="#0b1310" stroke="{ACCENT}" stroke-width="4"/>'
        f'<circle cx="{cx + dx}" cy="{cy + dy}" r="9" fill="{ACCENT}"/>'
        for dx, dy in [(-80, -80), (80, -80), (-80, 80), (80, 80)])
    town = "".join(f'<rect x="{x}" y="{y}" width="46" height="30" rx="4" fill="{LAND}" stroke="{MUTED}" stroke-width="2"/>'
                   for x, y in [(760, 150), (820, 150), (880, 150), (760, 196), (820, 196), (880, 196)])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Plan of the Plokštinė base (schematic)">
<rect width="{w}" height="{h}" fill="{BG}"/>
{fences}
<text x="{cx}" y="{cy - 270}" fill="{MUTED}" font-size="20" {MONO} text-anchor="middle">6 ×</text>
<rect x="{cx - 34}" y="{cy - 34}" width="68" height="68" rx="8" fill="{RED}" fill-opacity="0.25" stroke="{RED}" stroke-width="3"/>
<line x1="{cx - 80}" y1="{cy - 80}" x2="{cx + 80}" y2="{cy + 80}" stroke="{ACCENT}" stroke-opacity="0.5" stroke-width="2"/>
<line x1="{cx + 80}" y1="{cy - 80}" x2="{cx - 80}" y2="{cy + 80}" stroke="{ACCENT}" stroke-opacity="0.5" stroke-width="2"/>
{shafts}
<rect x="{cx - 34}" y="{cy - 34}" width="68" height="68" rx="8" fill="{RED}" fill-opacity="0.25" stroke="{RED}" stroke-width="3"/>
{town}
<line x1="{cx + 260}" y1="{cy - 110}" x2="750" y2="200" stroke="{MUTED}" stroke-width="2" stroke-dasharray="8 6"/>
<text x="840" y="270" fill="{TEXT}" font-size="26" {MONO} font-weight="600" text-anchor="middle">500 m</text>
<path d="M{cx + 270} {cy + 120} C 640 520, 760 560, 860 560" fill="none" stroke="#7fb3d5" stroke-width="3" stroke-dasharray="10 6"/>
<path d="M820 600 q20 -14 40 0 t40 0 t40 0 M820 625 q20 -14 40 0 t40 0 t40 0" fill="none" stroke="#7fb3d5" stroke-width="3"/>
<text x="700" y="610" fill="#7fb3d5" font-size="26" {MONO} font-weight="600" text-anchor="middle">2,5 km</text>
</svg>"""
    (OUT / "base-plan.svg").write_text(svg, encoding="utf-8")


def shaft_section() -> None:
    w, h = 1000, 1100
    px = 30  # pixels per metre
    ground, x0 = 120, 500
    depth, diameter, missile, warhead = 27 * px, 5 * px, 23 * px, 4 * px
    bottom = ground + depth
    mtop = bottom - missile
    ticks = "".join(
        f'<line x1="{x0 - diameter / 2 - 70}" y1="{ground + m * px}" x2="{x0 - diameter / 2 - 50}" y2="{ground + m * px}" stroke="{MUTED}" stroke-width="2"/>'
        f'<text x="{x0 - diameter / 2 - 80}" y="{ground + m * px + 7}" fill="{MUTED}" font-size="20" {MONO} text-anchor="end">{m} m</text>'
        for m in range(0, 28, 5))
    person = (f'<g transform="translate({x0 + 260} {ground})" stroke="{TEXT}" stroke-width="5" stroke-linecap="round" fill="none">'
              f'<circle cx="0" cy="{-1.8 * px + 8}" r="8" fill="{TEXT}"/><line x1="0" y1="{-1.8 * px + 16}" x2="0" y2="{-0.85 * px}"/>'
              f'<line x1="0" y1="{-0.85 * px}" x2="-10" y2="0"/><line x1="0" y1="{-0.85 * px}" x2="10" y2="0"/>'
              f'<line x1="-14" y1="{-1.35 * px}" x2="14" y2="{-1.35 * px}"/></g>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Cross-section of a missile shaft">
<rect width="{w}" height="{h}" fill="{BG}"/>
<rect x="0" y="{ground}" width="{w}" height="{h - ground}" fill="#16201b"/>
<line x1="0" y1="{ground}" x2="{w}" y2="{ground}" stroke="{MUTED}" stroke-width="3"/>
<rect x="{x0 - diameter / 2 - 18}" y="{ground}" width="{diameter + 36}" height="{depth + 18}" fill="#2a332e"/>
<rect x="{x0 - diameter / 2}" y="{ground}" width="{diameter}" height="{depth}" fill="#0b1310"/>
<path d="M{x0 - diameter / 2 - 40} {ground} Q{x0} {ground - 70} {x0 + diameter / 2 + 40} {ground}Z" fill="#3a4a42" stroke="{MUTED}" stroke-width="3"/>
{ticks}
<path d="M{x0 - 0.83 * px} {bottom} L{x0 - 0.83 * px} {mtop + warhead} L{x0} {mtop} L{x0 + 0.83 * px} {mtop + warhead} L{x0 + 0.83 * px} {bottom}Z" fill="#c9cfc9"/>
<path d="M{x0 - 0.83 * px} {mtop + warhead} L{x0} {mtop} L{x0 + 0.83 * px} {mtop + warhead}Z" fill="{RED}"/>
<line x1="{x0 + diameter / 2 + 40}" y1="{mtop}" x2="{x0 + diameter / 2 + 40}" y2="{bottom}" stroke="{ACCENT}" stroke-width="3"/>
<text x="{x0 + diameter / 2 + 56}" y="{(mtop + bottom) / 2}" fill="{ACCENT}" font-size="32" {MONO} font-weight="600">23 m</text>
<text x="{x0 + diameter / 2 + 56}" y="{mtop + warhead / 2 + 8}" fill="{RED}" font-size="22" {MONO}>4 m</text>
<text x="{x0 + diameter / 2 + 56}" y="{(mtop + bottom) / 2 + 40}" fill="{MUTED}" font-size="22" {MONO}>19 m + 4 m</text>
<line x1="{x0 - diameter / 2}" y1="{bottom + 50}" x2="{x0 + diameter / 2}" y2="{bottom + 50}" stroke="{MUTED}" stroke-width="2"/>
<text x="{x0}" y="{bottom + 84}" fill="{MUTED}" font-size="22" {MONO} text-anchor="middle">≈ 5 m</text>
<text x="{x0 - diameter / 2 - 80}" y="{bottom + 7}" fill="{TEXT}" font-size="26" {MONO} font-weight="600" text-anchor="end">27 m</text>
{person}
<text x="{x0 + 260}" y="{ground - 1.8 * px - 14}" fill="{MUTED}" font-size="20" {MONO} text-anchor="middle">1,8 m</text>
</svg>"""
    (OUT / "shaft-section.svg").write_text(svg, encoding="utf-8")


range_map()
base_plan()
shaft_section()
for f in sorted(OUT.glob("*.svg")):
    print(f.name, f.stat().st_size, "bytes")
