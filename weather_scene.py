import datetime, sys

SVG_FILE = "weather_scene.svg"

def pick_season(override, temp_c, wcode):
    ov = (override or "auto").strip().lower()
    if ov in ("winter", "monsoon", "autumn", "spring"):
        return ov
    if wcode >= 51:
        return "monsoon"
    m = datetime.datetime.utcnow().month
    if m in (12, 1, 2) or (m == 11 and (temp_c is not None and temp_c <= 20.0)):
        return "winter"
    if m in (6, 7, 8, 9):
        return "monsoon"
    if m in (10, 11):
        return "autumn"
    return "spring"

def pixel_janitor_svg(mopping=False):
    p = 3
    rects = []
    def px(x, y, w, h, c):
        rects.append(f'<rect x="{x*p}" y="{y*p}" width="{w*p}" height="{h*p}" fill="{c}"/>')

    # Blue Cap & Outline
    px(5, 0, 7, 1, "#0B0D14")
    px(4, 1, 9, 1, "#0B0D14"); px(5, 1, 7, 1, "#2563EB")
    px(4, 2, 10, 1, "#0B0D14"); px(5, 2, 5, 1, "#3B82F6"); px(10, 2, 3, 1, "#60A5FA")
    px(3, 3, 12, 1, "#0B0D14"); px(4, 3, 10, 1, "#2563EB")
    # Hair & Face
    px(4, 4, 9, 1, "#0B0D14"); px(5, 4, 7, 1, "#291D18")
    px(4, 5, 9, 3, "#0B0D14"); px(5, 5, 7, 3, "#FDBA74")
    px(5, 5, 2, 1, "#291D18")
    px(7, 6, 1, 2, "#0B0D14"); px(10, 6, 1, 2, "#0B0D14")
    px(6, 8, 5, 1, "#0B0D14"); px(7, 8, 3, 1, "#EA9B5A")
    # Blue Overalls & Arms
    px(4, 9, 9, 5, "#0B0D14"); px(5, 9, 7, 5, "#2563EB")
    px(7, 10, 3, 1, "#F1F5F9")
    px(3, 10, 2, 2, "#0B0D14"); px(3, 10, 1, 2, "#FDBA74")
    px(12, 10, 2, 2, "#0B0D14"); px(12, 10, 1, 2, "#FDBA74")
    # Legs & Boots
    px(5, 14, 3, 2, "#0B0D14"); px(5, 14, 2, 2, "#1D4ED8")
    px(9, 14, 3, 2, "#0B0D14"); px(10, 14, 2, 2, "#1D4ED8")
    px(4, 16, 4, 2, "#0B0D14"); px(5, 16, 2, 1, "#3F2E26")
    px(9, 16, 4, 2, "#0B0D14"); px(10, 16, 2, 1, "#3F2E26")
    # Blue Bucket trailing behind
    px(15, 12, 5, 6, "#0B0D14")
    px(16, 13, 3, 4, "#2563EB")
    px(15, 13, 5, 1, "#60A5FA")

    if not mopping:
        px(1, 5, 2, 11, "#0B0D14"); px(1, 5, 1, 11, "#92400E")
        px(-1, 15, 6, 3, "#0B0D14"); px(0, 16, 4, 2, "#E2E8F0")
    else:
        px(2, 9, 2, 2, "#92400E"); px(1, 11, 2, 2, "#92400E")
        px(0, 13, 2, 2, "#92400E"); px(-1, 15, 2, 2, "#92400E")
        px(-4, 16, 6, 2, "#0B0D14"); px(-3, 16, 4, 2, "#E2E8F0")
        px(-6, 17, 2, 1, "#38BDF8"); px(-2, 18, 3, 1, "#7DD3FC")
    return "".join(rects)

