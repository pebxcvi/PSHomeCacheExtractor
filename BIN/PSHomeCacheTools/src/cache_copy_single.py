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
        debug_log.write(f"[DEBUG] {message}\n")
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

def copy_file(src, dst, message=""):
    global copied_count
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
        debug_log.write(log_line + "\n")
        debug_log.flush()

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

def process_inf_line(line, archive_root, search_root, queryname, cachename, ffprobe_path, nofileforinf_file, dupes_file):
    global copied_count, corrupt_count, modified_count, dupe_count, multiple_matched_dat_files
    dbg("Processing line: %s", line.strip())
    parts = line.strip().split('|')
    if len(parts) < 4:
        dbg("Skipping line due to invalid format")
        return
        
    if not cachename or not cachename.strip():
        cachename = parts[3].strip()

    c, d, _, raw_date = parts[:4]

    DATE_MAP = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
    }

    parsed_date = "null"
    if raw_date and raw_date.lower() != "null":
        try:
            day = raw_date[:2]
            month_str = raw_date[2:5]
            year = raw_date[5:]
            month = DATE_MAP.get(month_str, "??")
            if month != "??":
                parsed_date = f"{year}-{month}-{day}"
        except Exception as e:
            dbg("Failed to parse date '%s': %s", raw_date, e)

    inf_url = d
    ext = Path(inf_url).suffix
    inf_url_parts = inf_url.split('/')
    inf_url_host = inf_url_parts[0].lower() if inf_url_parts else ""
    
    dbg("Parsed inf_url_host: %s", inf_url_host)
    
    crackle_domains = {
        "images-us-az.crackle.com",
        "images.crackle.com",
        "images2.crackle.com",
        "images3.crackle.com",
        "dl.dropbox.com",
    }
    
    root_folder_map = {
        "scee": "scee-home.playstation.net",
        "scea": "scea-home.playstation.net",
        "scej": "scej-home.playstation.net",
        "sceasia": "sceasia-home.playstation.net"
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
                     if '<xml' in chunk_lower or any(tag in chunk_lower for tag in ['<?xml', '<rss', '<profile']):
                         if not inf_url.endswith('.xml'):
                             inf_url += ".xml"
                             special_path += ".xml"
                             dbg("[EXTENSIONLESS] Patched path with .xml : %s", file)
             except Exception as e:
                 dbg("Failed to detect type for extensionless file %s: %s", file, e)
    
        normal_target = construct_full_target_path(archive_root, queryname, cachename, special_path)
        info = get_file_info(str(file), ffprobe_path, archive_root, queryname, cachename, inf_url=inf_url)
        if not info:
            dbg("Skipping file %s due to failed info retrieval", file)
            continue

        size = info['size']
        sha1 = info['sha1']
        sdatver = info['sdatver']
        imgcor = info['imgcor']
        vidcor = info['vidcor']

        if size == 0:
            corrupt_target = construct_full_target_path(archive_root, queryname, cachename, f"corrupted/{special_path}")
            final_target, _ = incremental_copy(str(file), str(corrupt_target), OVERRIDE_MODE, ffprobe_path)
            copy_file(file, final_target, f"{cachename}/corrupted/{special_path} - CORRUPT ( 0 BYTES )")
            corrupt_count += 1
            return

        elif imgcor == 1 or vidcor == 1 or sdatver == 0 or info.get('xmlcor', 0) == 1:

            if info.get('xmlcor', 0) == 1:
                dbg("[XML] Corrupted XML: %s", file)

            corrupt_target = construct_full_target_path(archive_root, queryname, cachename, f"corrupted/{special_path}")
            final_target, cor_old = incremental_copy(str(file), str(corrupt_target), OVERRIDE_MODE, ffprobe_path)
            if cor_old['sha1'] and cor_old['filesize'] >= 0:
                if sha1 != cor_old['sha1'] and size > cor_old['filesize']:
                    copy_file(file, final_target, f"{cachename}/corrupted/{special_path} - CORRUPT ( NEW FILE SIZE )")
                    corrupt_count += 1
                    return
            else:
                copy_file(file, final_target, f"{cachename}/corrupted/{special_path} - CORRUPT")
                corrupt_count += 1
                return

        elif sdatver == 3.3:
            mod_target = construct_full_target_path(archive_root, queryname, cachename, f"modified/{special_path}")
            final_target, cor_old = incremental_copy(str(file), str(mod_target), OVERRIDE_MODE, ffprobe_path)
            if sha1 != cor_old['sha1']:
                copy_file(file, final_target, f"{cachename}/modified/{special_path} - MODIFIED SDAT")
                modified_count += 1
            return

        if normal_target.exists():
            old_info = get_file_info(str(normal_target), ffprobe_path, archive_root, queryname, cachename)
            if old_info and old_info['sha1'] == sha1:
                relative_path = Path(file).relative_to(search_root).as_posix()
                dat_line = f"{cachename}\t{cachename}/{relative_path}\t{special_path}\n"
                with open(dupes_file, 'a', encoding='utf-8', errors='ignore') as dup:
                    dup.write(dat_line)
                dupe_count += 1
                return
            else:
                dbg("[SHA1-MISMATCH] Existing target: %s | New SHA1: %s | Old SHA1: %s", normal_target, sha1, old_info['sha1'])

        final_target, _ = incremental_copy(str(file), str(normal_target), OVERRIDE_MODE, ffprobe_path)
        copy_file(file, final_target, f"{cachename}/{special_path}")

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

    if '--debug' in sys.argv:
        DEBUG_ENABLED = True
        sys.argv.remove('--debug')

    for arg in sys.argv[9:]:
        if arg == "--skipincrcopy":
            OVERRIDE_MODE = "1"
        elif arg == "--verbose":
            VERBOSE_MODE = True
        elif arg == "--customquery":
            CUSTOM_QUERY_MODE = True

    if len(sys.argv) < 9:
        print("Usage: cache_copy_single.py <archive_root> <queryname> <cachename> <search_root> <inf_file_path> <ffprobe_path> <dupes_logfile_path> <nofileforinf_logfile_path> [--customquery] [--skipincrcopy] [--verbose] [--debug]")
        sys.exit(1)

    archive_root = sys.argv[1]
    queryname = sys.argv[2]
    cachename = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].strip() else None
    search_root = sys.argv[4]
    inf_file_path = sys.argv[5]
    ffprobe_path = sys.argv[6]
    dupes_file = sys.argv[7]
    nofileforinf_file = sys.argv[8]

    if CUSTOM_QUERY_MODE:
        base_copy_path = Path(archive_root) / "ARCHIVE" / queryname / cachename
    else:
        base_copy_path = Path(archive_root) / "ARCHIVE"

    if DEBUG_ENABLED:
        debug_log_path = base_copy_path / "log_DEBUG.log"
        os.makedirs(debug_log_path.parent, exist_ok=True)
        debug_log = open(debug_log_path, 'w', encoding='utf-8', buffering=1)

    dbg("Starting processing with inf file: %s", inf_file_path)

    with open(inf_file_path, encoding='utf-8') as file:
        for line in file:
            process_inf_line(
                line,
                archive_root,
                search_root,
                queryname,
                cachename,
                ffprobe_path,
                nofileforinf_file,
                dupes_file
            )

    sort_dupes_file_by_target_path(dupes_file)

    end_time = datetime.now()
    duration_secs = (end_time - start_time).total_seconds()

    try:
        start_fmt = start_time.strftime("%-m/%-d/%Y %H:%M:%S")
        end_fmt = end_time.strftime("%-m/%-d/%Y %H:%M:%S")
    except ValueError:
        start_fmt = start_time.strftime("%#m/%#d/%Y %H:%M:%S")
        end_fmt = end_time.strftime("%#m/%#d/%Y %H:%M:%S")

    print("\n=======================================================")
    print(f"Cache Copy started at :          | {start_fmt}")
    print(f"Cache Copy ended at :            | {end_fmt}")
    print(f"Duration :                       | {format_duration(duration_secs)}")
    print(f"Total files copied :             | {copied_count}")
    print(f"Total corrupt files copied :     | {corrupt_count}")
    print(f"Total modified files copied :    | {modified_count}")
    print(f"Total dupes :                    | {dupe_count}")
    print(f"Total INF w/ multi DAT matches : | {multiple_matched_dat_files}")
    print("=======================================================")
    
    if DEBUG_ENABLED:
        debug_log.write("\n=======================================================\n")
        debug_log.write(f"Cache Copy started at :          {start_fmt}\n")
        debug_log.write(f"Cache Copy ended at :            {end_fmt}\n")
        debug_log.write(f"Duration :                       {format_duration(duration_secs)}\n")
        debug_log.write(f"Total files copied :             {copied_count}\n")
        debug_log.write(f"Total corrupt files copied :     {corrupt_count}\n")
        debug_log.write(f"Total modified files copied :    {modified_count}\n")
        debug_log.write(f"Total dupes :                    {dupe_count}\n")
        debug_log.write(f"Total INF w/ multi DAT matches : {multiple_matched_dat_files}\n")
        debug_log.write(f"=======================================================")
        debug_log.flush()
        debug_log.close()
