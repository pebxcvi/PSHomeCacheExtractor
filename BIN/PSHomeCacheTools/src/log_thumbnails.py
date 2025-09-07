import sys
import re

REGIONS = [
    "en-US", "en-GB", "fr-FR", "ja-JP", "ko-KR", "it-IT", "es-ES", "de-DE", "zh-TW", "zh-HK", "en-SG"
]

SCENE_PATTERNS = [
    (r'^Cinema$',                       r'(?i)^large_en-us_T(?P<tval>\d+)\.png$',              r'Cinema_T{tval}L-SCEA.png'),
    (r'^Cinema$',                       r'(?i)^large_scee_T(?P<tval>\d+)\.png$',               r'Cinema_T{tval}L-SCEE.png'),
    (r'^Cinema$',                       r'(?i)^large_ja-JP_T(?P<tval>\d+)\.png$',              r'Cinema_T{tval}L-SCEJ.png'),
    (r'^Cinema$',                       r'(?i)^large_sceasia_T(?P<tval>\d+)\.png$',            r'Cinema_T{tval}L-SCEAsia.png'),
    (r'^Cinema$',                       r'(?i)^large_en-us\.png$',                             r'Cinema_T000L-SCEA.png'),
    (r'^Cinema$',                       r'(?i)^large_scee\.png$',                              r'Cinema_T000L-SCEE.png'),
    (r'^Cinema$',                       r'(?i)^large_ja-jp\.png$',                             r'Cinema_T000L-SCEJ.png'),
    (r'^Cinema$',                       r'(?i)^large_sceasia\.png$',                           r'Cinema_T000L-SCEAsia.png'),
    (r'^Game_Space$',                   r'(?i)^large_en-us_T(?P<tval>\d+)\.png$',              r'Game_Space_T{tval}L-SCEA.png'),
    (r'^Game_Space$',                   r'(?i)^large_scee_T(?P<tval>\d+)\.png$',               r'Game_Space_T{tval}L-SCEE.png'),
    (r'^Game_Space$',                   r'(?i)^large_ja-JP_T(?P<tval>\d+)\.png$',              r'Game_Space_T{tval}L-SCEJ.png'),
    (r'^Game_Space$',                   r'(?i)^large_sceasia_T(?P<tval>\d+)\.png$',            r'Game_Space_T{tval}L-SCEAsia.png'),
    (r'^Game_Space$',                   r'(?i)^large_en-us\.png$',                             r'Game_Space_T000L-SCEA.png'),
    (r'^Game_Space$',                   r'(?i)^large_scee\.png$',                              r'Game_Space_T000L-SCEE.png'),
    (r'^Game_Space$',                   r'(?i)^large_ja-jp\.png$',                             r'Game_Space_T000L-SCEJ.png'),
    (r'^Game_Space$',                   r'(?i)^large_sceasia\.png$',                           r'Game_Space_T000L-SCEAsia.png'),
    (r'^Home_Square$',                  r'(?i)^large_en-us_T(?P<tval>\d+)\.png$',              r'Home_Square_T{tval}L-SCEA.png'),
    (r'^Home_Square$',                  r'(?i)^large_scee_T(?P<tval>\d+)\.png$',               r'Home_Square_T{tval}L-SCEE.png'),
    (r'^Home_Square$',                  r'(?i)^large_ja-jp_T(?P<tval>\d+)\.png$',              r'Home_Square_T{tval}L-SCEJ.png'),
    (r'^Home_Square$',                  r'(?i)^large_sceasia_T(?P<tval>\d+)\.png$',            r'Home_Square_T{tval}L-SCEAsia.png'),
    (r'^Home_Square$',                  r'(?i)^large_en-us\.png$',                             r'Home_Square_T000L-SCEA.png'),
    (r'^Home_Square$',                  r'(?i)^large_scee\.png$',                              r'Home_Square_T000L-SCEE.png'),
    (r'^Home_Square$',                  r'(?i)^large_ja-jp\.png$',                             r'Home_Square_T000L-SCEJ.png'),
    (r'^Home_Square$',                  r'(?i)^large_sceasia\.png$',                           r'Home_Square_T000L-SCEAsia.png'),
    (r'^Marketplace$',                  r'(?i)^large_en-us_T(?P<tval>\d+)\.png$',              r'Marketplace_T{tval}L-SCEA.png'),
    (r'^Marketplace$',                  r'(?i)^large_scee_T(?P<tval>\d+)\.png$',               r'Marketplace_T{tval}L-SCEE.png'),
    (r'^Marketplace$',                  r'(?i)^large_sceasia_T(?P<tval>\d+)\.png$',            r'Marketplace_T{tval}L-SCEAsia.png'),
    (r'^Marketplace$',                  r'(?i)^large_ja-jp_T(?P<tval>\d+)\.png$',              r'Marketplace_T{tval}L-SCEJ.png'),
    (r'^Marketplace$',                  r'(?i)^large_en-us\.png$',                             r'Marketplace_T000L-SCEA.png'),
    (r'^Marketplace$',                  r'(?i)^large_scee\.png$',                              r'Marketplace_T000L-SCEE.png'),
    (r'^Marketplace$',                  r'(?i)^large_ja-jp\.png$',                             r'Marketplace_T000L-SCEJ.png'),
    (r'^Marketplace$',                  r'(?i)^large_sceasia\.png$',                           r'Marketplace_T000L-SCEAsia.png'),
    (r'^Marketplace$',                  r'^large\.png$',                                       r'Marketplace_T000L-SCEA.png'),
    (r'^SCE_Cinema$',                   r'^EU_Cinema_large\.png$',                             r'SCE_Cinema_T000L-SCEE.png'),
    (r'^SCE_Cinema$',                   r'^EU_Cinema_large_T(?P<tval>\d+)\.png$',              r'SCE_Cinema_T{tval}L-SCEE.png'),
    (r'^SCE_Cinema$',                   r'^SCEAsia_large\.png$',                               r'SCE_Cinema_T000L-SCEAsia.png'),
    (r'^SCE_Cinema$',                   r'^US_Cinema_large_T(?P<tval>\d+)\.png$',              r'SCE_Cinema_T{tval}-SCEA.png'),
    (r'^SCE_Cinema$',                   r'^US_large_T(?P<tval>\d+)\.png$',                     r'SCE_Cinema_T{tval}-SCEA.png'),
    (r'^SCE_Cinema$',                   r'^SCEJ_large\.png$',                                  r'SCE_Cinema_T000L-SCEJ.png'),
    (r'^SCE_GameSpace$',                r'^EU_GameSpace_large\.png$',                          r'SCE_GameSpace_T000L-SCEE.png'),
    (r'^SCE_GameSpace$',                r'^EU_GameSpace_large_T(?P<tval>\d+)\.png$',           r'SCE_GameSpace_T{tval}L-SCEE.png'),
    (r'^SCE_GameSpace$',                r'^GameSpaceAsiaDL\.png$',                             r'SCE_GameSpace_T000L-SCEAsia.png'),
    (r'^SCE_GameSpace$',                r'^US_large_T(?P<tval>\d+)\.png$',                     r'SCE_GameSpace_T{tval}-SCEA.png'),
    (r'^SCE_GameSpace$',                r'^large\.png$',                                       r'SCE_GameSpace_T000L-SCEA.png'),
    (r'^SCE_GameSpace$',                r'^Jlarge\.png$',                                      r'SCE_GameSpace_T000L-SCEJ.png'),
    (r'^SCE_HomeSquare$',               r'^Jlarge\.png$',                                      r'SCE_HomeSquare_T000L-SCEJ.png'),
    (r'^SCE_HomeSquare$',               r'^Jlarge_T(?P<tval>\d+)\.png$',                       r'SCE_HomeSquare_T{tval}L-SCEJ.png'),
    (r'^SCE_HomeSquare$',               r'^US_large\.png$',                                    r'SCE_HomeSquare_T000L-SCEA.png'),
    (r'^SCE_HomeSquare$',               r'^EU_HomeSquare_large\.png$',                         r'SCE_HomeSquare_T000L-SCEE.png'),
    (r'^SCE_HomeSquare$',               r'^EU_HomeSquare_large_T(?P<tval>\d+)\.png$',          r'SCE_HomeSquare_T{tval}L-SCEE.png'),
    (r'^SCE_HomeSquare$',               r'^EU_large_T(?P<tval>\d+)\.png$',                     r'SCE_HomeSquare_T{tval}L-SCEE.png'),
    (r'^SCE_HomeSquare$',               r'^homesquare_KR\.png$',                               r'SCE_HomeSquare_T000L-SCEAsia.png'),
    (r'^SCE_HomeSquare$',               r'^US_HomePlaza_large_T(?P<tval>\d+)\.png$',           r'SCE_HomeSquare_T{tval}-SCEA.png'),
    (r'^SCE_Marketplace$',              r'^EU_large_T(?P<tval>\d+)\.png$',                     r'SCE_Marketplace_T{tval}L-SCEE.png'),
    (r'^SCE_Marketplace$',              r'^EU_marketplace_large\.png$',                        r'SCE_Marketplace_T000L-SCEE.png'),
    (r'^SCE_Marketplace$',              r'^US_Marketplace_large\.png$',                        r'SCE_Marketplace_T000L-SCEA.png'),
    (r'^SCE_Marketplace$',              r'^US_Marketplace_large_T(?P<tval>\d+)\.png$',         r'SCE_Marketplace_T{tval}L-SCEA.png'),
    (r'^SCE_Marketplace$',              r'^Jmarketplace_nova_large_T(?P<tval>\d+)\.png$',      r'SCE_Marketplace_T{tval}L-SCEJ.png'),
    (r'^SCE_BasicClubhouse$',           r'^club_house_v1_large\.png$',                         r'SCE_BasicClubhouse_T000L.png'),
    (r'^SCE_BasicClubhouse$',           r'^club_house_v1_large_T(?P<tval>\d+)\.png$',          r'SCE_BasicClubhouse_T{tval}L.png'),
    (r'^SCE_Summerhouse$',              r'^summerhouse_large_T(?P<tval>\d+)\.png$',            r'SCE_Summerhouse_T{tval}L.png'),
    (r'^SCE_Cafe$',                     r'^US_large\.png$',                                    r'SCE_Cafe_T000L-SCEA.png'),
    (r'^SCE_Cafe$',                     r'^Jlarge_T(?P<tval>\d+)\.png$',                       r'SCE_Cafe_T{tval}L-SCEJ.png'),
    (r'^PackagedScenes$',               r'^basic_apartment_large\.png$',                       r'basic_apartment_T000L.png'),
    (r'^LOOT_Public_Space_237E_1F7A$',  r'^en-US_large_T(?P<tval>\d+)\.png$',                  r'LOOT_Public_Space_237E_1F7A_T{tval}L.png'),
    (r'^SCEA_Central_Plaza_C9D2_1E85$', r'^large_en-US_T(?P<tval>\d+)\.png$',                  r'SCEA_Central_Plaza_C9D2_1E85_T{tval}L.png'),
    (r'^SCEA_HomeCafe_7898_7B5$',       r'^US_large\.png$',                                    r'SCEA_HomeCafe_7898_7B5_T000L.png'),
    (r'^VMShoppingCentre_F1EB_5D0C$',   r'^large_scee_T(?P<tval>\d+)\.png$',                   r'VMShoppingCentre_F1EB_5D0C_T{tval}L.png'),
    (r'^VMShoppingCentre_F1EB_5D0C$',   r'^large_scee\.png$',                                  r'VMShoppingCentre_F1EB_5D0C_T000L.png'),
    (r'^New_Home_Square_3_5305_3636$',  r'^large_scee_T(?P<tval>\d+)\.png$',                   r'New_Home_Square_3_5305_3636_T{tval}L.png'),
    (r'^New_Home_Square_3_5305_3636$',  r'^large_scee\.png$',                                  r'New_Home_Square_3_5305_3636_T000L.png'),
    (r'^2013_Marketplace_8480_98F0$',   r'^large_scee_T(?P<tval>\d+)\.png$',                   r'2013_Marketplace_8480_98F0_T{tval}L.png'),
    (r'^2013_Marketplace_8480_98F0$',   r'^large_scee\.png$',                                  r'2013_Marketplace_8480_98F0_T000L.png'),
    (r'^2013_Cinema_193B_7E40$',        r'^large_scee_T(?P<tval>\d+)\.png$',                   r'2013_Cinema_193B_7E40_T{tval}L.png'),
    (r'^2013_Cinema_193B_7E40$',        r'^large_scee\.png$',                                  r'2013_Cinema_193B_7E40_T000L.png'),
    (r'^jcinema_auditorium_1$',         r'^large_ja-JP_T(?P<tval>\d+)\.png$',                  r'jcinema_auditorium_1_T{tval}L.png'),
    (r'^jcinema_auditorium_2$',         r'^large_ja-JP_T(?P<tval>\d+)\.png$',                  r'jcinema_auditorium_2_T{tval}L.png'),
]