def particle_svg(season, idx, x, size):
    if season == "winter":
        if idx % 3 == 0:
            s = size
            return (
                f'<rect x="{x}" y="{-s}" width="{s}" height="{s*3}" fill="#E0F2FE"/>'
                f'<rect x="{x-s}" y="0" width="{s*3}" height="{s}" fill="#BAE6FD"/>'
                f'<rect x="{x}" y="0" width="{s}" height="{s}" fill="#FFFFFF"/>'
            )
        return f'<rect x="{x}" y="0" width="{size}" height="{size}" fill="#E0F2FE"/>'
    elif season == "monsoon":
        return (
            f'<rect x="{x}" y="0" width="3" height="11" fill="#3B82F6"/>'
            f'<rect x="{x}" y="8" width="3" height="5" fill="#93C5FD"/>'
            f'<rect x="{x}" y="11" width="3" height="3" fill="#E0F2FE"/>'
        )
    elif season == "autumn":
        c1 = "#F97316" if idx % 2 == 0 else "#EF4444"
        c2 = "#FACC15" if idx % 2 == 0 else "#F97316"
        return (
            f'<rect x="{x}" y="0" width="6" height="6" fill="{c1}"/>'
            f'<rect x="{x+3}" y="-3" width="4" height="4" fill="{c2}"/>'
            f'<rect x="{x-3}" y="3" width="4" height="4" fill="{c2}"/>'
        )
    else:
        c1 = "#22C55E" if idx % 2 == 0 else "#16A34A"
        return (
            f'<rect x="{x}" y="0" width="7" height="5" fill="{c1}"/>'
            f'<rect x="{x+2}" y="2" width="3" height="2" fill="#86EFAC"/>'
            f'<rect x="{x-2}" y="4" width="3" height="2" fill="#15803D"/>'
        )

