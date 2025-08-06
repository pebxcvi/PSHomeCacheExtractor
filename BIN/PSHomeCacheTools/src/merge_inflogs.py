import os
import sys
import re
from pathlib import Path
from datetime import datetime

DEBUG_ENABLED = False

SPICEWAVE_BOTTOM = [
    "SplicewaveObjects",
    "SplicewaveScenes",
    "SplicewaveVideos",
    "SplicewaveWorldMaps",
    "SplicewaveGlobals"
]

#NPIA00005 can be for retail open betas or QA versions
#NPEA00013 can be for retail closed betas or old HDK versions
#NPIA00010 is for new HDK versions
# As far as I can tell, $(env) is only seen in NPIA00005 versions
# If assumption is wrong, I will add additional mapping based on cache name
title_env_map = {
    "NPIA00005": "cprod",
    "NPIA00010": "cdev",
    "NPEA00013": "cbeta"
}
DEFAULT_ENV = "cprod"

def batch_cleanup_dir_field(DIR, env):
    replacements = [
        ('$(env)', env),
        ('https://', ''),
        ('http://', ''),
        ('file://', ''),
        ('tss://', ''),
        ('web://', ''),
        ('://', '/'),
        (':/', '/'),
        ('//', '/'),
        (':10010', ''),
        (':10443', ''),
        (':10071', ''),
        ('%20', ' '),
        ('"', ''),
        ('?', ''),
        (':', ''),
        #('!', ''),
        #('&', 'amp'),
        #('$', ''),
        #('%', ''),
        #('(', ''),
        #(')', ''),
        #(' ', ''),
    ]
    for old, new in replacements:
        DIR = DIR.replace(old, new)
    return DIR

def format_batch_date(date_raw):
    date_raw = date_raw.strip()
    if not date_raw or date_raw.lower() == "null":
        return "null"
    if re.fullmatch(r'[a-fA-F0-9]{8,}', date_raw):
        return "null"
    for fmt in (
        "%a, %d %b %Y %H:%M:%S GMT",
        "%d%b%Y",
        "%d %b %Y",
        "%d %b %Y %H:%M:%S",
        "%d/%m/%Y"
    ):
        try:
            dt = datetime.strptime(date_raw, fmt)
            formatted = dt.strftime("%d%b%Y")
            if re.fullmatch(r"\d{2}[A-Za-z]{3}\d{4}", formatted):
                return formatted
        except Exception:
            continue
    if re.fullmatch(r"\d{2}[A-Za-z]{3}\d{4}", date_raw):
        return date_raw
    return "null"

def split_cachename_parts(filename):
    stem = Path(filename).stem
    return stem.split('$')

def process_log_file(file_path, temp_lines, env, given_cachename=None):
    filename = os.path.basename(file_path)
    parts = split_cachename_parts(filename)
    cachename = given_cachename
    if not cachename:
        cachename = parts[2] if len(parts) > 2 else (parts[-1] if parts else "")
    cachename = cachename.strip()
    with open(file_path, encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if (
                not line
                or line.startswith('[')
                or line.startswith('|=')
                or line.startswith('|-')
                or line.startswith('__')
                or line.lower().startswith('uri hash')
                or line.startswith('| URI Hash')
                or (line.startswith('|') and 'Short URI' in line)
            ):
                continue
            if line.startswith('|'):
                parts = [part.strip() for part in line.strip('|').split('|')]
                if len(parts) < 4:
                    continue
                HASH = parts[0].replace(' ', '')
                DIR = parts[1]
                DATE = parts[3].strip()
                URI = batch_cleanup_dir_field(DIR, env)
                if 'destinationhome' in URI.lower():
                    continue
                batch_date = format_batch_date(DATE)
                temp_lines.append((cachename, f"{HASH}|{URI}|{batch_date}|{cachename}\n"))

if __name__ == "__main__":
    args = sys.argv

    if len(args) < 3:
        print("Usage: merge_inflogs.py <INFLOGS path> <logs_ALL.txt path> [output_file] [title_id] [cachename] [--debug]")
        sys.exit(1)

    inf_folder = args[1]
    logs_all_path = args[2]
    output_file = None
    title_id = None
    given_cachename = None

    if len(args) > 3 and not args[3].startswith('--'):
        output_file = args[3]
    if len(args) > 4 and not args[4].startswith('--'):
        title_id = args[4]
    if len(args) > 5 and not args[5].startswith('--'):
        given_cachename = args[5]

    for arg in args:
        if arg == "--debug":
            DEBUG_ENABLED = True

    if not output_file:
        output_file = logs_all_path

    env = DEFAULT_ENV
    if title_id and title_id in title_env_map:
        env = title_env_map[title_id]

    inf_folder_path = Path(inf_folder).resolve()
    logs_all_path = Path(logs_all_path).resolve()
    output_file = Path(output_file).resolve()

    log_files = [p for p in inf_folder_path.glob('*.txt') if p.resolve() != logs_all_path]

    temp_lines = []
    total_files = len(log_files)
    for idx, file_path in enumerate(log_files, 1):
        print(f"({idx}/{total_files}) INFLOGS\\{file_path.stem} IS GETTING CLEANED UP ...")
        process_log_file(file_path, temp_lines, env, given_cachename)

    def cache_sort_key(t):
        cache, line = t
        if cache in SPICEWAVE_BOTTOM:
            return (1, SPICEWAVE_BOTTOM.index(cache), cache.lower(), line)
        else:
            return (0, 0, cache.lower(), line)

    temp_lines.sort(key=cache_sort_key)

    with open(output_file, 'w', encoding='utf-8') as out_f:
        for cache, line in temp_lines:
            out_f.write(line)

    if DEBUG_ENABLED:
        print(f"Merge complete: {len(temp_lines)} entries written to {output_file}")
