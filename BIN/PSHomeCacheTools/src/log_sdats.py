import sys
import os
from pathlib import Path
import time

def dbg(msg, *args):
    print("[DEBUG]", msg % args if args else msg)

def get_file_size(file_path):
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        dbg("Error getting file size: %s", e)
        return -1

def get_sdata_version(file_path, file_size):
    if not file_path.lower().endswith('.sdat'):
        return "NA"
    if file_size < 16:
        return "0"
    version_signatures = {
        b"SDATA 4.0.0.W\x00\x00\x00": "4.0",
        b"SDATA 2.4.0.W\x00\x00\x00": "2.4",
        b"SDATA 2.2.0.W\x00\x00\x00": "2.2",
        b"SDATA 3.3.0.W\x00\x00\x00": "3.3",
    }
    try:
        with open(file_path, 'rb') as file:
            file.seek(-16, 2)
            end_bytes = file.read(16)
            for signature, version in version_signatures.items():
                if end_bytes == signature:
                    return version
            return "0"
    except Exception as e:
        dbg("Error checking SDATA version: %s", e)
        return "ERROR"

def split_inf_path(path):
    parts = path.strip('/').split('/')
    while len(parts) < 9:
        parts.append('')
    return parts[:9]

def find_objects_fields(parts):
    if parts[4].lower() == "objects":
        return True, "O"
    if parts[5].lower() == "objects":
        return True, "P"
    return False, None

def find_scenes_fields(parts):
    if parts[4].lower() == "scenes":
        return True, "O"
    if parts[5].lower() == "scenes":
        return True, "P"
    return False, None

def get_ext(filename):
    return filename.rsplit('.', 1)[-1] if '.' in filename else ''

def get_fname_without_ext(filename):
    return filename.rsplit('.', 1)[0] if '.' in filename else filename

def build_sdat_index(search_root):
    index = {}
    for f in Path(search_root).rglob("*.sdat"):
        if f.is_file():
            name = f.name.lower()
            if name.endswith(".sdat") and "_dat" in name:
                hashval = name.split('_')[0]
                if hashval not in index:
                    index[hashval] = []
                index[hashval].append(str(f))
    return index

def find_sdat_file_from_index(sdat_index, hashval, _call_counter=[0]):
    _call_counter[0] += 1
    hashval = str(hashval).lower()
    matches = sdat_index.get(hashval, [])
    if matches:
        return matches[0]
    return None

_sdat_dir_cache = {}
_sdat_hash_index = {}

def find_sdat_file_unlimited(path_combo, inf_cachename, INF_hash, debug):
    FIXED_FOLDERS = {"NPIA00005", "NPIA00010", "NPEA00013"}
    FIXED_FOLDERS_LC = {f.lower() for f in FIXED_FOLDERS}

    if "|" not in path_combo:
        if debug:
            dbg("No '|' found in cache_folder_path: %r", path_combo)
        return None

    root, sub = path_combo.split("|", 1)
    root = root.strip().replace("/", "\\")
    sub = sub.strip().replace("/", "\\").lstrip("\\")
    search_root = Path(root)

    if not search_root.is_dir():
        if debug:
            dbg("Root search directory does not exist: %r", search_root)
        return None

    inf_cachename_lc = inf_cachename.lower()
    sub_lc_parts = [s.lower() for s in Path(sub).parts]
    cache_key = (str(search_root).lower(), inf_cachename_lc, str(sub).lower())

    if cache_key not in _sdat_dir_cache:
        matched_dirs = []
        for dirpath, dirnames, filenames in os.walk(search_root):
            dirpath_parts = Path(dirpath).parts
            dirpath_parts_lc = [p.lower() for p in dirpath_parts]

            try:
                idx_inf = dirpath_parts_lc.index(inf_cachename_lc)
            except ValueError:
                continue

            for i in range(len(dirpath_parts_lc) - len(sub_lc_parts) + 1):
                if dirpath_parts_lc[i:i + len(sub_lc_parts)] == sub_lc_parts:
                    idx_sub = i
                    break
            else:
                continue

            between = dirpath_parts_lc[idx_inf + 1:idx_sub]
            if not FIXED_FOLDERS_LC.intersection(between):
                continue

            matched_dirs.append(Path(dirpath))

            hash_key = (inf_cachename_lc, dirpath.lower())
            if hash_key not in _sdat_hash_index:
                _sdat_hash_index[hash_key] = {}
                for file in filenames:
                    if file.lower().endswith(".sdat") and "_dat" in file.lower():
                        hashval = file.lower().split("_")[0]
                        _sdat_hash_index[hash_key][hashval] = os.path.join(dirpath, file)

        _sdat_dir_cache[cache_key] = matched_dirs
        if debug:
            dbg("Cached %d dirs for key: %r", len(matched_dirs), cache_key)

    for candidate in _sdat_dir_cache[cache_key]:
        hash_key = (inf_cachename_lc, str(candidate).lower())
        sdat_map = _sdat_hash_index.get(hash_key, {})
        sdat_file = sdat_map.get(INF_hash.lower())
        if sdat_file:
            if debug:
                dbg("Found SDAT (unlimited_all): %s (hash match: %s)", sdat_file, INF_hash)
            return sdat_file

    if debug:
        dbg("No SDAT found for unlimited_all: %s\\%s\\**\\%s [hash=%s]", root, inf_cachename, sub, INF_hash)
    return None



