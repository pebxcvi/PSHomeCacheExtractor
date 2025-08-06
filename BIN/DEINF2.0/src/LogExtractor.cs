using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Security.Cryptography;
using System.Collections.Generic;
using System.Linq;

public static class LogExtractor
{
    public static bool DebugOutput = false;

    static readonly string[] KnownExts = new[] {
        "agf","ani","atgi","atmos","bank","bin","bnk","cam-def","dat","dds","effect","efx","enemy","gui-setup",
        "hkx","ini","jpg","json","level-setup","lpf","lua","luac","map","mdl","mp3","node-def","oel","png","probe",
        "psd","raw","repertoire_circuit","rig","scene","skn","spline-def","tempo","tmx","ttf","txt","ui-setup","xml",
        "cdata","mp4","ocean","tga","wav","avtr","der","fnt","sdc","sql","hcdb","bar","sdat","m4v","odc","jpeg","do", "hsml"
    };

    static readonly Regex FileExtRegex = new Regex(
        @"([a-zA-Z0-9_\-\./\\]+?\.(?:" +
        string.Join("|", KnownExts) +
        "))",
        RegexOptions.IgnoreCase
    );

    public static LogRow ExtractLogInfo(string filePath, List<string> errorLines = null)
    {
        if (DebugOutput) Console.WriteLine($"[DEBUG] ExtractLogInfo for: {filePath}");
        try
        {
            var fileName = Path.GetFileName(filePath);
            if (DebugOutput) Console.WriteLine($"[DEBUG] fileName: {fileName}");
            var uriHash = fileName.Split('_')[0];
            if (DebugOutput) Console.WriteLine($"[DEBUG] uriHash: {uriHash}");

            byte[] fileBytes = File.ReadAllBytes(filePath);
            if (DebugOutput) Console.WriteLine($"[DEBUG] fileBytes length: {fileBytes.Length}");
            string encryptedSha1 = CalculateSHA1(fileBytes);
            if (DebugOutput) Console.WriteLine($"[DEBUG] encryptedSha1: {encryptedSha1}");

            bool WasEncrypted = fileBytes.Length > 4 &&
                fileBytes[0] == 0x00 && fileBytes[1] == 0x00 &&
                fileBytes[2] == 0x00 && fileBytes[3] == 0x01;

            if (DebugOutput) Console.WriteLine($"[DEBUG] WasEncrypted: {WasEncrypted}");

            string decryptedSha1 = "";
            byte[] decryptedBytes = null;

            if (WasEncrypted)
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Removing prefix and decrypting...");
                var noPrefix = ToolsImplementation.RemovePaddingPrefix(fileBytes);
                decryptedBytes = LIBSECURE.Crypt_Decrypt(noPrefix, ToolsImplementation.MetaDataV1IVA, 8);
                decryptedSha1 = CalculateSHA1(decryptedBytes);
            }
            else
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Not encrypted, using fileBytes directly.");
                decryptedBytes = fileBytes;
            }

            string uriPath = ExtractUriPath(decryptedBytes);
            if (DebugOutput) Console.WriteLine($"[DEBUG] Extracted uriPath: [{uriPath}]");
            string dateStr = ExtractDateString(decryptedBytes);
            if (DebugOutput) Console.WriteLine($"[DEBUG] Extracted dateStr: [{dateStr}]");

