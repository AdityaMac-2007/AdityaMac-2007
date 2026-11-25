import json, math, os, sys

STATE_FILE = "doom_state.json"
SVG_FILE = "doom_frame.svg"

# 9x9 Grand Hellfire Corridor (1=Hellfire Crimson Brick, 2=Cyber-Steel Pillar, 3=Neon Tech Wall)
MAP = [
    [1,1,1,3,3,3,1,1,1],
    [1,0,0,0,0,0,0,0,1],
    [1,0,2,0,0,0,2,0,1],
    [3,0,0,0,0,0,0,0,3],
    [1,0,2,0,0,0,2,0,1],
    [1,0,0,0,0,0,0,0,1],
    [1,2,0,0,0,0,0,2,1],
    [1,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1],
]

def default_state():
    return {
        "x": 4.5, "y": 7.35, "angle": -1.5708,
        "hp": 100, "armor": 100, "ammo": 50, "frags": 0,
        "enemies": [
            {"id": "CACODEMON", "x": 4.5, "y": 4.7, "hp": 60, "max_hp": 60, "kind": "caco"},
            {"id": "CYBER-IMP", "x": 3.1, "y": 2.9, "hp": 40, "max_hp": 40, "kind": "imp"},
            {"id": "HELL-BARON", "x": 5.9, "y": 2.4, "hp": 80, "max_hp": 80, "kind": "baron"},
        ],
        "last_log": "E1M1: LSM-HANGAR LIVE // TARGET LOCKED ON CACODEMON",
        "last_player": "AdityaMac-2007",
        "fired": False,
    }

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return default_state()

def is_wall(x, y):
    mx, my = int(x), int(y)
    if my < 0 or my >= len(MAP) or mx < 0 or mx >= len(MAP[0]):
        return True
    return MAP[my][mx] > 0