def process_objects(
    lines, log_func, cachename=None, debug=False, object_cache_folder=None, sdat_index=None,
    unlimited_all=False, start_time=None
):
    import time
    found = False
    printed_cachenames = set()
    infcachename_counter = 1

    def format_delta(seconds):
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m{seconds % 60:02d}s"
        else:
            return f"{seconds // 3600}h{(seconds % 3600)//60:02d}m{seconds % 60:02d}s"

    sdat_count_by_cache = {}
    for line in lines:
        parts = line.rstrip('\n').split('|')
        if len(parts) < 4:
            continue
        _, INF_path, _, INF_cachename = parts[:4]
        if INF_path.lower().endswith('.sdat'):
            key = INF_cachename.lower()
            sdat_count_by_cache[key] = sdat_count_by_cache.get(key, 0) + 1

    object_cache_missing = object_cache_folder is not None and not os.path.isdir(
        object_cache_folder.split("|")[0] if unlimited_all and "|" in object_cache_folder else object_cache_folder
    )

    curr_cache = None
    curr_cache_start = None

    printed_stats_for_current = False

    cache_lines = []
    for line in lines:
        parts = line.rstrip('\n').split('|')
        cache_lines.append(parts[3].lower() if len(parts) >= 4 else None)

    for idx, (line_num, line) in enumerate(zip(range(1, len(lines)+1), lines)):
        parts = line.rstrip('\n').split('|')
        if len(parts) < 4:
            if debug:
                dbg("Skipping line %d (too few fields): %r", line_num, line)
            continue
        INF_hash, INF_path, INF_date, INF_cachename = parts[:4]
        inf_cachename_lc = INF_cachename.lower()

        if unlimited_all and inf_cachename_lc != curr_cache:
            if curr_cache is not None and curr_cache_start is not None:
                now = time.time()
                delta = now - curr_cache_start
                print(f"({infcachename_counter-1}) {curr_cache_name} ~ stats : sdats = {sdat_count_by_cache.get(curr_cache, 0)} / time taken = {format_delta(delta)}")
                printed_stats_for_current = True
            elapsed = time.time() - start_time if start_time is not None else 0
            elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            print(f"({infcachename_counter}) ({elapsed_str}) logging {INF_cachename} ...")
            curr_cache = inf_cachename_lc
            curr_cache_start = time.time()
            curr_cache_name = INF_cachename
            infcachename_counter += 1
            printed_stats_for_current = False

        cache_out = INF_cachename if unlimited_all else (cachename if cachename is not None else INF_cachename)

        if not (INF_path.lower().endswith('.sdat') or INF_path.lower().endswith('.bar')):
            continue

        split_path = split_inf_path(INF_path)
        is_object, which = find_objects_fields(split_path)
        if not is_object:
            continue
        K, L, M, N, O, P, Q, R, S = split_path

        if (which == "O" and P.lower() == "objectcatalogue.bar") or (which == "P" and Q.lower() == "objectcatalogue.bar"):
            if debug:
                dbg("Ignoring ObjectCatalogue.bar at line %d", line_num)
            continue
        if INF_path.lower().endswith('.bar'):
            version_field = "n/a"
        elif unlimited_all:
            if object_cache_folder:
                sdat_file = find_sdat_file_unlimited(object_cache_folder, INF_cachename, INF_hash, debug)
            else:
                sdat_file = None
            if sdat_file is None:
                version_field = "n/a"
            else:
                size = get_file_size(sdat_file)
                version_field = get_sdata_version(sdat_file, size)
        elif cachename is None:
            version_field = "n/a"
        elif object_cache_folder is None or object_cache_missing:
            version_field = "n/a"
        elif cachename.lower() != INF_cachename.lower():
            version_field = "n/a"
        else:
            if sdat_index is not None:
                sdat_file = find_sdat_file_from_index(sdat_index, INF_hash)
            else:
                sdat_file = None
            if sdat_file is None:
                version_field = "n/a"
            else:
                size = get_file_size(sdat_file)
                version_field = get_sdata_version(sdat_file, size)

        if which == "O":
            if M.lower() == 'cds':
                field4 = L.rstrip('/')
            elif M.lower() == 'dev':
                field4 = f"{L.rstrip('/')}.{M.rstrip('/')}"
            else:
                field4 = M.rstrip('/')
            field5 = N.rstrip('/')
            uuid = P.rstrip('/')
            fname_wo_ext = get_fname_without_ext(Q)
            ext = get_ext(Q)
            txxx = 'T000'
            if '_' in fname_wo_ext and fname_wo_ext.split('_')[-1].upper().startswith('T'):
                tpart = fname_wo_ext.split('_')[-1]
                if tpart[1:].isdigit():
                    txxx = tpart.upper()
            sdatname = f"{uuid}_{txxx}"
        else:
            field4 = f"{L.rstrip('/')}.{N.rstrip('/')}"
            field5 = O.rstrip('/')
            uuid = Q.rstrip('/')
            fname_wo_ext = get_fname_without_ext(R)
            ext = get_ext(R)
            txxx = 'T000'
            if '_' in fname_wo_ext and fname_wo_ext.split('_')[-1].upper().startswith('T'):
                tpart = fname_wo_ext.split('_')[-1]
                if tpart[1:].isdigit():
                    txxx = tpart.upper()
            sdatname = f"{uuid}_{txxx}"

        log_func('\t'.join([
            cache_out,
            INF_hash,
            INF_date,
            field4,
            field5,
            uuid,
            fname_wo_ext,
            ext,
            version_field,
            sdatname
        ]))
        found = True

    if unlimited_all and curr_cache is not None and curr_cache_start is not None and not printed_stats_for_current:
        now = time.time()
        delta = now - curr_cache_start
        print(f"({infcachename_counter-1}) {curr_cache_name} ~ stats : sdats = {sdat_count_by_cache.get(curr_cache, 0)} / time taken = {format_delta(delta)}")

    return found