            if (string.IsNullOrWhiteSpace(uriPath))
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] uriPath is null/whitespace. Logging error.");
                errorLines?.Add($"[ERROR] {fileName} failed to decrypt");
                return null;
            }

            if (!string.IsNullOrEmpty(uriPath))
            {
                if (uriPath.IndexOf("cache/", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    if (DebugOutput) Console.WriteLine($"[DEBUG] uriPath contains 'cache/'. Logging error.");
                    errorLines?.Add($"[ERROR] {fileName} partially decrypted");
                    return null;
                }
                
               if (uriPath.Length > 32 && uriPath.Distinct().Count() == 1)
               {
                   if (DebugOutput) Console.WriteLine($"[DEBUG] uriPath is a wall of '{uriPath[0]}' (len={uriPath.Length}). Logging error.");
                   errorLines?.Add($"[ERROR] {fileName} wall of {uriPath[0]}");
                   return null;
               }
            }

            return new LogRow
            {
                UriHash = uriHash,
                UriPath = uriPath,
                WasEncrypted = WasEncrypted ? "Yes" : "No",
                Date = dateStr,
                EncryptedSha1 = encryptedSha1,
                DecryptedSha1 = decryptedSha1
            };
        }
        catch (Exception ex)
        {
            var fileName = Path.GetFileName(filePath);
            if (DebugOutput) Console.WriteLine($"[DEBUG] Exception: {ex}");
            errorLines?.Add($"[ERROR] {fileName} failed to decrypt");
            return null;
        }
    }

    public static void WriteLogTable(
        List<LogRow> rows,
        string outputPath,
        string[] infoLines = null,
        string[] postInfoLines = null)
    {
        if (DebugOutput) Console.WriteLine($"[DEBUG] Writing log table to {outputPath}");
        string[] headers = {
            "URI Hash",
            "URI Path",
            "Was Encrypted ?",
            "Date",
            "Encrypted INF SHA1",
            "Decrypted INF SHA1"
        };

        int[] widths = new int[headers.Length];
        widths[0] = Math.Max(headers[0].Length, rows.Count == 0 ? 10 : MaxLen(rows, r => r.UriHash));
        widths[1] = Math.Max(headers[1].Length, rows.Count == 0 ? 10 : MaxLen(rows, r => r.UriPath));
        widths[2] = Math.Max(headers[2].Length, rows.Count == 0 ? 3 : MaxLen(rows, r => r.WasEncrypted));
        widths[3] = Math.Max(headers[3].Length, rows.Count == 0 ? 10 : MaxLen(rows, r => r.Date));
        widths[4] = Math.Max(headers[4].Length, 40);
        widths[5] = Math.Max(headers[5].Length, 40);

        string sep = "|" + string.Join("|", widths.Select(w => new string('=', w + 2))) + "|";

        var sb = new StringBuilder();

        if (infoLines != null)
        {
            foreach (var line in infoLines)
                sb.AppendLine("[INFO] " + line);
            sb.AppendLine();
        }

        sb.AppendLine(sep);

        sb.Append("| ");
        for (int i = 0; i < headers.Length; i++)
        {
            sb.Append(headers[i].PadRight(widths[i]));
            sb.Append(" | ");
        }
        sb.Length -= 1;
        sb.AppendLine();

        sb.AppendLine(sep);

        foreach (var r in rows)
        {
            if (DebugOutput) Console.WriteLine($"[DEBUG] Writing row: {r.UriHash} | {r.UriPath}");
            sb.AppendFormat("| {0} | {1} | {2} | {3} | {4} | {5} |\n",
                r.UriHash.PadRight(widths[0]),
                r.UriPath.PadRight(widths[1]),
                r.WasEncrypted.PadRight(widths[2]),
                r.Date.PadRight(widths[3]),
                r.EncryptedSha1.PadRight(widths[4]),
                r.DecryptedSha1.PadRight(widths[5])
            );
        }

        sb.AppendLine(sep);

        if (postInfoLines != null)
        {
            sb.AppendLine();
            foreach (var line in postInfoLines)
                sb.AppendLine("[INFO] " + line);
        }

        Directory.CreateDirectory(Path.GetDirectoryName(outputPath));
        if (DebugOutput) Console.WriteLine($"[DEBUG] Saving log file to disk.");
        File.WriteAllText(outputPath, sb.ToString());
    }

    static int MaxLen(List<LogRow> rows, Func<LogRow, string> f)
    {
        int max = 0;
        foreach (var r in rows)
            max = Math.Max(max, (f(r) ?? "").Length);
        if (DebugOutput) Console.WriteLine($"[DEBUG] MaxLen result: {max}");
        return max;
    }

    public static string CalculateSHA1(byte[] data)
    {
        if (DebugOutput) Console.WriteLine($"[DEBUG] Calculating SHA1 for data length: {data.Length}");
        using (var sha1 = SHA1.Create())
        {
            string hash = BitConverter.ToString(sha1.ComputeHash(data)).Replace("-", "");
            if (DebugOutput) Console.WriteLine($"[DEBUG] SHA1: {hash}");
            return hash;
        }
    }

    public static string ExtractUriPath(byte[] data)
    {
        string allText = Encoding.UTF8.GetString(data);
        if (DebugOutput) Console.WriteLine($"[DEBUG] allText (start): [{(allText.Length > 120 ? allText.Substring(0,120) + "..." : allText)}]");
        allText = allText.Replace("ÿ", "y");
        if (DebugOutput) Console.WriteLine($"[DEBUG] allText (after ÿ->y): [{(allText.Length > 120 ? allText.Substring(0,120) + "..." : allText)}]");

        List<string> asciiStrings = new List<string>();
        StringBuilder cur = new StringBuilder();

        foreach (char c in allText)
        {
            if (c >= 32 && c <= 126)
                cur.Append(c);
            else
            {
                if (cur.Length >= 6)
                {
                    if (DebugOutput) Console.WriteLine($"[DEBUG] asciiString candidate: [{cur}]");
                    asciiStrings.Add(cur.ToString());
                }
                cur.Clear();
            }
        }
        if (cur.Length >= 6)
        {
            if (DebugOutput) Console.WriteLine($"[DEBUG] asciiString candidate: [{cur}]");
            asciiStrings.Add(cur.ToString());
        }

        var httpOrWebUris = Regex.Matches(
            allText,
            @"(?:https?|web|tss|file)://[^\x00-\x1F""<>]+",
            RegexOptions.IgnoreCase
        );
        if (DebugOutput) Console.WriteLine($"[DEBUG] httpOrWebUris.Count: {httpOrWebUris.Count}");
        if (httpOrWebUris.Count > 0)
        {
            string longestUri = httpOrWebUris.Cast<Match>()
                                             .Select(m => m.Value)
                                             .OrderByDescending(s => s.Length)
                                             .First();
            if (DebugOutput) Console.WriteLine($"[DEBUG] Matched URI: [{longestUri}]");
            longestUri = longestUri.Replace('\\', '/');
            if (DebugOutput) Console.WriteLine($"[DEBUG] URI after \\->/: [{longestUri}]");
            return TrimToAscii(longestUri);
        }

        string specialCandidate = null;

        foreach (var s in asciiStrings)
        {
            if (DebugOutput) Console.WriteLine($"[DEBUG] asciiString: [{s}]");
            // Avatar-X.jpg
            var avatarMatch = Regex.Match(s, @"Avatar-[a-zA-Z0-9_\-]+\.jpg", RegexOptions.IgnoreCase);
            if (avatarMatch.Success)
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Matched Avatar: [{avatarMatch.Value}]");
                return avatarMatch.Value;
            }

            // Profile-XXX.xml or Inventory-XXX.xml (keep longest)
            var specialMatch = Regex.Match(s, @"(Profile|Inventory)-[a-zA-Z0-9_\-]+(\.xml)?", RegexOptions.IgnoreCase);
            if (specialMatch.Success && (specialCandidate == null || specialMatch.Value.Length > specialCandidate.Length))
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Matched special Profile/Inventory: [{specialMatch.Value}]");
                specialCandidate = specialMatch.Value;
            }

            // Starts with "NP" and has a dash at position 9 (NPXXXXXXXXX-)
            for (int i = 0; i <= s.Length - 2; i++)
            {
                if (s.Substring(i, 2).Equals("NP", StringComparison.OrdinalIgnoreCase))
                {
                    string candidate = s.Substring(i).Trim(" '\"()[]{}<>\t\r\n".ToCharArray());
                    int dashIdx = candidate.IndexOf('-');
                    if (dashIdx > 0 && dashIdx == 9)
                    {
                        if (DebugOutput) Console.WriteLine($"[DEBUG] Matched NP-candidate: [{candidate}]");
                        return candidate;
                    }
                }
            }

            // vers_ version identifiers
            var versMatch = Regex.Match(
                s,
                @"\bVERS_[A-Za-z0-9\-_/\\\.]{20,}\.xml\b",
                RegexOptions.IgnoreCase
            );
            if (versMatch.Success)
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Matched vers_: [{versMatch.Value}]");
                return versMatch.Value;
            }

            // TSSExtract/RegionMap.xml
            if (s.Contains("TSSExtract/") && s.EndsWith(".xml", StringComparison.OrdinalIgnoreCase))
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Matched TSSExtract/RegionMap.xml");
                return "TSSExtract/RegionMap.xml";
            }

            // Objects/{GUID}/{GUID}.ext
            var objMatch = Regex.Match(
                s,
                @"Objects/[0-9a-fA-F]{8}-[0-9a-fA-F]{8}-[0-9a-fA-F]{8}-[0-9a-fA-F]{8}/[0-9a-fA-F]{8}-[0-9a-fA-F]{8}-[0-9a-fA-F]{8}-[0-9a-fA-F]{8}\.(bar|bin|sdat)",
                RegexOptions.IgnoreCase
            );
            if (objMatch.Success)
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Matched Objects/{{guid}}.ext: [{objMatch.Value}]");
                return objMatch.Value;
            }
        }

        // Return longest Profile/Inventory match if found
        if (!string.IsNullOrEmpty(specialCandidate))
        {
            if (DebugOutput) Console.WriteLine($"[DEBUG] Using specialCandidate: [{specialCandidate}]");
            return specialCandidate;
        }

        foreach (var s in asciiStrings.AsEnumerable().Reverse())
        {
            var m = Regex.Match(s, @"\.?([A-Za-z0-9_\-\.]+\.jpg)", RegexOptions.IgnoreCase);
            if (m.Success)
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Matched .jpg fallback: [{m.Groups[1].Value}]");
                return m.Groups[1].Value;
            }
        }

        var fileMatches = FileExtRegex.Matches(allText);
        foreach (Match m in fileMatches.Cast<Match>().Reverse())
        {
            string value = m.Value.Replace("\\", "/");
            if (!value.StartsWith("cache/", StringComparison.OrdinalIgnoreCase) &&
                !value.StartsWith("objectdefs/", StringComparison.OrdinalIgnoreCase))
            {
                if (DebugOutput) Console.WriteLine($"[DEBUG] Matched FileExtRegex fallback: [{value}]");
                return CleanLeadingDots(value);
            }
        }
        if (fileMatches.Count > 0)
        {
            if (DebugOutput) Console.WriteLine($"[DEBUG] Matched FileExtRegex (last): [{fileMatches[fileMatches.Count - 1].Value}]");
            return CleanLeadingDots(fileMatches[fileMatches.Count - 1].Value);
        }

        var paths = Regex.Matches(allText, @"(?:[a-z0-9_./\-]+/[a-z0-9_./\-]+\.\w+)", RegexOptions.IgnoreCase);
        if (paths.Count > 0)
        {
            if (DebugOutput) Console.WriteLine($"[DEBUG] Matched paths fallback: [{paths[paths.Count - 1].Value}]");
            return CleanLeadingDots(paths[paths.Count - 1].Value);
        }

        string longest = "";
        foreach (Match m in Regex.Matches(allText, @"[ -~]{8,}"))
            if (m.Value.Length > longest.Length)
                longest = m.Value;
        if (DebugOutput) Console.WriteLine($"[DEBUG] Final longest fallback: [{longest}]");
        return CleanLeadingDots(longest);
    }

    static string CleanLeadingDots(string s)
    {
        if (string.IsNullOrEmpty(s)) return s;
        int i = 0;
        while (i < s.Length && !char.IsLetterOrDigit(s[i])) i++;
        if (DebugOutput) Console.WriteLine($"[DEBUG] CleanLeadingDots: [{s}] => [{s.Substring(i)}]");
        return s.Substring(i);
    }

    static string TrimToAscii(string s)
    {
        int end = 0;
        while (end < s.Length && s[end] >= 0x20 && s[end] <= 0x7E) end++;
        if (DebugOutput) Console.WriteLine($"[DEBUG] TrimToAscii: [{s}] => [{s.Substring(0, end)}]");
        return s.Substring(0, end);
    }

    public static string ExtractDateString(byte[] data)
    {
        string allText = Encoding.ASCII.GetString(data);
        if (DebugOutput) Console.WriteLine($"[DEBUG] ExtractDateString: [{(allText.Length > 120 ? allText.Substring(0,120) + "..." : allText)}]");
        var m = Regex.Match(allText, @"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s\d{2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}\s\d{2}:\d{2}:\d{2}\sGMT\b");
        if (m.Success) return m.Value;
        m = Regex.Match(allText, @"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b");
        if (m.Success) return m.Value;
        return "";
    }
}