def render_scene(season, temp_c):
    W, H = 900, 175
    THEMES = {
        "winter":  ("WINTER SNOWFALL",  "#071324", "#0F2942", "#E0F2FE", "#BAE6FD", "#38BDF8", "SNOW"),
        "monsoon": ("MONSOON RAIN",     "#07121E", "#102A43", "#60A5FA", "#93C5FD", "#3B82F6", "RAIN"),
        "autumn":  ("AUTUMN LEAF-FALL", "#1A0D0A", "#3B170E", "#FB923C", "#FACC15", "#EF4444", "FALL"),
        "spring":  ("SPRING BREEZE",    "#071A12", "#0F3826", "#4ADE80", "#86EFAC", "#22C55E", "LEAF"),
    }
    label, bg1, bg2, pile1, pile2, accent, tag = THEMES[season]
    temp_str = f"{temp_c:.1f}C" if temp_c is not None else "LIVE"

    particles = []
    for i in range(28):
        x = 24 + (i * 31 + (i % 5) * 13) % (W - 48)
        dur = 2.6 + (i % 7) * 0.45 if season != "monsoon" else 1.1 + (i % 5) * 0.22
        delay = -(i * 0.37) % dur
        sz = 4 if i % 2 == 0 else 3
        shape = particle_svg(season, i, x, sz)
        cls = "rain-fall" if season == "monsoon" else "drift-fall"
        particles.append(
            f'<g class="{cls}" style="animation-duration:{dur:.2f}s; animation-delay:{delay:.2f}s;">{shape}</g>'
        )

    mounds, mound_kf = [], []
    for i in range(30):
        mx = i * 30
        mh = 10 + ((i * 7) % 9)
        c_p = 48 + int(((29 - i) / 29.0) * 38)
        mounds.append(
            f'<g style="transform-origin:{mx+15}px {H}px; animation: mound{i} 22s linear infinite;">'
            f'<rect x="{mx}" y="{H-mh}" width="32" height="{mh}" fill="{pile1}"/>'
            f'<rect x="{mx+4}" y="{H-mh-3}" width="20" height="4" fill="{pile2}"/>'
            f'</g>'
        )
        mound_kf.append(
            f"@keyframes mound{i} {{"
            f" 0% {{ transform: scaleY(0.15); opacity: 0.5; }}"
            f" 42% {{ transform: scaleY(1.0); opacity: 1; }}"
            f" {c_p}% {{ transform: scaleY(1.0); opacity: 1; }}"
            f" {min(95, c_p+4)}% {{ transform: scaleY(0.05); opacity: 0.15; }}"
            f" 100% {{ transform: scaleY(0.15); opacity: 0.5; }}"
            f"}}"
        )

    janitor_walk = pixel_janitor_svg(mopping=False)
    janitor_mop = pixel_janitor_svg(mopping=True)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" role="img" aria-label="Live India Weather and Pixel Janitor">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{bg1}"/>
      <stop offset="100%" stop-color="{bg2}"/>
    </linearGradient>
    <clipPath id="clip"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <style>
      .drift-fall {{ animation: driftFall linear infinite; }}
      .rain-fall  {{ animation: rainFall linear infinite; }}
      @keyframes driftFall {{
        0%   {{ transform: translate(0px, -16px); opacity: 0; }}
        10%  {{ opacity: 0.95; }}
        50%  {{ transform: translate(16px, 85px); opacity: 0.95; }}
        92%  {{ opacity: 0.9; }}
        100% {{ transform: translate(-8px, {H+6}px); opacity: 0; }}
      }}
      @keyframes rainFall {{
        0%   {{ transform: translate(0px, -20px); opacity: 0; }}
        15%  {{ opacity: 0.95; }}
        100% {{ transform: translate(-18px, {H+10}px); opacity: 0.2; }}
      }}
      .janitor-track {{ animation: janitorSweep 22s linear infinite; }}
      @keyframes janitorSweep {{
        0%, 40% {{ transform: translate(940px, {H-58}px); }}
        46%     {{ transform: translate(825px, {H-58}px); }}
        88%     {{ transform: translate(-10px, {H-58}px); }}
        95%,100%{{ transform: translate(-90px, {H-58}px); }}
      }}
      .mop-pose  {{ animation: mopStep 0.55s steps(1, end) infinite; }}
      .walk-pose {{ animation: walkStep 0.55s steps(1, end) infinite; }}
      @keyframes mopStep  {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: 0; }} }}
      @keyframes walkStep {{ 0%,49% {{ opacity: 0; }} 50%,100% {{ opacity: 1; }} }}
      {''.join(mound_kf)}
    </style>
  </defs>
  <g clip-path="url(#clip)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <rect x="60" y="28" width="3" height="3" fill="#FFFFFF" fill-opacity="0.45"/>
    <rect x="190" y="18" width="3" height="3" fill="#FFFFFF" fill-opacity="0.35"/>
    <rect x="360" y="34" width="3" height="3" fill="#FFFFFF" fill-opacity="0.5"/>
    <rect x="540" y="22" width="3" height="3" fill="#FFFFFF" fill-opacity="0.4"/>
    <rect x="740" y="30" width="3" height="3" fill="#FFFFFF" fill-opacity="0.5"/>
    <rect x="830" y="18" width="3" height="3" fill="#FFFFFF" fill-opacity="0.35"/>

    <rect x="18" y="16" width="370" height="34" rx="10" fill="#09090B" fill-opacity="0.72" stroke="{accent}" stroke-width="1.5"/>
    <text x="32" y="37" fill="#F8FAFC" font-family="monospace" font-size="13" font-weight="800">[{tag}] INDIA LIVE • {temp_str} • {label}</text>

    <rect x="650" y="16" width="232" height="34" rx="10" fill="#09090B" fill-opacity="0.72" stroke="#334155" stroke-width="1.2"/>
    <text x="766" y="37" text-anchor="middle" fill="{pile2}" font-family="monospace" font-size="11.5" font-weight="700">JANITOR ON DUTY • LOOPING</text>

    {''.join(particles)}
    {''.join(mounds)}
    <g class="janitor-track">
      <g class="mop-pose">{janitor_mop}</g>
      <g class="walk-pose">{janitor_walk}</g>
    </g>
  </g>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="{accent}" stroke-opacity="0.45" stroke-width="1.5"/>
</svg>'''
    with open(SVG_FILE, "w") as f:
        f.write(svg)

if __name__ == "__main__":
    override = sys.argv[1] if len(sys.argv) > 1 else "auto"
    temp_c = float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
    wcode = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else 0
    season = pick_season(override, temp_c, wcode)
    render_scene(season, temp_c)
    print(f"Rendered {SVG_FILE}: season={season}, temp={temp_c}")
