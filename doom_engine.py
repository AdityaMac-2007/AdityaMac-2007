import json, math, os, sys

STATE_FILE = "doom_state.json"
SVG_FILE = "doom_frame.svg"

MAP = [
    [1,1,1,1,1,1,1,1,1],
    [1,0,0,0,2,0,0,0,1],
    [1,0,2,0,0,0,2,0,1],
    [1,0,0,0,0,0,0,0,1],
    [1,2,0,0,2,0,0,2,1],
    [1,0,0,0,0,0,0,0,1],
    [1,0,2,0,0,0,2,0,1],
    [1,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1],
]

def default_state():
    return {
        "x": 1.5, "y": 7.5, "angle": -0.78,
        "hp": 100, "armor": 100, "ammo": 50, "frags": 0,
        "enemies": [
            {"id": "CACODEMON-01", "x": 4.5, "y": 5.5, "hp": 60},
            {"id": "CYBER-IMP-02", "x": 6.5, "y": 3.5, "hp": 40},
            {"id": "BARON-03",     "x": 2.5, "y": 2.5, "hp": 80},
        ],
        "last_log": "E1M1: LSM-HANGAR INITIALIZED // CLICK CONTROLS TO PLAY",
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
        st["last_log"] = f"NEW RUN STARTED BY @{st['last_player']} // RIP & TEAR"
        return st

    dx, dy = math.cos(st["angle"]), math.sin(st["angle"])
    if cmd == "left":
        st["angle"] -= 0.45
        st["last_log"] = f"@{player} TURNED LEFT"
    elif cmd == "right":
        st["angle"] += 0.45
        st["last_log"] = f"@{player} TURNED RIGHT"
    elif cmd == "forward":
        nx, ny = st["x"] + dx * 0.75, st["y"] + dy * 0.75
        if not is_wall(nx, ny):
            st["x"], st["y"] = nx, ny
            st["last_log"] = f"@{player} MOVED FORWARD"
        else:
            st["last_log"] = f"@{player} BLOCKED BY STEEL WALL"
    elif cmd == "back":
        nx, ny = st["x"] - dx * 0.75, st["y"] - dy * 0.75
        if not is_wall(nx, ny):
            st["x"], st["y"] = nx, ny
            st["last_log"] = f"@{player} STEPPED BACK"
        else:
            st["last_log"] = f"@{player} WALL BEHIND YOU"
    elif cmd == "fire":
        st["fired"] = True
        if st["ammo"] <= 0:
            st["last_log"] = f"@{player} OUT OF PLASMA! CLICK RESET"
            return st
        st["ammo"] -= 1
        hit = None
        best_dist = 999.0
        for e in st["enemies"]:
            if e["hp"] <= 0:
                continue
            ex, ey = e["x"] - st["x"], e["y"] - st["y"]
            dist = math.hypot(ex, ey)
            ea = math.atan2(ey, ex)
            diff = (ea - st["angle"] + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < 0.28 and dist < best_dist:
                best_dist = dist
                hit = e
        if hit:
            hit["hp"] -= 40
            if hit["hp"] <= 0:
                st["frags"] += 1
                st["last_log"] = f"@{player} FRAGGED {hit['id']}! (+1 FRAG)"
            else:
                st["last_log"] = f"@{player} HIT {hit['id']} (-40 HP, {hit['hp']} LEFT)"
        else:
            st["last_log"] = f"@{player} FIRED PLASMA RIFLE (MISS)"
    else:
        st["last_log"] = f"READY // COMMANDS: FORWARD, LEFT, RIGHT, FIRE, RESET"

    # Respawn wave if all cleared
    if all(e["hp"] <= 0 for e in st["enemies"]):
        st["enemies"] = default_state()["enemies"]
        st["ammo"] = min(99, st["ammo"] + 25)
        st["last_log"] = f"SECTOR CLEARED BY @{player}! WAVE RESPAWNED (+25 AMMO)"
    return st

def render_svg(st):
    W, H = 900, 420
    HUD_H = 82
    VH = H - HUD_H
    FOV = math.pi / 3.0
    RAYS = 90
    slice_w = W / RAYS
    px, py, pa = st["x"], st["y"], st["angle"]

    walls_svg = []
    zbuf = [99.0] * RAYS

    for i in range(RAYS):
        ra = pa - FOV / 2 + (i / RAYS) * FOV
        rx, ry = math.cos(ra), math.sin(ra)
        dist = 0.05
        hit_type = 1
        side = 0
        while dist < 12.0:
            tx, ty = px + rx * dist, py + ry * dist
            mx, my = int(tx), int(ty)
            if my < 0 or my >= len(MAP) or mx < 0 or mx >= len(MAP[0]):
                break
            if MAP[my][mx] > 0:
                hit_type = MAP[my][mx]
                fx, fy = tx - mx, ty - my
                side = 1 if min(fx, 1 - fx) < min(fy, 1 - fy) else 0
                break
            dist += 0.04
        perp = max(0.25, dist * math.cos(ra - pa))
        zbuf[i] = perp
        wh = min(VH * 1.15, (VH * 0.92) / perp)
        y0 = (VH - wh) / 2
        shade = max(0.18, 1.0 - perp / 9.5) * (0.78 if side else 1.0)
        if hit_type == 1:
            r = int(215 * shade); g = int(34 * shade); b = int(42 * shade)
        else:
            r = int(70 * shade); g = int(85 * shade); b = int(115 * shade)
        color = f"rgb({r},{g},{b})"
        walls_svg.append(f'<rect x="{i*slice_w:.1f}" y="{y0:.1f}" width="{slice_w+0.8:.1f}" height="{wh:.1f}" fill="{color}"/>')

    # Project 3D Enemies (far to near)
    sprites = []
    for e in st["enemies"]:
        if e["hp"] <= 0:
            continue
        ex, ey = e["x"] - px, e["y"] - py
        dist = math.hypot(ex, ey)
        ea = math.atan2(ey, ex)
        diff = (ea - pa + math.pi) % (2 * math.pi) - math.pi
        if abs(diff) < FOV * 0.75 and dist > 0.4:
            sprites.append((dist, diff, e))
    sprites.sort(key=lambda t: -t[0])

    enemies_svg = []
    for dist, diff, e in sprites:
        sx = (0.5 + diff / FOV) * W
        ray_idx = max(0, min(RAYS - 1, int(sx / slice_w)))
        if dist >= zbuf[ray_idx]:
            continue
        sz = min(170, 155 / dist)
        sy = VH * 0.52
        enemies_svg.append(f'''
        <g class="demon-bob" transform="translate({sx:.1f},{sy:.1f})">
          <ellipse cx="0" cy="{sz*0.58:.1f}" rx="{sz*0.36:.1f}" ry="{sz*0.1:.1f}" fill="#000" fill-opacity="0.45"/>
          <circle cx="0" cy="0" r="{sz*0.44:.1f}" fill="#DC2626" stroke="#FF9F1C" stroke-width="2.2"/>
          <polygon points="{-sz*0.38:.1f},{-sz*0.22:.1f} {-sz*0.24:.1f},{-sz*0.54:.1f} {-sz*0.12:.1f},{-sz*0.34:.1f}" fill="#FDE68A"/>
          <polygon points="{sz*0.38:.1f},{-sz*0.22:.1f} {sz*0.24:.1f},{-sz*0.54:.1f} {sz*0.12:.1f},{-sz*0.34:.1f}" fill="#FDE68A"/>
          <ellipse cx="0" cy="{-sz*0.05:.1f}" rx="{sz*0.2:.1f}" ry="{sz*0.12:.1f}" fill="#39FF14"/>
          <circle cx="0" cy="{-sz*0.05:.1f}" r="{sz*0.06:.1f}" fill="#09090B"/>
          <path d="M{-sz*0.22:.1f},{sz*0.16:.1f} Q0,{sz*0.34:.1f} {sz*0.22:.1f},{sz*0.16:.1f} Z" fill="#09090B"/>
          <text x="0" y="{-sz*0.56:.1f}" text-anchor="middle" fill="#FF9F1C" font-family="monospace" font-size="11" font-weight="700">{e["id"]} [{e["hp"]}HP]</text>
        </g>''')

    # 2D Tactical Minimap (top right)
    mm_cell = 11
    mm_x0, mm_y0 = W - len(MAP[0]) * mm_cell - 16, 14
    mm_svg = [f'<rect x="{mm_x0-6}" y="{mm_y0-6}" width="{len(MAP[0])*mm_cell+12}" height="{len(MAP)*mm_cell+12}" rx="8" fill="#09090B" fill-opacity="0.82" stroke="#39FF14" stroke-opacity="0.55" stroke-width="1.2"/>']
    for r_i, row in enumerate(MAP):
        for c_i, cell in enumerate(row):
            if cell > 0:
                fc = "#FF2A2A" if cell == 1 else "#475569"
                mm_svg.append(f'<rect x="{mm_x0+c_i*mm_cell}" y="{mm_y0+r_i*mm_cell}" width="{mm_cell-1}" height="{mm_cell-1}" fill="{fc}" fill-opacity="0.85"/>')
    for e in st["enemies"]:
        if e["hp"] > 0:
            mm_svg.append(f'<circle cx="{mm_x0+e["x"]*mm_cell:.1f}" cy="{mm_y0+e["y"]*mm_cell:.1f}" r="3" fill="#FF9F1C"/>')
    p_mx, p_my = mm_x0 + px * mm_cell, mm_y0 + py * mm_cell
    mm_svg.append(f'<line x1="{p_mx:.1f}" y1="{p_my:.1f}" x2="{p_mx+math.cos(pa)*11:.1f}" y2="{p_my+math.sin(pa)*11:.1f}" stroke="#39FF14" stroke-width="2"/>')
    mm_svg.append(f'<circle cx="{p_mx:.1f}" cy="{p_my:.1f}" r="3.4" fill="#39FF14"/>')

    flash_svg = ""
    if st.get("fired"):
        flash_svg = f'''
        <g class="flash">
          <circle cx="{W/2}" cy="{VH-112}" r="44" fill="#FF9F1C" fill-opacity="0.55"/>
          <circle cx="{W/2}" cy="{VH-112}" r="22" fill="#FFFBEB"/>
          <line x1="{W/2}" y1="{VH-112}" x2="{W/2}" y2="{VH*0.5}" stroke="#39FF14" stroke-width="4" stroke-opacity="0.85"/>
        </g>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Playable DOOM 3D Raycaster on GitHub">
  <defs>
    <linearGradient id="ceilGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#050507"/>
      <stop offset="100%" stop-color="#1A0B0E"/>
    </linearGradient>
    <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#17171D"/>
      <stop offset="100%" stop-color="#09090B"/>
    </linearGradient>
    <style>
      .gun-bob {{ animation: bob 2.2s ease-in-out infinite; }}
      .demon-bob {{ animation: float 2.6s ease-in-out infinite; }}
      .core-pulse {{ animation: glow 1.4s ease-in-out infinite; }}
      @keyframes bob {{ 0%,100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(5px); }} }}
      @keyframes float {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.92; }} }}
      @keyframes glow {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.45; }} }}
    </style>
  </defs>

  <rect width="{W}" height="{H}" rx="18" fill="#09090B"/>
  <rect x="0" y="0" width="{W}" height="{VH/2}" fill="url(#ceilGrad)"/>
  <rect x="0" y="{VH/2}" width="{W}" height="{VH/2}" fill="url(#floorGrad)"/>

  <!-- 3D Raycasted Walls -->
  {''.join(walls_svg)}
  <!-- 3D Z-Buffered Demons -->
  {''.join(enemies_svg)}

  <!-- Center Crosshair -->
  <g stroke="#39FF14" stroke-opacity="0.78" stroke-width="1.5">
    <line x1="{W/2-12}" y1="{VH/2}" x2="{W/2-4}" y2="{VH/2}"/>
    <line x1="{W/2+4}" y1="{VH/2}" x2="{W/2+12}" y2="{VH/2}"/>
    <line x1="{W/2}" y1="{VH/2-12}" x2="{W/2}" y2="{VH/2-4}"/>
    <line x1="{W/2}" y1="{VH/2+4}" x2="{W/2}" y2="{VH/2+12}"/>
  </g>

  {flash_svg}

  <!-- First-Person DOOM Plasma Rifle -->
  <g class="gun-bob">
    <polygon points="{W/2-52},{VH} {W/2-28},{VH-92} {W/2+28},{VH-92} {W/2+52},{VH}" fill="#1E293B" stroke="#475569" stroke-width="2"/>
    <rect x="{W/2-18}" y="{VH-114}" width="36" height="32" rx="4" fill="#334155" stroke="#94A3B8" stroke-width="1.5"/>
    <rect class="core-pulse" x="{W/2-10}" y="{VH-106}" width="20" height="14" rx="3" fill="#39FF14"/>
    <rect x="{W/2-34}" y="{VH-54}" width="68" height="12" rx="3" fill="#0F172A" stroke="#FF2A2A" stroke-width="1.5"/>
  </g>

  <!-- Tactical Minimap -->
  {''.join(mm_svg)}

  <!-- Top-left Sector Badge -->
  <rect x="14" y="14" width="232" height="28" rx="6" fill="#09090B" fill-opacity="0.82" stroke="#FF2A2A" stroke-width="1.2"/>
  <text x="26" y="32" fill="#FF2A2A" font-family="monospace" font-size="12" font-weight="800">E1M1 // ADITYA'S LSM-HANGAR</text>

  <!-- Classic DOOM Bottom Status HUD -->
  <rect x="0" y="{VH}" width="{W}" height="{HUD_H}" fill="#18181B"/>
  <line x1="0" y1="{VH}" x2="{W}" y2="{VH}" stroke="#FF2A2A" stroke-width="2.5"/>

  <g font-family="monospace" text-anchor="middle">
    <text x="90"  y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">PLASMA AMMO</text>
    <text x="90"  y="{VH+56}" fill="#FF9F1C" font-size="30" font-weight="900">{st["ammo"]}</text>

    <text x="235" y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">HEALTH</text>
    <text x="235" y="{VH+56}" fill="#39FF14" font-size="30" font-weight="900">{st["hp"]}%</text>

    <text x="380" y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">ARMOR</text>
    <text x="380" y="{VH+56}" fill="#38BDF8" font-size="30" font-weight="900">{st["armor"]}%</text>

    <text x="515" y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">FRAGS</text>
    <text x="515" y="{VH+56}" fill="#FF2A2A" font-size="30" font-weight="900">{st["frags"]}</text>
  </g>

  <rect x="585" y="{VH+12}" width="300" height="58" rx="8" fill="#09090B" stroke="#27272A" stroke-width="1.2"/>
  <text x="598" y="{VH+32}" fill="#39FF14" font-family="monospace" font-size="11" font-weight="700">LAST PILOT: @{st["last_player"]}</text>
  <text x="598" y="{VH+54}" fill="#F8FAFC" font-family="monospace" font-size="10.5">{st["last_log"][:42]}</text>
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
import json, math, os, sys

STATE_FILE = "doom_state.json"
SVG_FILE = "doom_frame.svg"

MAP = [
    [1,1,1,1,1,1,1,1,1],
    [1,0,0,0,2,0,0,0,1],
    [1,0,2,0,0,0,2,0,1],
    [1,0,0,0,0,0,0,0,1],
    [1,2,0,0,2,0,0,2,1],
    [1,0,0,0,0,0,0,0,1],
    [1,0,2,0,0,0,2,0,1],
    [1,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1],
]

def default_state():
    return {
        "x": 1.5, "y": 7.5, "angle": -0.78,
        "hp": 100, "armor": 100, "ammo": 50, "frags": 0,
        "enemies": [
            {"id": "CACODEMON-01", "x": 4.5, "y": 5.5, "hp": 60},
            {"id": "CYBER-IMP-02", "x": 6.5, "y": 3.5, "hp": 40},
            {"id": "BARON-03",     "x": 2.5, "y": 2.5, "hp": 80},
        ],
        "last_log": "E1M1: LSM-HANGAR INITIALIZED // CLICK CONTROLS TO PLAY",
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
        st["last_log"] = f"NEW RUN STARTED BY @{st['last_player']} // RIP & TEAR"
        return st

    dx, dy = math.cos(st["angle"]), math.sin(st["angle"])
    if cmd == "left":
        st["angle"] -= 0.45
        st["last_log"] = f"@{player} TURNED LEFT"
    elif cmd == "right":
        st["angle"] += 0.45
        st["last_log"] = f"@{player} TURNED RIGHT"
    elif cmd == "forward":
        nx, ny = st["x"] + dx * 0.75, st["y"] + dy * 0.75
        if not is_wall(nx, ny):
            st["x"], st["y"] = nx, ny
            st["last_log"] = f"@{player} MOVED FORWARD"
        else:
            st["last_log"] = f"@{player} BLOCKED BY STEEL WALL"
    elif cmd == "back":
        nx, ny = st["x"] - dx * 0.75, st["y"] - dy * 0.75
        if not is_wall(nx, ny):
            st["x"], st["y"] = nx, ny
            st["last_log"] = f"@{player} STEPPED BACK"
        else:
            st["last_log"] = f"@{player} WALL BEHIND YOU"
    elif cmd == "fire":
        st["fired"] = True
        if st["ammo"] <= 0:
            st["last_log"] = f"@{player} OUT OF PLASMA! CLICK RESET"
            return st
        st["ammo"] -= 1
        hit = None
        best_dist = 999.0
        for e in st["enemies"]:
            if e["hp"] <= 0:
                continue
            ex, ey = e["x"] - st["x"], e["y"] - st["y"]
            dist = math.hypot(ex, ey)
            ea = math.atan2(ey, ex)
            diff = (ea - st["angle"] + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < 0.28 and dist < best_dist:
                best_dist = dist
                hit = e
        if hit:
            hit["hp"] -= 40
            if hit["hp"] <= 0:
                st["frags"] += 1
                st["last_log"] = f"@{player} FRAGGED {hit['id']}! (+1 FRAG)"
            else:
                st["last_log"] = f"@{player} HIT {hit['id']} (-40 HP, {hit['hp']} LEFT)"
        else:
            st["last_log"] = f"@{player} FIRED PLASMA RIFLE (MISS)"
    else:
        st["last_log"] = f"READY // COMMANDS: FORWARD, LEFT, RIGHT, FIRE, RESET"

    # Respawn wave if all cleared
    if all(e["hp"] <= 0 for e in st["enemies"]):
        st["enemies"] = default_state()["enemies"]
        st["ammo"] = min(99, st["ammo"] + 25)
        st["last_log"] = f"SECTOR CLEARED BY @{player}! WAVE RESPAWNED (+25 AMMO)"
    return st

def render_svg(st):
    W, H = 900, 420
    HUD_H = 82
    VH = H - HUD_H
    FOV = math.pi / 3.0
    RAYS = 90
    slice_w = W / RAYS
    px, py, pa = st["x"], st["y"], st["angle"]

    walls_svg = []
    zbuf = [99.0] * RAYS

    for i in range(RAYS):
        ra = pa - FOV / 2 + (i / RAYS) * FOV
        rx, ry = math.cos(ra), math.sin(ra)
        dist = 0.05
        hit_type = 1
        side = 0
        while dist < 12.0:
            tx, ty = px + rx * dist, py + ry * dist
            mx, my = int(tx), int(ty)
            if my < 0 or my >= len(MAP) or mx < 0 or mx >= len(MAP[0]):
                break
            if MAP[my][mx] > 0:
                hit_type = MAP[my][mx]
                fx, fy = tx - mx, ty - my
                side = 1 if min(fx, 1 - fx) < min(fy, 1 - fy) else 0
                break
            dist += 0.04
        perp = max(0.25, dist * math.cos(ra - pa))
        zbuf[i] = perp
        wh = min(VH * 1.15, (VH * 0.92) / perp)
        y0 = (VH - wh) / 2
        shade = max(0.18, 1.0 - perp / 9.5) * (0.78 if side else 1.0)
        if hit_type == 1:
            r = int(215 * shade); g = int(34 * shade); b = int(42 * shade)
        else:
            r = int(70 * shade); g = int(85 * shade); b = int(115 * shade)
        color = f"rgb({r},{g},{b})"
        walls_svg.append(f'<rect x="{i*slice_w:.1f}" y="{y0:.1f}" width="{slice_w+0.8:.1f}" height="{wh:.1f}" fill="{color}"/>')

    # Project 3D Enemies (far to near)
    sprites = []
    for e in st["enemies"]:
        if e["hp"] <= 0:
            continue
        ex, ey = e["x"] - px, e["y"] - py
        dist = math.hypot(ex, ey)
        ea = math.atan2(ey, ex)
        diff = (ea - pa + math.pi) % (2 * math.pi) - math.pi
        if abs(diff) < FOV * 0.75 and dist > 0.4:
            sprites.append((dist, diff, e))
    sprites.sort(key=lambda t: -t[0])

    enemies_svg = []
    for dist, diff, e in sprites:
        sx = (0.5 + diff / FOV) * W
        ray_idx = max(0, min(RAYS - 1, int(sx / slice_w)))
        if dist >= zbuf[ray_idx]:
            continue
        sz = min(170, 155 / dist)
        sy = VH * 0.52
        enemies_svg.append(f'''
        <g class="demon-bob" transform="translate({sx:.1f},{sy:.1f})">
          <ellipse cx="0" cy="{sz*0.58:.1f}" rx="{sz*0.36:.1f}" ry="{sz*0.1:.1f}" fill="#000" fill-opacity="0.45"/>
          <circle cx="0" cy="0" r="{sz*0.44:.1f}" fill="#DC2626" stroke="#FF9F1C" stroke-width="2.2"/>
          <polygon points="{-sz*0.38:.1f},{-sz*0.22:.1f} {-sz*0.24:.1f},{-sz*0.54:.1f} {-sz*0.12:.1f},{-sz*0.34:.1f}" fill="#FDE68A"/>
          <polygon points="{sz*0.38:.1f},{-sz*0.22:.1f} {sz*0.24:.1f},{-sz*0.54:.1f} {sz*0.12:.1f},{-sz*0.34:.1f}" fill="#FDE68A"/>
          <ellipse cx="0" cy="{-sz*0.05:.1f}" rx="{sz*0.2:.1f}" ry="{sz*0.12:.1f}" fill="#39FF14"/>
          <circle cx="0" cy="{-sz*0.05:.1f}" r="{sz*0.06:.1f}" fill="#09090B"/>
          <path d="M{-sz*0.22:.1f},{sz*0.16:.1f} Q0,{sz*0.34:.1f} {sz*0.22:.1f},{sz*0.16:.1f} Z" fill="#09090B"/>
          <text x="0" y="{-sz*0.56:.1f}" text-anchor="middle" fill="#FF9F1C" font-family="monospace" font-size="11" font-weight="700">{e["id"]} [{e["hp"]}HP]</text>
        </g>''')

    # 2D Tactical Minimap (top right)
    mm_cell = 11
    mm_x0, mm_y0 = W - len(MAP[0]) * mm_cell - 16, 14
    mm_svg = [f'<rect x="{mm_x0-6}" y="{mm_y0-6}" width="{len(MAP[0])*mm_cell+12}" height="{len(MAP)*mm_cell+12}" rx="8" fill="#09090B" fill-opacity="0.82" stroke="#39FF14" stroke-opacity="0.55" stroke-width="1.2"/>']
    for r_i, row in enumerate(MAP):
        for c_i, cell in enumerate(row):
            if cell > 0:
                fc = "#FF2A2A" if cell == 1 else "#475569"
                mm_svg.append(f'<rect x="{mm_x0+c_i*mm_cell}" y="{mm_y0+r_i*mm_cell}" width="{mm_cell-1}" height="{mm_cell-1}" fill="{fc}" fill-opacity="0.85"/>')
    for e in st["enemies"]:
        if e["hp"] > 0:
            mm_svg.append(f'<circle cx="{mm_x0+e["x"]*mm_cell:.1f}" cy="{mm_y0+e["y"]*mm_cell:.1f}" r="3" fill="#FF9F1C"/>')
    p_mx, p_my = mm_x0 + px * mm_cell, mm_y0 + py * mm_cell
    mm_svg.append(f'<line x1="{p_mx:.1f}" y1="{p_my:.1f}" x2="{p_mx+math.cos(pa)*11:.1f}" y2="{p_my+math.sin(pa)*11:.1f}" stroke="#39FF14" stroke-width="2"/>')
    mm_svg.append(f'<circle cx="{p_mx:.1f}" cy="{p_my:.1f}" r="3.4" fill="#39FF14"/>')

    flash_svg = ""
    if st.get("fired"):
        flash_svg = f'''
        <g class="flash">
          <circle cx="{W/2}" cy="{VH-112}" r="44" fill="#FF9F1C" fill-opacity="0.55"/>
          <circle cx="{W/2}" cy="{VH-112}" r="22" fill="#FFFBEB"/>
          <line x1="{W/2}" y1="{VH-112}" x2="{W/2}" y2="{VH*0.5}" stroke="#39FF14" stroke-width="4" stroke-opacity="0.85"/>
        </g>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Playable DOOM 3D Raycaster on GitHub">
  <defs>
    <linearGradient id="ceilGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#050507"/>
      <stop offset="100%" stop-color="#1A0B0E"/>
    </linearGradient>
    <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#17171D"/>
      <stop offset="100%" stop-color="#09090B"/>
    </linearGradient>
    <style>
      .gun-bob {{ animation: bob 2.2s ease-in-out infinite; }}
      .demon-bob {{ animation: float 2.6s ease-in-out infinite; }}
      .core-pulse {{ animation: glow 1.4s ease-in-out infinite; }}
      @keyframes bob {{ 0%,100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(5px); }} }}
      @keyframes float {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.92; }} }}
      @keyframes glow {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.45; }} }}
    </style>
  </defs>

  <rect width="{W}" height="{H}" rx="18" fill="#09090B"/>
  <rect x="0" y="0" width="{W}" height="{VH/2}" fill="url(#ceilGrad)"/>
  <rect x="0" y="{VH/2}" width="{W}" height="{VH/2}" fill="url(#floorGrad)"/>

  <!-- 3D Raycasted Walls -->
  {''.join(walls_svg)}
  <!-- 3D Z-Buffered Demons -->
  {''.join(enemies_svg)}

  <!-- Center Crosshair -->
  <g stroke="#39FF14" stroke-opacity="0.78" stroke-width="1.5">
    <line x1="{W/2-12}" y1="{VH/2}" x2="{W/2-4}" y2="{VH/2}"/>
    <line x1="{W/2+4}" y1="{VH/2}" x2="{W/2+12}" y2="{VH/2}"/>
    <line x1="{W/2}" y1="{VH/2-12}" x2="{W/2}" y2="{VH/2-4}"/>
    <line x1="{W/2}" y1="{VH/2+4}" x2="{W/2}" y2="{VH/2+12}"/>
  </g>

  {flash_svg}

  <!-- First-Person DOOM Plasma Rifle -->
  <g class="gun-bob">
    <polygon points="{W/2-52},{VH} {W/2-28},{VH-92} {W/2+28},{VH-92} {W/2+52},{VH}" fill="#1E293B" stroke="#475569" stroke-width="2"/>
    <rect x="{W/2-18}" y="{VH-114}" width="36" height="32" rx="4" fill="#334155" stroke="#94A3B8" stroke-width="1.5"/>
    <rect class="core-pulse" x="{W/2-10}" y="{VH-106}" width="20" height="14" rx="3" fill="#39FF14"/>
    <rect x="{W/2-34}" y="{VH-54}" width="68" height="12" rx="3" fill="#0F172A" stroke="#FF2A2A" stroke-width="1.5"/>
  </g>

  <!-- Tactical Minimap -->
  {''.join(mm_svg)}

  <!-- Top-left Sector Badge -->
  <rect x="14" y="14" width="232" height="28" rx="6" fill="#09090B" fill-opacity="0.82" stroke="#FF2A2A" stroke-width="1.2"/>
  <text x="26" y="32" fill="#FF2A2A" font-family="monospace" font-size="12" font-weight="800">E1M1 // ADITYA'S LSM-HANGAR</text>

  <!-- Classic DOOM Bottom Status HUD -->
  <rect x="0" y="{VH}" width="{W}" height="{HUD_H}" fill="#18181B"/>
  <line x1="0" y1="{VH}" x2="{W}" y2="{VH}" stroke="#FF2A2A" stroke-width="2.5"/>

  <g font-family="monospace" text-anchor="middle">
    <text x="90"  y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">PLASMA AMMO</text>
    <text x="90"  y="{VH+56}" fill="#FF9F1C" font-size="30" font-weight="900">{st["ammo"]}</text>

    <text x="235" y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">HEALTH</text>
    <text x="235" y="{VH+56}" fill="#39FF14" font-size="30" font-weight="900">{st["hp"]}%</text>

    <text x="380" y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">ARMOR</text>
    <text x="380" y="{VH+56}" fill="#38BDF8" font-size="30" font-weight="900">{st["armor"]}%</text>

    <text x="515" y="{VH+24}" fill="#94A3B8" font-size="11" font-weight="700">FRAGS</text>
    <text x="515" y="{VH+56}" fill="#FF2A2A" font-size="30" font-weight="900">{st["frags"]}</text>
  </g>

  <rect x="585" y="{VH+12}" width="300" height="58" rx="8" fill="#09090B" stroke="#27272A" stroke-width="1.2"/>
  <text x="598" y="{VH+32}" fill="#39FF14" font-family="monospace" font-size="11" font-weight="700">LAST PILOT: @{st["last_player"]}</text>
  <text x="598" y="{VH+54}" fill="#F8FAFC" font-family="monospace" font-size="10.5">{st["last_log"][:42]}</text>
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