def process_scenes(
    lines, log_func, cachename=None, debug=False, scene_cache_folder=None, sdat_index=None,
    unlimited_all=False, start_time=None
):
    import time
    found = False
    printed_cachenames = set()
    infcachename_counter = 1

    def human_time(seconds):
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}m{secs:02d}s"
        else:
            hrs = seconds // 3600
            mins = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hrs}h{mins:02d}m{secs:02d}s"

    sdat_counts = {}
    for line in lines:
        parts = line.rstrip('\n').split('|')
        if len(parts) < 4:
            continue
        _, INF_path, _, INF_cachename = parts[:4]
        if INF_path.lower().endswith('.sdat'):
            k = INF_cachename.lower()
            sdat_counts[k] = sdat_counts.get(k, 0) + 1

    scene_cache_missing = scene_cache_folder is not None and not os.path.isdir(
        scene_cache_folder.split("|")[0] if unlimited_all and "|" in scene_cache_folder else scene_cache_folder
    )

    cache_lines = []
    for line in lines:
        parts = line.rstrip('\n').split('|')
        cache_lines.append(parts[3].lower() if len(parts) >= 4 else None)

    curr_cache = None
    curr_cache_start = start_time if start_time is not None else time.time()
    prev_cache_name = None

    printed_stats_for_current = False

    for idx, (line_num, line) in enumerate(zip(range(1, len(lines)+1), lines)):
        parts = line.rstrip('\n').split('|')
        if len(parts) < 4:
            if debug:
                dbg("Skipping line %d (too few fields): %r", line_num, line)
            continue
        INF_hash, INF_path, INF_date, INF_cachename = parts[:4]
        inf_cachename_lc = INF_cachename.lower()

        if unlimited_all and inf_cachename_lc != curr_cache:
            if curr_cache is not None:
                now = time.time()
                delta = now - curr_cache_start
                print(f"({infcachename_counter-1}) {prev_cache_name} ~ stats : sdats = {sdat_counts.get(curr_cache, 0)} / time taken = {human_time(delta)}")
                printed_stats_for_current = True
            elapsed = time.time() - start_time if start_time is not None else 0
            elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            print(f"({infcachename_counter}) ({elapsed_str}) logging {INF_cachename} ...")
            curr_cache = inf_cachename_lc
            curr_cache_start = time.time()
            prev_cache_name = INF_cachename
            infcachename_counter += 1
            printed_stats_for_current = False

        cache_out = INF_cachename if unlimited_all else (cachename if cachename is not None else INF_cachename)

        if not (INF_path.lower().endswith('.sdat') or INF_path.lower().endswith('.bar')):
            continue

        split_path = split_inf_path(INF_path)
        is_scene, which = find_scenes_fields(split_path)
        if not is_scene:
            continue

        K, L, M, N, O, P, Q, R, S = split_path

        if INF_path.lower().endswith('.bar'):
            version_field = "n/a"
        elif unlimited_all:
            if scene_cache_folder:
                sdat_file = find_sdat_file_unlimited(scene_cache_folder, INF_cachename, INF_hash, debug)
            else:
                sdat_file = None
            if sdat_file is None:
                version_field = "n/a"
            else:
                size = get_file_size(sdat_file)
                version_field = get_sdata_version(sdat_file, size)
        elif cachename is None:
            version_field = "n/a"
        elif scene_cache_folder is None or scene_cache_missing:
            version_field = "n/a"
        elif cachename.lower() != INF_cachename.lower():
            version_field = "n/a"
        else:
            if sdat_index is not None:
                sdat_file = find_sdat_file_from_index(sdat_index, INF_hash)
            else:
                sdat_file = None
            if sdat_file is None:
                version_field = "n/a"
            else:
                size = get_file_size(sdat_file)
                version_field = get_sdata_version(sdat_file, size)

        if which == "O":
            if M.lower() == 'cds':
                field4 = L.rstrip('/')
            elif M.lower() == 'dev':
                field4 = f"{L.rstrip('/')}.{M.rstrip('/')}"
            else:
                field4 = M.rstrip('/')
            field5 = N.rstrip('/')
            scene = P.rstrip('/')
            fname_wo_ext = get_fname_without_ext(Q)
            ext = get_ext(Q)
            sdatname = f"{scene}${fname_wo_ext}"
        else:
            field4 = f"{L.rstrip('/')}.{N.rstrip('/')}"
            field5 = O.rstrip('/')
            scene = Q.rstrip('/')
            fname_wo_ext = get_fname_without_ext(R)
            ext = get_ext(R)
            sdatname = f"{scene}${fname_wo_ext}"

        log_func('\t'.join([
            cache_out,
            INF_hash,
            INF_date,
            field4,
            field5,
            scene,
            fname_wo_ext,
            ext,
            version_field,
            sdatname
        ]))
        found = True

    if unlimited_all and curr_cache is not None and curr_cache_start is not None and not printed_stats_for_current:
        now = time.time()
        delta = now - curr_cache_start
        print(f"({infcachename_counter-1}) {prev_cache_name} ~ stats : sdats = {sdat_counts.get(curr_cache, 0)} / time taken = {human_time(delta)}")

    return found


