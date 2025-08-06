import os
import shutil
import subprocess
import sys
import hashlib
import logging
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, UnidentifiedImageError

DEBUG_ENABLED = False
VERBOSE_MODE = False
CUSTOM_QUERY_MODE = False
OVERRIDE_LOG_PATH = None
OVERRIDE_NEW_MODE = False
OVERRIDE_NEW_LOG = None 
any_processed = False
started_processing = False
exceptions_modified_file = None
exceptions_corrupt_file = None
OVERRIDE_MODE = "0"
copied_count = 0
corrupt_count = 0
modified_count = 0
dupe_count = 0
multiple_matched_dat_files = 0

FOLDER_RENAMES = {
    "scee": "scee-home.playstation.net",
    "scea": "scea-home.playstation.net",
    "scej": "scej-home.playstation.net",
    "sceasia": "sceasia-home.playstation.net"
}

def rename_root_folders(base_dir):
    for subfolder in ["", "corrupted", "modified"]:
        path = Path(base_dir) / subfolder if subfolder else Path(base_dir)
        if not path.exists() or not path.is_dir():
            continue
        for entry in path.iterdir():
            if entry.is_dir() and entry.name in FOLDER_RENAMES:
                new_path = entry.parent / FOLDER_RENAMES[entry.name]
                try:
                    dbg("Renaming %s -> %s", entry, new_path)
                    entry.rename(new_path)
                except Exception as e:
                    dbg(f"Failed to rename {entry} -> {new_path}: {e}")

def dbg(msg, *args):
    if DEBUG_ENABLED:
        message = msg % args if args else msg
        debug_log.write(f"[{target_cachename}] {message}\n")
        debug_log.flush()

# === FILE ANALYSIS FUNCTIONS START ===

def get_file_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension

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

def calculate_sha1(file_path):
    try:
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                sha1.update(chunk)
        return sha1.hexdigest().upper()
    except Exception as e:
        dbg("Error calculating SHA1: %s", e)
        return "ERROR"

def is_image_corrupt(filepath):
    try:
        with Image.open(filepath) as img:
            img.verify()
        with Image.open(filepath) as img:
            img.load()
    except (IOError, SyntaxError, UnidentifiedImageError, ValueError, AttributeError):
        return 1
    return 0

SPECIFIC_ERRORS = [
    "moov atom not found",
    "contradictory STSC and STCO",
    "error reading header",
    "Invalid data found when processing input",
    "corrupt",
    "error",
    "invalid",
    "malformed",
    "missing",
    "missing picture in access unit with size 5",
    "partial file"
]

def log_and_print(message, log_only=True):
    logging.info(message)

def extract_error_summary(output):
    detailed_lines = []
    for line in output.splitlines():
        for error in SPECIFIC_ERRORS:
            if error.lower() in line.lower():
                if line not in detailed_lines:
                    detailed_lines.append(line)
    return detailed_lines