def step_game(st, cmd, player):
    cmd = (cmd or "reset").strip().lower()
    st["fired"] = False
    st["last_player"] = player or "visitor"

    if cmd == "reset":
        st = default_state()
        st["last_player"] = player or "AdityaMac-2007"
        st["last_log"] = f"E1M1 RESET BY @{st['last_player']} // TARGET LOCKED"
        return st

    dx, dy = math.cos(st["angle"]), math.sin(st["angle"])
    if cmd == "left":
        st["angle"] -= 0.38
        st["last_log"] = f"@{player} TURNED LEFT"
    elif cmd == "right":
        st["angle"] += 0.38
        st["last_log"] = f"@{player} TURNED RIGHT"
    elif cmd == "forward":
        nx, ny = st["x"] + dx * 0.72, st["y"] + dy * 0.72
        if not is_wall(nx, ny):
            st["x"], st["y"] = nx, ny
            st["last_log"] = f"@{player} ADVANCED DOWN CORRIDOR"
        else:
            st["last_log"] = f"@{player} BLOCKED BY REINFORCED WALL"
    elif cmd == "back":
        nx, ny = st["x"] - dx * 0.72, st["y"] - dy * 0.72
        if not is_wall(nx, ny):
            st["x"], st["y"] = nx, ny
            st["last_log"] = f"@{player} STEPPED BACK"
        else:
            st["last_log"] = f"@{player} WALL BEHIND YOU"
    elif cmd == "fire":
        st["fired"] = True
        if st["ammo"] <= 0:
            st["last_log"] = f"@{player} OUT OF PLASMA! CLICK NEW RUN"
            return st
        st["ammo"] -= 1
        hit, best_dist = None, 999.0
        for e in st["enemies"]:
            if e["hp"] <= 0:
                continue
            ex, ey = e["x"] - st["x"], e["y"] - st["y"]
            dist = math.hypot(ex, ey)
            ea = math.atan2(ey, ex)
            diff = (ea - st["angle"] + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < 0.26 and dist < best_dist:
                best_dist, hit = dist, e
        if hit:
            hit["hp"] -= 40
            if hit["hp"] <= 0:
                st["frags"] += 1
                st["last_log"] = f"@{player} OBLITERATED {hit['id']}! (+1 FRAG)"
            else:
                st["last_log"] = f"@{player} PLASMA HIT {hit['id']} ({hit['hp']} HP LEFT)"
        else:
            st["last_log"] = f"@{player} FIRED BFG PLASMA (NO HIT)"

    if all(e["hp"] <= 0 for e in st["enemies"]):
        st["enemies"] = default_state()["enemies"]
        st["ammo"] = min(99, st["ammo"] + 25)
        st["last_log"] = f"SECTOR CLEARED BY @{player}! NEW WAVE (+25 AMMO)"
    return st

def render_svg(st):
    W, H = 900, 440
    HUD_H = 88
    VH = H - HUD_H
    FOV = math.pi / 2.85
    RAYS = 120
    slice_w = W / RAYS
    px, py, pa = st["x"], st["y"], st["angle"]

    walls_svg = []
    zbuf = [99.0] * RAYS

    for i in range(RAYS):
        ra = pa - FOV / 2 + (i / RAYS) * FOV
        rx, ry = math.cos(ra), math.sin(ra)
        dist = 0.05
        hit_type, side, hit_u = 1, 0, 0.0
        while dist < 13.0:
            tx, ty = px + rx * dist, py + ry * dist
            mx, my = int(tx), int(ty)
            if my < 0 or my >= len(MAP) or mx < 0 or mx >= len(MAP[0]):
                break
            if MAP[my][mx] > 0:
                hit_type = MAP[my][mx]
                fx, fy = tx - mx, ty - my
                if min(fx, 1 - fx) < min(fy, 1 - fy):
                    side = 1
                    hit_u = fy
                else:
                    side = 0
                    hit_u = fx
                break
            dist += 0.032
        perp = max(0.25, dist * math.cos(ra - pa))
        zbuf[i] = perp
        wh = min(VH * 1.18, (VH * 0.96) / perp)
        y0 = (VH - wh) / 2
        shade = max(0.16, 1.0 - perp / 10.2) * (0.74 if side else 1.0)
        seam = 0.72 if (hit_u < 0.06 or hit_u > 0.94) else 1.0
        s = shade * seam

        if hit_type == 1:
            r, g, b = int(205 * s), int(28 * s), int(38 * s)
            trim = f"rgb({int(255*shade)},{int(140*shade)},{int(25*shade)})"
        elif hit_type == 2:
            r, g, b = int(58 * s), int(72 * s), int(96 * s)
            trim = f"rgb({int(57*shade)},{int(255*shade)},{int(20*shade)})"
        else:
            r, g, b = int(95 * s), int(35 * s), int(145 * s)
            trim = f"rgb({int(255*shade)},{int(42*shade)},{int(90*shade)})"

        x0 = i * slice_w
        walls_svg.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{slice_w+0.7:.1f}" height="{wh:.1f}" fill="rgb({r},{g},{b})"/>')
        # Glowing architectural tech-trim stripe along upper & lower wall
        walls_svg.append(f'<rect x="{x0:.1f}" y="{y0+wh*0.14:.1f}" width="{slice_w+0.7:.1f}" height="{max(1.5, wh*0.035):.1f}" fill="{trim}" fill-opacity="0.72"/>')
        walls_svg.append(f'<rect x="{x0:.1f}" y="{y0+wh*0.84:.1f}" width="{slice_w+0.7:.1f}" height="{max(1.5, wh*0.03):.1f}" fill="{trim}" fill-opacity="0.5"/>')

    # Project 3D Enemies (far to near with Z-buffer occlusion)
    sprites = []
    for e in st["enemies"]:
        if e["hp"] <= 0:
            continue
        ex, ey = e["x"] - px, e["y"] - py
        dist = math.hypot(ex, ey)
        ea = math.atan2(ey, ex)
        diff = (ea - pa + math.pi) % (2 * math.pi) - math.pi
        if abs(diff) < FOV * 0.72 and dist > 0.35:
            sprites.append((dist, diff, e))
    sprites.sort(key=lambda t: -t[0])

    enemies_svg = []
    for dist, diff, e in sprites:
        sx = (0.5 + diff / FOV) * W
        ray_idx = max(0, min(RAYS - 1, int(sx / slice_w)))
        if dist >= zbuf[ray_idx]:
            continue
        sz = min(190, 175 / dist)
        sy = VH * 0.51
        hp_pct = max(0.0, e["hp"] / max(1, e.get("max_hp", 60)))
        bar_w = max(44, sz * 0.85)
        body_col = "#DC2626" if e.get("kind") == "caco" else ("#9333EA" if e.get("kind") == "baron" else "#EA580C")
        eye_col = "#39FF14" if e.get("kind") == "caco" else "#FF9F1C"
        enemies_svg.append(f'''
        <g class="demon-bob" transform="translate({sx:.1f},{sy:.1f})">
          <ellipse cx="0" cy="{sz*0.64:.1f}" rx="{sz*0.42:.1f}" ry="{sz*0.11:.1f}" fill="#000" fill-opacity="0.55"/>
          <circle cx="0" cy="0" r="{sz*0.52:.1f}" fill="{body_col}" fill-opacity="0.22"/>
          <circle cx="0" cy="0" r="{sz*0.44:.1f}" fill="{body_col}" stroke="#FF9F1C" stroke-width="2.4"/>
          <polygon points="{-sz*0.38:.1f},{-sz*0.20:.1f} {-sz*0.26:.1f},{-sz*0.56:.1f} {-sz*0.10:.1f},{-sz*0.36:.1f}" fill="#FEF3C7"/>
          <polygon points="{sz*0.38:.1f},{-sz*0.20:.1f} {sz*0.26:.1f},{-sz*0.56:.1f} {sz*0.10:.1f},{-sz*0.36:.1f}" fill="#FEF3C7"/>
          <polygon points="0,{-sz*0.42:.1f} {-sz*0.09:.1f},{-sz*0.58:.1f} {sz*0.09:.1f},{-sz*0.58:.1f}" fill="#FF9F1C"/>
          <ellipse cx="0" cy="{-sz*0.06:.1f}" rx="{sz*0.22:.1f}" ry="{sz*0.13:.1f}" fill="{eye_col}"/>
          <circle cx="0" cy="{-sz*0.06:.1f}" r="{sz*0.065:.1f}" fill="#09090B"/>
          <path d="M{-sz*0.24:.1f},{sz*0.16:.1f} Q0,{sz*0.38:.1f} {sz*0.24:.1f},{sz*0.16:.1f} Z" fill="#09090B"/>
          <polygon points="{-sz*0.16:.1f},{sz*0.18:.1f} {-sz*0.11:.1f},{sz*0.26:.1f} {-sz*0.06:.1f},{sz*0.18:.1f}" fill="#FEF3C7"/>
          <polygon points="{sz*0.16:.1f},{sz*0.18:.1f} {sz*0.11:.1f},{sz*0.26:.1f} {sz*0.06:.1f},{sz*0.18:.1f}" fill="#FEF3C7"/>
          <rect x="{-bar_w/2:.1f}" y="{-sz*0.66:.1f}" width="{bar_w:.1f}" height="5" rx="2.5" fill="#09090B" stroke="#334155" stroke-width="0.8"/>
          <rect x="{-bar_w/2:.1f}" y="{-sz*0.66:.1f}" width="{bar_w*hp_pct:.1f}" height="5" rx="2.5" fill="#FF2A2A"/>
          <text x="0" y="{-sz*0.72:.1f}" text-anchor="middle" fill="#FEF08A" font-family="monospace" font-size="11" font-weight="800">{e["id"]}</text>
        </g>''')

    # 2D Tactical Minimap (top right)
    mm_cell = 11
    mm_x0, mm_y0 = W - len(MAP[0]) * mm_cell - 16, 14
    mm_svg = [f'<rect x="{mm_x0-7}" y="{mm_y0-7}" width="{len(MAP[0])*mm_cell+14}" height="{len(MAP)*mm_cell+14}" rx="10" fill="#09090B" fill-opacity="0.86" stroke="#39FF14" stroke-opacity="0.65" stroke-width="1.3"/>']
    for r_i, row in enumerate(MAP):
        for c_i, cell in enumerate(row):
            if cell > 0:
                fc = "#FF2A2A" if cell == 1 else ("#64748B" if cell == 2 else "#A855F7")
                mm_svg.append(f'<rect x="{mm_x0+c_i*mm_cell}" y="{mm_y0+r_i*mm_cell}" width="{mm_cell-1}" height="{mm_cell-1}" rx="1.5" fill="{fc}" fill-opacity="0.9"/>')
    for e in st["enemies"]:
        if e["hp"] > 0:
            mm_svg.append(f'<circle cx="{mm_x0+e["x"]*mm_cell:.1f}" cy="{mm_y0+e["y"]*mm_cell:.1f}" r="3.2" fill="#FF9F1C"/>')
    p_mx, p_my = mm_x0 + px * mm_cell, mm_y0 + py * mm_cell
    mm_svg.append(f'<line x1="{p_mx:.1f}" y1="{p_my:.1f}" x2="{p_mx+math.cos(pa)*13:.1f}" y2="{p_my+math.sin(pa)*13:.1f}" stroke="#39FF14" stroke-width="2.2"/>')
    mm_svg.append(f'<circle cx="{p_mx:.1f}" cy="{p_my:.1f}" r="3.6" fill="#39FF14"/>')

    flash_svg = ""
    if st.get("fired"):
        flash_svg = f'''
        <g>
          <circle cx="{W/2}" cy="{VH-124}" r="58" fill="#39FF14" fill-opacity="0.32"/>
          <circle cx="{W/2}" cy="{VH-124}" r="32" fill="#FF9F1C" fill-opacity="0.72"/>
          <circle cx="{W/2}" cy="{VH-124}" r="16" fill="#FFFBEB"/>
          <line x1="{W/2}" y1="{VH-124}" x2="{W/2}" y2="{VH*0.5}" stroke="#39FF14" stroke-width="6" stroke-opacity="0.9"/>
          <line x1="{W/2}" y1="{VH-124}" x2="{W/2}" y2="{VH*0.5}" stroke="#FFFFFF" stroke-width="2"/>
        </g>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Playable DOOM 3D Raycaster on GitHub">
  <defs>
    <linearGradient id="ceilGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#050508"/>
      <stop offset="70%" stop-color="#1C090F"/>
      <stop offset="100%" stop-color="#2D0C14"/>
    </linearGradient>
    <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#221015"/>
      <stop offset="45%" stop-color="#15151C"/>
      <stop offset="100%" stop-color="#08080B"/>
    </linearGradient>
    <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="#000000" fill-opacity="0.22"/>
    </pattern>
    <style>
      .gun-bob {{ animation: bob 2.1s ease-in-out infinite; }}
      .demon-bob {{ animation: float 2.4s ease-in-out infinite; }}
      .core-pulse {{ animation: glow 1.2s ease-in-out infinite; }}
      @keyframes bob {{ 0%,100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(5px); }} }}
      @keyframes float {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.90; }} }}
      @keyframes glow {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.45; }} }}
    </style>
  </defs>

  <rect width="{W}" height="{H}" rx="20" fill="#09090B"/>
  <rect x="0" y="0" width="{W}" height="{VH/2}" fill="url(#ceilGrad)"/>
  <rect x="0" y="{VH/2}" width="{W}" height="{VH/2}" fill="url(#floorGrad)"/>

  <!-- 3D Raycasted Hellfire & Cyber-Steel Corridor -->
  {''.join(walls_svg)}
  <!-- 3D Z-Buffered Demons -->
  {''.join(enemies_svg)}

  <!-- Target Lock Reticle -->
  <g stroke="#39FF14" stroke-opacity="0.85" stroke-width="1.6" fill="none">
    <circle cx="{W/2}" cy="{VH/2}" r="16" stroke-dasharray="6 4"/>
    <line x1="{W/2-22}" y1="{VH/2}" x2="{W/2-7}" y2="{VH/2}"/>
    <line x1="{W/2+7}" y1="{VH/2}" x2="{W/2+22}" y2="{VH/2}"/>
    <line x1="{W/2}" y1="{VH/2-22}" x2="{W/2}" y2="{VH/2-7}"/>
    <line x1="{W/2}" y1="{VH/2+7}" x2="{W/2}" y2="{VH/2+22}"/>
  </g>

  {flash_svg}

  <!-- Heavy BFG-9000 / Plasma Cannon -->
  <g class="gun-bob">
    <polygon points="{W/2-82},{VH} {W/2-46},{VH-78} {W/2+46},{VH-78} {W/2+82},{VH}" fill="#1E293B" stroke="#475569" stroke-width="2"/>
    <polygon points="{W/2-54},{VH} {W/2-34},{VH-106} {W/2+34},{VH-106} {W/2+54},{VH}" fill="#334155" stroke="#94A3B8" stroke-width="1.8"/>
    <rect x="{W/2-22}" y="{VH-128}" width="44" height="32" rx="6" fill="#0F172A" stroke="#64748B" stroke-width="1.8"/>
    <rect class="core-pulse" x="{W/2-14}" y="{VH-120}" width="28" height="16" rx="4" fill="#39FF14"/>
    <rect class="core-pulse" x="{W/2-42}" y="{VH-66}" width="18" height="36" rx="4" fill="#FF9F1C"/>
    <rect class="core-pulse" x="{W/2+24}" y="{VH-66}" width="18" height="36" rx="4" fill="#FF9F1C"/>
    <rect x="{W/2-20}" y="{VH-56}" width="40" height="16" rx="4" fill="#09090B" stroke="#FF2A2A" stroke-width="1.6"/>
  </g>

  <!-- Subtle CRT Scanlines over 3D Viewport -->
  <rect x="0" y="0" width="{W}" height="{VH}" fill="url(#scanlines)"/>

  <!-- Tactical Minimap -->
  {''.join(mm_svg)}

  <!-- Top-left Sector Badge -->
  <rect x="14" y="14" width="256" height="30" rx="8" fill="#09090B" fill-opacity="0.86" stroke="#FF2A2A" stroke-width="1.4"/>
  <circle class="core-pulse" cx="30" cy="29" r="4.5" fill="#FF2A2A"/>
  <text x="42" y="33" fill="#FEF08A" font-family="monospace" font-size="12" font-weight="800">E1M1 // ADITYA'S LSM-HANGAR</text>

  <!-- Classic DOOM Metallic Status HUD -->
  <rect x="0" y="{VH}" width="{W}" height="{HUD_H}" fill="#18181B"/>
  <line x1="0" y1="{VH}" x2="{W}" y2="{VH}" stroke="#FF2A2A" stroke-width="3"/>

  <g font-family="monospace" text-anchor="middle">
    <text x="74"  y="{VH+25}" fill="#94A3B8" font-size="11" font-weight="700">AMMO</text>
    <text x="74"  y="{VH+60}" fill="#FF9F1C" font-size="32" font-weight="900">{st["ammo"]}</text>

    <text x="195" y="{VH+25}" fill="#94A3B8" font-size="11" font-weight="700">HEALTH</text>
    <text x="195" y="{VH+60}" fill="#39FF14" font-size="32" font-weight="900">{st["hp"]}%</text>

    <!-- Classic DOOM Marine Visor Portrait -->
    <rect x="275" y="{VH+12}" width="64" height="64" rx="10" fill="#09090B" stroke="#FF2A2A" stroke-width="1.6"/>
    <rect x="287" y="{VH+24}" width="40" height="38" rx="8" fill="#FDBA74"/>
    <rect x="285" y="{VH+20}" width="44" height="12" rx="4" fill="#334155"/>
    <rect x="292" y="{VH+36}" width="10" height="5" rx="1" fill="#09090B"/>
    <rect x="312" y="{VH+36}" width="10" height="5" rx="1" fill="#09090B"/>
    <rect x="298" y="{VH+50}" width="18" height="4" rx="1" fill="#7F1D1D"/>

    <text x="415" y="{VH+25}" fill="#94A3B8" font-size="11" font-weight="700">ARMOR</text>
    <text x="415" y="{VH+60}" fill="#38BDF8" font-size="32" font-weight="900">{st["armor"]}%</text>

    <text x="520" y="{VH+25}" fill="#94A3B8" font-size="11" font-weight="700">FRAGS</text>
    <text x="520" y="{VH+60}" fill="#FF2A2A" font-size="32" font-weight="900">{st["frags"]}</text>
  </g>

  <rect x="578" y="{VH+12}" width="308" height="64" rx="10" fill="#09090B" stroke="#27272A" stroke-width="1.4"/>
  <text x="592" y="{VH+34}" fill="#39FF14" font-family="monospace" font-size="11.5" font-weight="800">PILOT: @{st["last_player"]}</text>
  <text x="592" y="{VH+56}" fill="#F8FAFC" font-family="monospace" font-size="10.5">{st["last_log"][:44]}</text>
</svg>'''
    with open(SVG_FILE, "w") as f:
        f.write(svg)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "reset"
    player = sys.argv[2] if len(sys.argv) > 2 else "AdityaMac-2007"
    state = load_state()
    state = step_game(state, cmd, player)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    render_svg(state)
    print("Rendered DOOM frame:", state["last_log"])
