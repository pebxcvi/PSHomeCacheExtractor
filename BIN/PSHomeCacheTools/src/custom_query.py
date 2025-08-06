import re
import sys

def do_replace(match, replace):
    """
    Implements JREPL-like $txt=... replacement.
    Supports $txt=$1+$2, $txt=$1, etc.
    Does not remove plus signs from the input, only concatenates groups.
    """
    if replace.startswith('$txt='):
        expr = replace[5:]
        tokens = expr.split('+')
        result = ''
        for token in tokens:
            token = token.strip()
            if token.startswith("$") and token[1:].isdigit():
                idx = int(token[1:])
                val = match.group(idx) if idx <= len(match.groups()) and match.group(idx) else ''
                result += val
            else:
                result += token
        return result
    return match.group(0)

def parse_jrepl_regex(pattern):
    """
    Converts a JREPL-style regex like /.../i to (pattern, flags).
    If the pattern does not start with /, returns as is with IGNORECASE.
    """
    if pattern.startswith('/') and pattern.count('/') >= 2:
        last_slash = pattern.rfind('/')
        pat = pattern[1:last_slash]
        flags = pattern[last_slash+1:]
        py_flags = 0
        if 'i' in flags.lower():
            py_flags |= re.IGNORECASE
        return pat, py_flags
    return pattern, re.IGNORECASE

def process_file(search_pat, replace_pat, blocklist_pat, infile, outfile):
    search_re = re.compile(search_pat, re.IGNORECASE)

    blocklist_re = None
    blocklist_flags = 0
    if blocklist_pat and blocklist_pat not in ("$^", ""):
        pat, blocklist_flags = parse_jrepl_regex(blocklist_pat)
        blocklist_re = re.compile(pat, blocklist_flags)

    with open(infile, encoding='utf-8', errors='ignore') as fin, \
         open(outfile, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.rstrip('\n')
            m = search_re.match(line)
            if not m:
                continue
            if blocklist_re and blocklist_re.search(line):
                continue
            fout.write(do_replace(m, replace_pat) + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: custom_query.py SEARCH REPLACE BLOCKLIST infile outfile")
        sys.exit(1)
    search_pat = sys.argv[1]
    replace_pat = sys.argv[2]
    blocklist_pat = sys.argv[3]
    infile = sys.argv[4]
    outfile = sys.argv[5]
    process_file(search_pat, replace_pat, blocklist_pat, infile, outfile)