def main():
    usage = (
        "Usage: log_sdats.py <inf_file_path> <sdat_log> "
        "[--cachename <cachename>] "
        "[--objects <literalpath>/<rootdir|substr>] "
        "[--scenes <literalpath>/<rootdir|substr>] "
        "[--unlimited_all] "
        "[--debug]"
    )
    if len(sys.argv) < 3:
        print(usage)
        sys.exit(1)

    inf_file = sys.argv[1]
    log_file = sys.argv[2]
    args = sys.argv[3:]

    cachename = None
    idx = 0
    unlimited_all = False

    if len(args) >= 2 and args[0] == '--cachename':
        cachename = args[1]
        idx = 2
    elif args and args[0] == '--cachename':
        print("ERROR: --cachename requires a value.")
        sys.exit(1)

    object_cache_folder = None
    scene_cache_folder = None
    process_objects_flag = False
    process_scenes_flag = False
    debug = False

    while idx < len(args):
        if args[idx] == '--objects':
            process_objects_flag = True
            if idx + 1 < len(args) and not args[idx + 1].startswith('--'):
                object_cache_folder = args[idx + 1]
                idx += 2
            else:
                object_cache_folder = None
                idx += 1
        elif args[idx] == '--scenes':
            process_scenes_flag = True
            if idx + 1 < len(args) and not args[idx + 1].startswith('--'):
                scene_cache_folder = args[idx + 1]
                idx += 2
            else:
                scene_cache_folder = None
                idx += 1
        elif args[idx] == '--unlimited_all':
            unlimited_all = True
            idx += 1
        elif args[idx] == '--debug':
            debug = True
            idx += 1
        else:
            print(f"ERROR: Unrecognized flag '{args[idx]}'\n{usage}")
            sys.exit(1)

    if not process_objects_flag and not process_scenes_flag:
        print("ERROR: Must specify at least --objects or --scenes")
        sys.exit(1)

    if not os.path.isfile(inf_file):
        print(f"Input file {inf_file} does not exist")
        sys.exit(1)

    with open(inf_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

    object_lines = [l for l in all_lines if '/objects/' in l.lower()]
    scene_lines  = [l for l in all_lines if '/scenes/' in l.lower()]

    sdat_index_objects = None
    sdat_index_scenes = None

    if not unlimited_all:
        if process_objects_flag and object_cache_folder:
            sdat_index_objects = build_sdat_index(object_cache_folder)
        if process_scenes_flag and scene_cache_folder:
            sdat_index_scenes = build_sdat_index(scene_cache_folder)
    else:
        if debug:
            dbg("Unlimited_all mode active. objects=%r scenes=%r", object_cache_folder, scene_cache_folder)

    any_logged = False
    output_lines = []
    def cache_log(x):
        output_lines.append(x)

    start_time = time.time()

    if process_objects_flag:
        found_obj = process_objects(
            object_lines, cache_log, cachename=cachename, debug=debug,
            object_cache_folder=object_cache_folder, sdat_index=sdat_index_objects,
            unlimited_all=unlimited_all, start_time=start_time
        )
        any_logged = any_logged or found_obj

    if process_scenes_flag:
        found_scn = process_scenes(
            scene_lines, cache_log, cachename=cachename, debug=debug,
            scene_cache_folder=scene_cache_folder, sdat_index=sdat_index_scenes,
            unlimited_all=unlimited_all, start_time=start_time
        )
        any_logged = any_logged or found_scn

    if any_logged:
        with open(log_file, 'w', encoding='utf-8') as f_out:
            for out_line in output_lines:
                f_out.write(out_line + '\n')
        if debug:
            dbg("Log file created: %s", log_file)
    else:
        if debug:
            dbg("No .sdat/.bar objects or scenes found; no log file created.")

if __name__ == "__main__":
    main()