DEBUG_LOG_FILE = "tmp.log"
debug_scenes = False
debug_objects = False

LOG_TO_FILE = False
if "--logtofile" in sys.argv:
    LOG_TO_FILE = True
    sys.argv.remove("--logtofile")
if "--logtocmd" in sys.argv:
    LOG_TO_FILE = False
    sys.argv.remove("--logtocmd")
if "--debugscenes" in sys.argv:
    debug_scenes = True
    sys.argv.remove("--debugscenes")
if "--debugobjects" in sys.argv:
    debug_objects = True
    sys.argv.remove("--debugobjects")

_debug_lines = []

def log_debug(msg, sortkey=None):
    """Write to log file or CMD, storing for sorting if logging to file."""
    if LOG_TO_FILE:
        key = sortkey if sortkey is not None else ("", "")
        _debug_lines.append((key, msg))
    else:
        print(msg)

def parse_inf_line(line):
    parts = line.rstrip("\r\n").split("|")
    if len(parts) < 4:
        return None
    E, F, G, H = parts[:4]
    return E, F, G, H


def build_thumb(E, F, G, H):
    if not F.lower().endswith(".png"):
        return None

    fields = F.split("/")
    fields += [""] * (8 - len(fields))
    K, L, M, N, O, P, Q, R = fields[:8]

    BLACKLIST_PREFIXES = [
        "gp1.wac.edgecastcdn.net",
        "www.outso-srv1.com",
    ]
    if any(F.startswith(prefix) for prefix in BLACKLIST_PREFIXES):
        return None

    is_scene = O.lower() == "scenes" or P.lower() == "scenes"
    is_object = O.lower() == "objects" or P.lower() == "objects"

    if P.lower() in ("scenes", "objects"):
        scene_name = Q
        filename = R if R else Q
    else:
        scene_name = P
        filename = Q

    # --- REGEX MATCH LOGIC ---
    if is_scene:
        for scene_pat, file_pat, result_template in SCENE_PATTERNS:
            scene_match = re.match(scene_pat, scene_name)
            file_match = re.match(file_pat, filename)
            if scene_match and file_match:
                m = file_match
                matched_result = result_template.format(**m.groupdict())
                if debug_scenes:
                    if P.lower() == "scenes":
                        log_debug(f"[DBG][SCENE] N={N!r} O={O!r} P={P!r} Q={Q!r} R={R!r} => REGEX MATCHED => {matched_result}", (scene_name, filename))
                    else:
                        log_debug(f"[DBG][SCENE] O={O!r} P={P!r} Q={Q!r} => REGEX MATCHED => {matched_result}", (scene_name, filename))
                if P.lower() == "scenes":
                    return f"{H}\t{E}\t{G}\t{N}\t{P}\t{Q}\t{filename}\t{matched_result}"
                else:
                    n_val = M if M.lower() == "dev" else N
                    return f"{H}\t{E}\t{G}\t{n_val}\t{O}\t{P}\t{filename}\t{matched_result}"

    if not (is_scene or is_object):
        return None

    # --- REGION/NAMING LOGIC ---
    region_tag = None
    if "_" in filename:
        region_prefix = filename.split("_", 1)[0]
        for region in REGIONS:
            if region_prefix == region:
                region_tag = region
                break

    # -- LEFT-HAND PREFIX LOGIC --
    if O.lower() in ("scenes", "objects"):
        left = P
    elif P.lower() in ("scenes", "objects"):
        left = scene_name
    else:
        left = P

    # -- BUILD RESULT FILENAME --
    if region_tag:
        region_code = region_tag[-2:].upper()
        SLM = ""
        if "_small" in filename:
            SLM = "S"
        elif "_large" in filename:
            SLM = "L"
        elif "_maker" in filename:
            SLM = "M"
        TXXX = "T000"
        for part in filename.split("_"):
            if part.startswith("T") and part[1:4].isdigit():
                TXXX = part[:4]
                break
        result = f"{left}_{TXXX}{SLM}-{region_code}.png"
    else:
        REM_EXT = filename[:-4] if filename.lower().endswith('.png') else filename
        onelet = REM_EXT[:1].upper()
        if onelet == "S":
            oneletc = "S"
        elif onelet == "L":
            oneletc = "L"
        elif onelet == "M":
            oneletc = "M"
        else:
            oneletc = ""
        ver = REM_EXT[-4:]
        V = REM_EXT.lower() in ["large", "small", "maker"]
        if V:
            result = f"{left}_T000{oneletc}.png"
        else:
            result = f"{left}_{ver}{oneletc}.png"

    # --- FINAL OUTPUT FORMAT LOGIC ---
    if O.lower() == "objects":
        n_val = M if M.lower() == "dev" else N
        result_str = f"{H}\t{E}\t{G}\t{n_val}\t{O}\t{P}\t{filename}\t{result}"
        if debug_objects:
            log_debug(f"[DBG][OBJECT] O={O!r} P={P!r} Q={Q!r} => {result}", (scene_name, filename))
        return result_str
    elif P.lower() == "objects":
        result_str = f"{H}\t{E}\t{G}\t{N}\t{P}\t{Q}\t{filename}\t{result}"
        if debug_objects:
            log_debug(f"[DBG][OBJECT] N={N!r} O={O!r} P={P!r} Q={Q!r} R={R!r} => {result}", (scene_name, filename))
        return result_str
    elif O.lower() == "scenes":
        n_val = M if M.lower() == "dev" else N
        result_str = f"{H}\t{E}\t{G}\t{n_val}\t{O}\t{P}\t{filename}\t{result}"
        if debug_scenes:
            log_debug(f"[DBG][SCENE] O={O!r} P={P!r} Q={Q!r} => {result}", (scene_name, filename))
        return result_str
    elif P.lower() == "scenes":
        result_str = f"{H}\t{E}\t{G}\t{N}\t{P}\t{Q}\t{filename}\t{result}"
        if debug_scenes:
            log_debug(f"[DBG][SCENE] N={N!r} O={O!r} P={P!r} Q={Q!r} R={R!r} => {result}", (scene_name, filename))
        return result_str
    else:
        result_str = f"{H}\t{E}\t{G}\t{N}\t{O}\t{P}\t{filename}\t{result}"
        return result_str


def main():
    if len(sys.argv) != 3:
        print("Usage: log_thumbnails.py <inf_file_path> <thumbnail_log> [--debugscenes] [--debugobjects] [--logtofile|--logtocmd]")
        sys.exit(1)

    inf_file = sys.argv[1]
    thumbs_file = sys.argv[2]

    if LOG_TO_FILE:
        open(DEBUG_LOG_FILE, "w").close()

    with open(inf_file, encoding="utf-8") as f_in, open(thumbs_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            parsed = parse_inf_line(line)
            if not parsed:
                continue
            E, F, G, H = parsed
            entry = build_thumb(E, F, G, H)
            if entry:
                f_out.write(entry + "\n")
                f_out.flush()

    if LOG_TO_FILE and _debug_lines:
        _debug_lines.sort(key=lambda t: t[0])
        with open(DEBUG_LOG_FILE, "w", encoding="utf-8") as f:
            for _, msg in _debug_lines:
                f.write(msg + "\n")

if __name__ == "__main__":
    main()