def analyze_video(file_path, ffprobe_path, log_path=None, inf_url=None):
    def log_if_corrupt(detailed_lines, log_path):
        if not detailed_lines or not log_path:
            return False
        logger = logging.getLogger()
        if not logger.hasHandlers():
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            logging.basicConfig(filename=log_path, level=logging.INFO, format='%(message)s')
        return True

    cmd = [
        ffprobe_path,
        '-v', 'error',
        '-show_entries', 'format',
        '-show_entries', 'stream',
        '-show_entries', 'frame',
        '-print_format', 'json',
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    detailed_lines = extract_error_summary(result.stderr)

    if detailed_lines:
        relative_path = os.path.relpath(file_path, os.getcwd())
        if log_if_corrupt(detailed_lines, log_path):
            if inf_url:
                log_and_print(f"{inf_url}")
            log_and_print(f"{relative_path}:")
            if len(detailed_lines) == 1 and "missing picture in access unit with size 5" in detailed_lines[0]:
                log_and_print("Only error found is 'missing picture in access unit with size 5'. Skipping...")
                log_and_print("-----------------------------------------------")
                return 0
            for line in detailed_lines:
                log_and_print(f"{line}")
            log_and_print("-----------------------------------------------")
        return 1

    return 0

ROOT_TAGS = [
    "commerce_point", "XML", "xml", "REGIONINFO", "rss", "RSS", "LOCALISATION",
    "eula", "active_objects", "videos", "media", "WEATHER", "TICKER"
]

XML_PATTERNS = {
    tag.lower(): (
        re.compile(rf"<\s*{tag.lower()}\b[^>]*\/\s*>", re.IGNORECASE),  # self-closing
        re.compile(rf"<\s*{tag.lower()}\b[^>]*>", re.IGNORECASE),       # open
        re.compile(rf"</\s*{tag.lower()}\s*>", re.IGNORECASE),          # close
    )
    for tag in ROOT_TAGS
}

def is_xml_corrupt(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content_lower = f.read().lower()

        for tag_lc, (self_close, open_tag, close_tag) in XML_PATTERNS.items():
            if self_close.search(content_lower):
                return 0
            if open_tag.search(content_lower) and close_tag.search(content_lower):
                return 0
            elif open_tag.search(content_lower):
                return 1
        return 0
    except Exception:
        return 1

# === FILE ANALYSIS FUNCTIONS END ===

def get_file_info(file_path, ffprobe_path, archive_root, queryname, cachename, inf_url=None):
    ext = get_file_extension(file_path)
    ext_lc = ext.lower()
    
    size = get_file_size(file_path)
    
    sdatver = -1
    if ext_lc == '.sdat':
        ver = get_sdata_version(file_path, size)
        try:
            sdatver = float(ver)
        except (ValueError, TypeError):
            sdatver = -1

    sha1 = calculate_sha1(file_path)

    imgcor = "NA"
    if ext_lc in ['.png', '.jpg', '.jpeg', '.dds']:
        imgcor = is_image_corrupt(file_path)

    vidcor = "NA"
    if ext_lc in ['.mp4', '.m4v']:
        if not os.path.exists(ffprobe_path):
            dbg("Warning: ffprobe path is invalid or missing: %s", ffprobe_path)
            vidcor = -1
        else:
            if CUSTOM_QUERY_MODE:
                log_path = os.path.join(archive_root, "ARCHIVE", queryname, cachename, "log_VIDEO_ANALYSIS.log")
            else:
                log_path = os.path.join(archive_root, "ARCHIVE", "log_VIDEO_ANALYSIS.log")

            vidcor = analyze_video(file_path, ffprobe_path, log_path=log_path, inf_url=inf_url)

    xmlcor = "NA"
    if ext_lc == '.xml':
        xmlcor = is_xml_corrupt(file_path)

    return {
        'ext': ext,
        'size': size,
        'sdatver': sdatver,
        'sha1': sha1,
        'imgcor': imgcor if imgcor != "NA" else -1,
        'vidcor': vidcor if vidcor != "NA" else -1,
        'xmlcor': xmlcor if xmlcor != "NA" else -1
    }

def ensure_dir(path):
    dbg("Ensuring directory exists: %s", path)
    os.makedirs(path, exist_ok=True)

def construct_full_target_path(archive_root, queryname, cachename, special_path):

    if CUSTOM_QUERY_MODE:
        full_path = Path(archive_root) / "ARCHIVE" / queryname / cachename / special_path
    else:
        full_path = Path(archive_root) / "ARCHIVE" / special_path 
        
    dbg("Constructed full target path: %s", full_path)
    return full_path

def copy_file(src, dst, message="", inf_fields=None, special_path=None, log_override=True):
    global copied_count, OVERRIDE_NEW_LOG

    dbg("Copying from %s to %s", src, dst)

    if VERBOSE_MODE:
        log_line = f"[VERBOSE] COPIED {copied_count + 1} {message}"
    else:
        ensure_dir(os.path.dirname(dst))
        shutil.copy2(src, dst)
        log_line = f"COPIED {copied_count + 1} {message}"

    copied_count += 1

    print(log_line)

    if DEBUG_ENABLED:
        debug_log.write(f"[{target_cachename}] {log_line}\n")
        debug_log.flush()

    if OVERRIDE_NEW_MODE and log_override and inf_fields and special_path is not None:
        if len(inf_fields) >= 4:
            if OVERRIDE_NEW_LOG is None:
                os.makedirs(os.path.dirname(OVERRIDE_LOG_PATH), exist_ok=True)
                OVERRIDE_NEW_LOG = open(OVERRIDE_LOG_PATH, 'a', encoding='utf-8')
            OVERRIDE_NEW_LOG.write(f"{inf_fields[0]}|{special_path}|{inf_fields[2]}|{inf_fields[3]}\n")
            OVERRIDE_NEW_LOG.flush()
            
def incremental_copy(src, dst, override, ffprobe_path):
    dst = Path(dst)
    dir_name = dst.parent
    base = dst.stem
    ext = dst.suffix

    original_target = dir_name / f"{base}{ext}"

    if override == "1":
        dbg("Override is 1, using original path: %s", original_target)
        cor_old = {'fileext': '', 'filesize': -1, 'sha1': ''}
        if original_target.exists():
            info = get_file_info(str(original_target), ffprobe_path, archive_root, queryname, cachename)
            if info:
                cor_old = {
                    'fileext': info['ext'],
                    'filesize': info['size'],
                    'sha1': info['sha1']
                }
        return str(original_target), cor_old

    if not original_target.exists():
        dbg("Original target doesn't exist, using it directly: %s", original_target)
        return str(original_target), {'fileext': '', 'filesize': -1, 'sha1': ''}

    dbg("Finding unique target for duplicate: %s", original_target)
    counter = -1
    while True:
        candidate = dir_name / f"{base}{counter}{ext}"
        if not candidate.exists():
            break
        counter -= 1

    final_target = dir_name / f"{base}{counter}{ext}"
    dbg("Using fallback path: %s", final_target)
    return str(final_target), {'fileext': '', 'filesize': -1, 'sha1': ''}

def update_log_file_entry(logfile, special_path, date, with_x=False):
    # Ensures ONLY one entry per special_path, updated with x if needed
    lines = []
    found = False
    if os.path.exists(logfile):
        with open(logfile, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(f"{special_path}\t"):
                    found = True
                    line = f"{special_path}\t{date}" + ("\tx" if with_x else "")
                else:
                    line = line.rstrip('\n')
                lines.append(line)
    if not found:
        line = f"{special_path}\t{date}" + ("\tx" if with_x else "")
        lines.append(line)
    with open(logfile, 'w', encoding='utf-8') as f:
        for l in lines:
            f.write(l + '\n')

def process_inf_line(line, archive_root, search_root, queryname, cachename, ffprobe_path, nofileforinf_file, dupes_file, cdnfiles_file, dcfiles_file, exceptions_modified_set=None, exceptions_corrupt_set=None):
    global copied_count, corrupt_count, modified_count, dupe_count, multiple_matched_dat_files
    parts = line.strip().split('|')
    if len(parts) < 4:
        return
    if cachename and cachename.strip() and parts[3].strip().lower() != cachename.strip().lower():
        return

    dbg("Processing line: %s", line.strip())
    
    if not cachename or not cachename.strip():
        cachename = parts[3].strip()
    
    c, d, raw_date, _ = parts[:4]

    DATE_MAP = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
    }

    parsed_date = "null"
    parsed_date_dcfile = "null" 
    if raw_date and raw_date.lower() != "null":
        try:
            day = raw_date[:2]
            month_str = raw_date[2:5]
            year = raw_date[5:]
            month = DATE_MAP.get(month_str, "??")
            if month != "??":
                parsed_date = f"{year}-{month}-{day}"
                parsed_date_dcfile = f"{year}{month}{day}"
        except Exception as e:
            dbg("Failed to parse date '%s': %s", raw_date, e)

    inf_url = d
    ext = Path(inf_url).suffix
    inf_url_parts = inf_url.split('/')
    inf_url_host = inf_url_parts[0].lower() if inf_url_parts else ""
    
    dbg("Parsed inf_url_host: %s", inf_url_host)
    
    root_folder_map = {
        "scee": "scee-home.playstation.net",
        "scea": "scea-home.playstation.net",
        "scej": "scej-home.playstation.net",
        "sceasia": "sceasia-home.playstation.net"
    }
    
    crackle_domains = {
        "images-us-az.crackle.com",
        "images.crackle.com",
        "images2.crackle.com",
        "images3.crackle.com",
        "dl.dropbox.com",
    }
    
    if inf_url_host in crackle_domains:
        if ext.lower() in ['.jpg', '.png']:
            inf_url = d
        elif '.jpgts=' in d.lower():
            inf_url = d.split('=')[0].replace('.jpgts', '.jpg')
        elif '.jpgdl=' in d.lower():
            inf_url = d.split('=')[0].replace('.jpgdl', '.jpg')
        else:
            inf_url = d
    
    elif inf_url.startswith("web/secureobjectroot/") or inf_url.startswith("secureobjectroot/"):
        inf_url = d.replace("web/secureobjectroot/", "secure.cprod.homeps3.online.scee.com/objects/").replace("secureobjectroot/", "secure.cprod.homeps3.online.scee.com/objects/")
    
    elif inf_url.startswith("web/securesceneroot/") or inf_url.startswith("securesceneroot/"):
        inf_url = d.replace("web/securesceneroot/", "secure.cprod.homeps3.online.scee.com/scenes/").replace("securesceneroot/", "secure.cprod.homeps3.online.scee.com/scenes/")
    
    elif inf_url_host in root_folder_map:
        inf_url = d.replace(inf_url_host + "/", root_folder_map[inf_url_host] + "/", 1)

    elif inf_url_host.startswith("avatar-") and inf_url_host.endswith(".jpg"):
        inf_url = f"img-profile-avatars/{d}"
        
    elif inf_url_host.startswith("vers_") and inf_url_host.endswith(".xml"):
        inf_url = f"xml-scene-versions/{d}"
        
    elif inf_url_host.startswith("npwr00432") and inf_url_host.endswith(".xml"):
        inf_url = f"xml-clubhouses/{d}"
        
    elif inf_url_host.startswith("profanity") and inf_url_host.endswith(".bin"):
        inf_url = f"bin-profanityfilters/{d}"
        
    elif inf_url_host.startswith("profile-"):
        inf_url = f"xml-profile/{d}"
        
    elif inf_url_host.startswith("npia00005-"):
        inf_url = f"xml-clubhouses/{d}"
        
    elif inf_url_host.startswith("inventory-") and inf_url_host.endswith(".xml"):
        inf_url = f"xml-inventory/{d}"
        
    elif inf_url_host == "data":
        inf_url = f"tss-data/{d}"

    else:
        FLICKR_FARMS = [f"farm{i}.staticflickr.com" for i in range(1, 10)]
        if inf_url_host in FLICKR_FARMS:
            corrected_host = inf_url_host.replace("staticflickr.com", "static.flickr.com")
            dbg("Correcting Flickr host: %s -> %s", inf_url_host, corrected_host)
            inf_url = d.replace(inf_url_host, corrected_host, 1)
            inf_url_host = corrected_host
        else:
            dbg("No correction needed for host: %s", inf_url_host)

    special_path = inf_url.strip('/')
    
    dbg("Searching for %s_DAT*", c)
    dat_files = [f for f in Path(search_root).rglob(f"{c}_DAT*") if f.is_file()]
    dbg("Found %d file(s) for %s_DAT*", len(dat_files), c)

    if len(dat_files) > 1:
        multiple_matched_dat_files += 1

    if not dat_files:
        dbg("No DAT files found for %s, logging to nofiles", c)
        with open(nofileforinf_file, 'a', encoding='utf-8', errors='ignore') as nf:
            nf.write(f"{cachename}\t{c}_INF\t{special_path}\n")
        return
        
    for file in dat_files:
        dbg("Analyzing file: %s", file)
    
        if file.suffix == "":
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    chunk = f.read(2048).strip()
                chunk_lower = chunk.lower()
                if chunk.startswith('{') or chunk.startswith('['):
                    if not inf_url.endswith('.json'):
                        inf_url += ".json"
                        special_path += ".json"
                        dbg("[EXTENSIONLESS] Patched path .json : %s", file)
                elif chunk.startswith('<'):
                    if (
                        '<xml' in chunk_lower or 
                        any(tag in chunk_lower for tag in ['<?xml', '<rss', '<profile'])
                    ):
                        if not inf_url.endswith('.xml'):
                            inf_url += ".xml"
                            special_path += ".xml"
                            dbg("[EXTENSIONLESS] Patched path with .xml : %s", file)
            except Exception as e:
                dbg("Failed to detect type for extensionless file %s: %s", file, e)
    
        normal_target = construct_full_target_path(archive_root, queryname, cachename, special_path)
        info = get_file_info(str(file), ffprobe_path, archive_root, queryname, cachename, inf_url=inf_url)
        if not info:
            continue
    
        ext_lc = Path(normal_target).suffix.lower()
        sha1 = info['sha1']
        size = info['size']
        sdatver = info['sdatver']
        imgcor = info['imgcor']
        vidcor = info['vidcor']
        xmlcor = info.get('xmlcor', 0)
        
        dupe_file_path = str(file)
        if archive_root and dupe_file_path.startswith(str(archive_root)):
            dupe_file_path = dupe_file_path[len(str(archive_root)):].lstrip("\\/")

        force_corrupt = exceptions_corrupt_set and sha1 in exceptions_corrupt_set
        force_modified = exceptions_modified_set and sha1 in exceptions_modified_set
        
        # ----- CORRUPT FILE -----
        is_corrupt = force_corrupt or size == 0 or sdatver == 0 or imgcor == 1 or vidcor == 1 or xmlcor == 1
        if is_corrupt:
       
            if force_corrupt:
                dbg(f"[CORRUPT] {cachename}/{special_path} ( {sha1} )")
                
            corrupt_target = construct_full_target_path(archive_root, queryname, cachename, f"corrupted/{special_path}")
            
            if Path(corrupt_target).exists():
                cor_old = get_file_info(str(corrupt_target), ffprobe_path, archive_root, queryname, cachename)
                if cor_old and sha1 != cor_old['sha1'] and size > cor_old['size']:
                    final_target, _ = incremental_copy(str(file), str(corrupt_target), "1", ffprobe_path)
                    copy_file(file, final_target, f"{cachename}/corrupted/{special_path} - CORRUPT ( NEW FILE SIZE )", parts, special_path, log_override=False)
                    corrupt_count += 1
            else:
                final_target, _ = incremental_copy(str(file), str(corrupt_target), "1", ffprobe_path)
                copy_file(file, final_target, f"{cachename}/corrupted/{special_path} - CORRUPT", parts, special_path, log_override=False)
                corrupt_count += 1
            continue
            
        # ----- MODIFIED FILE -----
        is_modified = force_modified or sdatver == 3.3
        if is_modified:
     
            if force_modified:
                dbg(f"[MODIFIED] {cachename}/{special_path} ( {sha1} )")
                
            mod_target = construct_full_target_path(archive_root, queryname, cachename, f"modified/{special_path}")
            
            final_target, cor_old = incremental_copy(str(file), str(mod_target), "0", ffprobe_path)
            if sha1 != cor_old['sha1']:
                copy_file(file, final_target, f"{cachename}/modified/{special_path} - MODIFIED", parts, special_path, log_override=False)
                modified_count += 1
            continue

        # ----- ODC/SDC -----
        if ext_lc in {'.odc', '.sdc'}:
            if parsed_date_dcfile == "null":
                dbg(f"[DCFILES] Skipping: {file} (date is null)")
                continue
        
            dbg(f"[DCFILES] Processing: {dupe_file_path} (parsed_date: {parsed_date_dcfile}, special_path: {special_path})")
            existing_date = None
            if os.path.exists(dcfiles_file):
                dbg(f"[DCFILES] Looking for previous date in {dcfiles_file} for {special_path}")
                with open(dcfiles_file, encoding='utf-8') as dc:
                    for l in dc:
                        parts = l.strip().split('\t')
                        if len(parts) >= 2 and parts[0] == special_path:
                            existing_date = parts[1]
                            dbg(f"[DCFILES] Found existing date for {special_path}: {existing_date}")
                            break
        
            should_copy = False
            if normal_target.exists():
                dbg(f"[DCFILES] Target file exists: {normal_target}")
                old_info = get_file_info(str(normal_target), ffprobe_path, archive_root, queryname, cachename)
                if old_info and old_info['sha1'] == sha1:
                    dbg(f"[DCFILES] SHA1 matches for {normal_target}, logging as dupe.")
                    with open(dupes_file, 'a', encoding='utf-8') as dup:
                        dup.write(f"{cachename}\t{file}\t{special_path}\n")
                    dupe_count += 1
                    continue
                elif old_info and old_info['sha1'] != sha1:
                    dbg(f"[DCFILES] SHA1 differs (new: {sha1}, old: {old_info['sha1']})")
                    if existing_date is None or parsed_date_dcfile > existing_date:
                        dbg(f"[DCFILES] Date is newer or no previous date (parsed: {parsed_date_dcfile}, existing: {existing_date})")
                        should_copy = True
                    else:
                        dbg(f"[DCFILES] Date is not newer (parsed: {parsed_date_dcfile}, existing: {existing_date}), not copying.")
                        continue
            else:
                dbg(f"[DCFILES] Target file does not exist. Will copy.")
                should_copy = True
        
            if should_copy:
                dbg(f"[DCFILES] Copying file: {dupe_file_path} -> {normal_target}")
                if existing_date is None:
                    copy_file(
                        file, str(normal_target),
                        f"{cachename}/{special_path}",
                        parts, special_path
                    )
                    with open(dcfiles_file, 'a', encoding='utf-8') as dc:
                        dc.write(f"{special_path}\t{parsed_date_dcfile}\n")
                else:
                    copy_file(
                        file, str(normal_target),
                        f"{cachename}/{special_path} ( NEWER DATE {parsed_date_dcfile} )",
                        parts, special_path
                    )
                    with open(dcfiles_file, 'a', encoding='utf-8') as dc:
                        dc.write(f"{special_path}\t{parsed_date_dcfile}\tx\n")
            continue

            
        # ----- XML/JSON/TXT/HCDB/BAR/SHARC/BIN -----
        if ext_lc in {'.xml', '.json', '.txt', '.hcdb', '.bar', '.sharc', '.bin'}:
            target_dir = normal_target.parent
            stem = normal_target.stem
            suffix = normal_target.suffix
            has_date = parsed_date != "null"
            date_str = parsed_date if has_date else ""
            dupe_fmt = (f"{stem}_{parsed_date}-{{}}{suffix}" if has_date else f"{stem}-{{}}{suffix}")
        
            candidates = []
            if has_date:
                main_file = target_dir / f"{stem}_{parsed_date}{suffix}"
            else:
                main_file = target_dir / f"{stem}{suffix}"
            candidates.append(main_file)
            for n in range(1, 500):
                candidates.append(target_dir / dupe_fmt.format(n))
        
            incoming_sha1 = sha1
            dbg(f"[CDNFILES] Incoming SHA1: {incoming_sha1}")
            found_sha1 = None
            found_slot = None
            slot_sha1s = []
            for slot in candidates:
                if slot.exists():
                    info = get_file_info(str(slot), ffprobe_path, archive_root, queryname, cachename)
                    slot_sha1s.append((str(slot), info['sha1']))
                    if info['sha1'] == incoming_sha1:
                        found_sha1 = info['sha1']
                        found_slot = slot
                        break
            for p, sh in slot_sha1s:
                dbg(f"[CDNFILES] Candidate: {p} SHA1: {sh}")
        
            if found_sha1:
                dbg(f"[CDNFILES] SHA1 matched existing slot: {found_slot} (Dupe, not copying again)")
                with open(dupes_file, 'a', encoding='utf-8') as dup:
                    dup.write(f"{cachename}\t{dupe_file_path}\t{special_path}\n") 
                dupe_count += 1
                continue
        
            if has_date:
                found_cdn_date = None
                found_cdn_x = False
                parsed_yymmdd = parsed_date_dcfile if parsed_date_dcfile != "null" else ""
                filedate_str = f"{parsed_yymmdd[:4]}-{parsed_yymmdd[4:6]}-{parsed_yymmdd[6:8]}" if len(parsed_yymmdd) == 8 else parsed_date
                main_file = target_dir / f"{stem}{suffix}"
                date_file = target_dir / f"{stem}_{filedate_str}{suffix}"
            
                if os.path.exists(cdnfiles_file):
                    with open(cdnfiles_file, 'r', encoding='utf-8') as cdn:
                        for l in cdn:
                            parts = l.rstrip('\n').split('\t')
                            if len(parts) >= 2 and parts[0] == special_path:
                                found_cdn_date = parts[1]
                                if len(parts) == 3 and parts[2].lower() == "x":
                                    found_cdn_x = True
                                break
            
                dupe_found = False
                dupe_slots = [main_file, date_file] + [
                    target_dir / f"{stem}_{filedate_str}-{n}{suffix}" for n in range(1, 100)
                ]
                for slot in dupe_slots:
                    if slot.exists():
                        info = get_file_info(str(slot), ffprobe_path, archive_root, queryname, cachename)
                        if info and info['sha1'] == sha1:
                            with open(dupes_file, 'a', encoding='utf-8') as dup:
                                dup.write(f"{cachename}\t{dupe_file_path}\t{special_path}\n")
                            dupe_count += 1
                            dbg(f"[CDNFILES] Found SHA1 match at {slot}, skipping copy")
                            dupe_found = True
                            break
                if dupe_found:
                    continue
            
                if found_cdn_date is None:
                    copy_file(file, str(main_file), f"{cachename}/{Path(main_file).relative_to(Path(archive_root) / 'ARCHIVE').as_posix()}", parts, special_path)
                    dbg(f"[CDNFILES] Copied to main (first dated file): {main_file}")
                    update_log_file_entry(cdnfiles_file, special_path, parsed_yymmdd, with_x=False)
                    dbg(f"[CDNFILES] CDN log updated: {special_path}\t{parsed_yymmdd}")
            
                elif parsed_yymmdd > found_cdn_date:
                    olddate_filedate = (
                        f"{found_cdn_date[:4]}-{found_cdn_date[4:6]}-{found_cdn_date[6:8]}"
                        if found_cdn_date and len(found_cdn_date) == 8 else found_cdn_date
                    )
                    old_dated_file = target_dir / f"{stem}_{olddate_filedate}{suffix}"
                    if main_file.exists():
                        if old_dated_file.exists():
                            for n in range(1, 500):
                                dupe_file = target_dir / f"{stem}_{olddate_filedate}-{n}{suffix}"
                                if not dupe_file.exists():
                                    main_file.rename(dupe_file)
                                    dbg(f"[CDNFILES] Renamed existing main to: {dupe_file}")
                                    break
                        else:
                            main_file.rename(old_dated_file)
                            dbg(f"[CDNFILES] Renamed existing main to: {old_dated_file}")
                    copy_file(file, str(main_file), f"{cachename}/{Path(main_file).relative_to(Path(archive_root) / 'ARCHIVE').as_posix()} ( UNIQUE DUPE WITH NEW DATE {parsed_yymmdd} )", parts, special_path)
                    dbg(f"[CDNFILES] Copied to main (newer date): {main_file}")
                    update_log_file_entry(cdnfiles_file, special_path, parsed_yymmdd, with_x=True)
                    dbg(f"[CDNFILES] CDN log updated: {special_path}\t{parsed_yymmdd}\tx")
            
                else:
                    dupe_target = date_file
                    if dupe_target.exists():
                        for n in range(1, 500):
                            candidate = target_dir / f"{stem}_{filedate_str}-{n}{suffix}"
                            if not candidate.exists():
                                dupe_target = candidate
                                break
                    copy_file(file, str(dupe_target), f"{cachename}/{Path(dupe_target).relative_to(Path(archive_root) / 'ARCHIVE').as_posix()}  ( UNIQUE DUPE )", parts, special_path)
                    dbg(f"[CDNFILES] Saved as dupe: {dupe_target}")
            
                continue


            else:
                if not main_file.exists():
                    copy_file(file, str(main_file), f"{cachename}/{Path(main_file).relative_to(Path(archive_root) / 'ARCHIVE').as_posix()}", parts, special_path)
                    dbg(f"[CDNFILES] Copied to main (undated): {main_file}")
                    update_log_file_entry(cdnfiles_file, special_path, "", with_x=False)
                    dbg(f"[CDNFILES] CDN log updated (undated): {special_path}")
                else:
                    for slot in candidates[1:]:
                        if not slot.exists():
                            copy_file(file, str(slot), f"{cachename}/{Path(main_file).relative_to(Path(archive_root) / 'ARCHIVE').as_posix()} ( UNIQUE DUPE )", parts, special_path)
                            dbg(f"[CDNFILES] Saved as dupe: {slot}")
                            break
                continue

        # ----- MP3 FILES -----
        if ext_lc == '.mp3':
            if normal_target.exists():
                old_info = get_file_info(str(normal_target), ffprobe_path, archive_root, queryname, cachename)
                if old_info:
                    if sha1 == old_info['sha1']:
                        dbg(f"[MP3] SHA1 match for {dupe_file_path} and {normal_target}. Logging as dupe.")
                        with open(dupes_file, 'a', encoding='utf-8') as dup:
                            dup.write(f"{cachename}\t{dupe_file_path}\t{special_path}\n")
                        dupe_count += 1
                        continue
                    if size > old_info['size']:
                        dbg(f"[MP3] SHA1 differs and new file is bigger ({size}>{old_info['size']}). Overwriting file.")
                        copy_file(file, str(normal_target), f"{cachename}/{special_path} - {ext_lc} ( NEW FILE SIZE )", parts, special_path)
                        continue
                    else:
                        dbg(f"[MP3] SHA1 differs and new file is NOT bigger ({size}<={old_info['size']}). Skipping copy.")
                        continue
            copy_file(file, str(normal_target), f"{cachename}/{special_path} - {ext_lc}", parts, special_path)
            continue
            
        # ----- OVERRIDE MODE: SDAT, BAR, PNG  -----
        if OVERRIDE_NEW_MODE and ext_lc in {'.sdat', '.bar', '.png'}:
            if normal_target.exists():
                old_info = get_file_info(str(normal_target), ffprobe_path, archive_root, queryname, cachename)
                if old_info:
                    if sha1 == old_info['sha1']:
                        dbg(f"[OVERRIDE] SHA1 match for {dupe_file_path} and {normal_target}. Logging as dupe.")
                        with open(dupes_file, 'a', encoding='utf-8') as dup:
                            dup.write(f"{cachename}\t{dupe_file_path}\t{special_path}\n")
                        dupe_count += 1
                        continue
                    if size > old_info['size']:
                        dbg(f"[OVERRIDE] SHA1 differs and new file is bigger ({size}>{old_info['size']}). Overwriting file.")
                        copy_file(file, str(normal_target), f"{cachename}/{special_path} - {ext_lc} ( NEW FILE SIZE )", parts, special_path)
                        continue
                    else:
                        dbg(f"[OVERRIDE] SHA1 differs and new file is NOT bigger ({size}<={old_info['size']}). Skipping copy.")
                        continue
            copy_file(file, str(normal_target), f"{cachename}/{special_path} - {ext_lc}", parts, special_path)
            continue

        # ----- ALL OTHER FILES -----
        if normal_target.exists():
            dbg(f"[OTHER] {normal_target} exists. Checking for SHA1/size.")
            old_info = get_file_info(str(normal_target), ffprobe_path, archive_root, queryname, cachename)
            if old_info and old_info['sha1'] == sha1:
                dbg(f"[OTHER] SHA1 match. Logging as dupe. File: {dupe_file_path} Existing: {normal_target}")
                with open(dupes_file, 'a', encoding='utf-8') as dup:
                    dup.write(f"{cachename}\t{dupe_file_path}\t{special_path}\n")
                dupe_count += 1
                continue
        
            elif old_info and old_info['sha1'] != sha1 and size > old_info['size']:
                dbg(f"[OTHER] SHA1 differs, incoming file is larger ({size}>{old_info['size']}). Moving old main to dupe and promoting new file.")
                stem, suffix = normal_target.stem, normal_target.suffix
                parent = normal_target.parent
                for n in range(1, 100):
                    dupe_candidate = parent / f"{stem}-{n}{suffix}"
                    if not dupe_candidate.exists():
                        dbg(f"[OTHER] Renaming {normal_target} -> {dupe_candidate}")
                        normal_target.rename(dupe_candidate)
                        break
                final_target = str(normal_target)
                dbg(f"[OTHER] Copying new main: {dupe_file_path} -> {final_target}")
                copy_file(file, final_target, f"{cachename}/{Path(final_target).relative_to(Path(archive_root) / 'ARCHIVE').as_posix()} - UNIQUE DUPE ( NEW FILE SIZE )", parts, special_path)
                continue
        
            else:
                dbg(f"[OTHER] SHA1 differs but file is smaller or same size ({size}<={old_info['size'] if old_info else 'n/a'}), looking for dupe slots.")
                found_duplicate = False
                stem, suffix = normal_target.stem, normal_target.suffix
                parent = normal_target.parent
                for n in range(1, 100):
                    dupe_candidate = parent / f"{stem}-{n}{suffix}"
                    if not dupe_candidate.exists():
                        dbg(f"[OTHER] Dupe slot {dupe_candidate} is available.")
                        break
                    dupe_info = get_file_info(str(dupe_candidate), ffprobe_path, archive_root, queryname, cachename)
                    if dupe_info and dupe_info['sha1'] == sha1:
                        dbg(f"[OTHER] Found existing dupe with matching SHA1: {dupe_candidate}")
                        with open(dupes_file, 'a', encoding='utf-8') as dup:
                            dup.write(f"{cachename}\t{dupe_file_path}\t{dupe_candidate.name}\n")
                        dupe_count += 1
                        found_duplicate = True
                        break
                if found_duplicate:
                    dbg(f"[OTHER] Duplicate found, not copying new file: {dupe_file_path}")
                    continue
                final_target, _ = incremental_copy(str(file), str(normal_target), "0", ffprobe_path)
                dbg(f"[OTHER] Copying as new dupe: {dupe_file_path} -> {final_target}")
                copy_file(file, final_target, f"{cachename}/{Path(final_target).relative_to(Path(archive_root) / 'ARCHIVE').as_posix()} - UNIQUE DUPE", parts, special_path)
                continue
        
        final_target, _ = incremental_copy(str(file), str(normal_target), OVERRIDE_MODE, ffprobe_path)
        copy_file(file, final_target, f"{cachename}/{special_path}", parts, special_path)


def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        rem = seconds % 60
        return f"{minutes}m {rem:.2f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        rem = seconds % 60
        return f"{hours}h {minutes}m {rem:.2f}s"


def sort_dupes_file_by_target_path(dupes_file_path):
    if not os.path.exists(dupes_file_path):
        return

    try:
        with open(dupes_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        parsed = []
        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) != 3:
                continue
            cache_name, dat_path, target_path = parts
            parsed.append((target_path.lower(), dat_path.lower(), line))

        parsed.sort()

        with open(dupes_file_path, 'w', encoding='utf-8') as f:
            for _, _, original_line in parsed:
                f.write(original_line)

    except Exception as e:
        dbg(f"[ERROR] Failed to sort dupes file: {e}")

if __name__ == '__main__':
    global debug_log

    start_time = datetime.now()

    if len(sys.argv) < 11:
        print("Usage: cache_copy_combined.py <archive_root> <queryname> <cachename> <search_root> <inf_file_path> <ffprobe_path> <dupes_logfile_path> <nofileforinf_logfile_path> <cdnfiles_log_path> <dcfiles_log_path> [exceptions_modified_filepath] [exceptions_corrupt_filepath] [--customquery] [--skipincrcopy] [--verbose] [--debug] [--override <newfiles_log_path>]")
        sys.exit(1)

    archive_root = sys.argv[1]
    queryname = sys.argv[2]
    cachename = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].strip() else None
    search_root = sys.argv[4]
    inf_file_path = sys.argv[5]
    ffprobe_path = sys.argv[6]
    dupes_file = sys.argv[7]
    nofileforinf_file = sys.argv[8]
    cdnfiles_file = sys.argv[9]
    dcfiles_file = sys.argv[10]

    next_arg = 11
    if len(sys.argv) > next_arg and not sys.argv[next_arg].startswith("--"):
        exceptions_modified_file = sys.argv[next_arg]
        next_arg += 1
    if len(sys.argv) > next_arg and not sys.argv[next_arg].startswith("--"):
        exceptions_corrupt_file = sys.argv[next_arg]
        next_arg += 1

    exceptions_modified_set = set()
    exceptions_corrupt_set = set()
    if exceptions_modified_file and os.path.exists(exceptions_modified_file):
        with open(exceptions_modified_file, encoding='utf-8') as f:
            exceptions_modified_set = set(line.strip().upper() for line in f if line.strip())
    if exceptions_corrupt_file and os.path.exists(exceptions_corrupt_file):
        with open(exceptions_corrupt_file, encoding='utf-8') as f:
            exceptions_corrupt_set = set(line.strip().upper() for line in f if line.strip())

    i = next_arg
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--override":
            OVERRIDE_NEW_MODE = True
            if i + 1 >= len(sys.argv):
                print("Error: --override requires a log file path argument")
                sys.exit(1)
            OVERRIDE_LOG_PATH = sys.argv[i + 1]
            i += 2
            continue
        elif arg == "--skipincrcopy":
            OVERRIDE_MODE = "1"
        elif arg == "--verbose":
            VERBOSE_MODE = True
        elif arg == "--customquery":
            CUSTOM_QUERY_MODE = True
        elif arg == "--debug":
            DEBUG_ENABLED = True
        i += 1

    if CUSTOM_QUERY_MODE:
        base_copy_path = Path(archive_root) / "ARCHIVE" / queryname / cachename
    else:
        base_copy_path = Path(archive_root) / "ARCHIVE"

    if DEBUG_ENABLED:
        debug_log_path = base_copy_path / "log_DEBUG.log"
        os.makedirs(debug_log_path.parent, exist_ok=True)
        debug_log = open(debug_log_path, 'a', encoding='utf-8', buffering=1)

    target_cachename = cachename.strip().lower() if cachename else ""

    with open(inf_file_path, encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\r\n').split('|')
            if len(parts) >= 4 and parts[3].strip().lower() == target_cachename.lower():
                if not started_processing:
                    if DEBUG_ENABLED:
                        debug_log.write(f"[INIT] Processing ... {target_cachename}\n")
                        debug_log.flush()
                    started_processing = True
                process_inf_line(
                    line,
                    archive_root,
                    search_root,
                    queryname,
                    cachename,
                    ffprobe_path,
                    nofileforinf_file,
                    dupes_file,
                    cdnfiles_file,
                    dcfiles_file,
                    exceptions_modified_set,
                    exceptions_corrupt_set
                )
                any_processed = True

    sort_dupes_file_by_target_path(dupes_file)

    end_time = datetime.now()
    duration_secs = (end_time - start_time).total_seconds()

    try:
        start_fmt = start_time.strftime("%-m/%-d/%Y %H:%M:%S")
        end_fmt = end_time.strftime("%-m/%-d/%Y %H:%M:%S")
    except ValueError:
        start_fmt = start_time.strftime("%#m/%#d/%Y %H:%M:%S")
        end_fmt = end_time.strftime("%#m/%#d/%Y %H:%M:%S")

    if any_processed:
        print("\n=======================================================")
        print(f"Cache Copy started at :          | {start_fmt}")
        print(f"Cache Copy ended at :            | {end_fmt}")
        print(f"Duration :                       | {format_duration(duration_secs)}")
        print(f"Total files copied :             | {copied_count}")
        print(f"Total corrupt files copied :     | {corrupt_count}")
        print(f"Total modified files copied :    | {modified_count}")
        print(f"Total dupes :                    | {dupe_count}")
        print(f"Total INF w/ multi DAT matches : | {multiple_matched_dat_files}")
        print("=======================================================\n")

    if DEBUG_ENABLED and any_processed:
        debug_log.write("\n=======================================================\n")
        debug_log.write(f"Cache Copy started at :          {start_fmt}\n")
        debug_log.write(f"Cache Copy ended at :            {end_fmt}\n")
        debug_log.write(f"Duration :                       {format_duration(duration_secs)}\n")
        debug_log.write(f"Total files copied :             {copied_count}\n")
        debug_log.write(f"Total corrupt files copied :     {corrupt_count}\n")
        debug_log.write(f"Total modified files copied :    {modified_count}\n")
        debug_log.write(f"Total dupes :                    {dupe_count}\n")
        debug_log.write(f"Total INF w/ multi DAT matches : {multiple_matched_dat_files}\n")
        debug_log.write(f"=======================================================\n")
        debug_log.write("\n")
        debug_log.flush()
        debug_log.close()

    if OVERRIDE_NEW_MODE and OVERRIDE_NEW_LOG:
        OVERRIDE_NEW_LOG.close()
