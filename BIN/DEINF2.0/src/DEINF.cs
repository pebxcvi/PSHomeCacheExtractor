using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Diagnostics;
using ShellProgressBar;

class DEINF
{
    static void Main(string[] args)
    {
        const string VERSION = "2.0";
        var easternZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");
        var runDate = TimeZoneInfo.ConvertTimeFromUtc(DateTime.UtcNow, easternZone).ToString("M/d/yyyy h:mm tt");

        if (args.Length < 1)
        {
            PrintUsage();
            return;
        }

        string inputPath = null;
        string logOutput = null;
        string fileOutput = null;
        bool logInfo = false;
        bool saveFiles = false;

        List<string> preInfoLines = new List<string>
        {
            $"DEINF Version {VERSION}",
            "Home Laboratory",
            "C# Implementation",
            $"Run Date {runDate}",
            $"Parameters: [{string.Join(", ", args)}]"
        };

        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "-l":
                    logInfo = true;
                    break;
                case "-lo":
                    if (i + 1 < args.Length) logOutput = args[++i];
                    else { Console.WriteLine("[ERROR] -lo flag requires an output path."); return; }
                    break;
                case "-s":
                    saveFiles = true;
                    break;
                case "-fo":
                    if (i + 1 < args.Length) fileOutput = args[++i];
                    else { Console.WriteLine("[ERROR] -fo flag requires an output folder."); return; }
                    break;
                default:
                    if (inputPath == null) inputPath = args[i];
                    break;
            }
        }

        if (!logInfo && !saveFiles)
        {
            Console.WriteLine("[ERROR] No operation specified. Use -l and/or -s.");
            PrintUsage();
            return;
        }

        if (inputPath == null)
        {
            Console.WriteLine("[ERROR] No input file/folder specified.");
            PrintUsage();
            return;
        }

        if (logInfo && string.IsNullOrWhiteSpace(logOutput))
        {
            logOutput = Path.Combine(Directory.GetCurrentDirectory(), "log.txt");
            string info = $"No -lo specified. Using default: {logOutput}";
            preInfoLines.Add(info);
        }

        if (saveFiles && string.IsNullOrWhiteSpace(fileOutput))
        {
            fileOutput = Path.Combine(Directory.GetCurrentDirectory(), "DECRYPTED");
            string info = $"No -fo specified. Using default: {fileOutput}";
            preInfoLines.Add(info);
        }

        List<string> files = new List<string>();
        if (File.Exists(inputPath))
        {
            if (Path.GetFileName(inputPath).Contains("_INF"))
                files.Add(inputPath);
        }
        else if (Directory.Exists(inputPath))
        {
            files.AddRange(Directory.GetFiles(inputPath)
                .Where(f => Path.GetFileName(f).Contains("_INF")));
        }
        else
        {
            Console.WriteLine("[ERROR] Input not found: " + inputPath);
            return;
        }

        if (files.Count == 0)
        {
            Console.WriteLine();
            Console.WriteLine($"[WARNING] No INF files found in: {inputPath}");
            Console.WriteLine();

            if (logInfo && !string.IsNullOrWhiteSpace(logOutput))
            {
                var preInfo = new[]
                {
                    $"DEINF Version {VERSION}",
                    "Home Laboratory",
                    "C# Implementation",
                    $"Run Date {runDate}",
                    $"Parameters: [{string.Join(", ", args)}]",
                    "[WARNING] No INF files found"
                };

                var postInfo = new[]
                {
                    $"Completed. Saved output to '{logOutput}'"
                };

                LogExtractor.WriteLogTable(new List<LogRow>(), logOutput, preInfo, postInfo);
            }

            return;
        }

        Console.WriteLine();
        Console.WriteLine($"Processing : {inputPath}");

        Stopwatch swDecrypt = Stopwatch.StartNew();

        if (saveFiles)
            Directory.CreateDirectory(fileOutput);

        List<LogRow> logRows = new List<LogRow>();
        List<string> errorLines = new List<string>();

        var options = new ProgressBarOptions
        {
            ForegroundColor = ConsoleColor.Green,
            ProgressCharacter = '█',
            BackgroundColor = ConsoleColor.DarkGray,
            BackgroundCharacter = ' ',
            DisplayTimeInRealTime = false
        };

        using (var pbar = new ProgressBar(files.Count, "Processing INF files...", options))
        {
            for (int i = 0; i < files.Count; i++)
            {
                var file = files[i];

                var fileInfo = new FileInfo(file);
                if (fileInfo.Length == 0)
                {
                    errorLines.Add($"[ERROR] {Path.GetFileName(file)} has 0 bytes");
                }
                else if (fileInfo.Length > 2048)
                {
                    errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a sdat");
                }
                else
                {
                    if (saveFiles)
                    {
                        DecryptionHandler.DecryptOrCopy(file, fileOutput, false);
                    }

                    if (logInfo)
                    {
                        var row = LogExtractor.ExtractLogInfo(file, errorLines);
                        if (row != null)
                            logRows.Add(row);
                    }
                }

                pbar.Tick($" {i + 1} / {files.Count} INF files processed.");
            }
        }

        Console.WriteLine();
        swDecrypt.Stop();

        if (errorLines.Count > 0)
        {
            foreach (var line in errorLines)
            {
                int colonIndex = line.IndexOf(':');
                if (colonIndex > 0)
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.Write(line.Substring(0, colonIndex));
                    Console.ResetColor();
        
                    Console.WriteLine(line.Substring(colonIndex));
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine(line);
                    Console.ResetColor();
                }
            }
            Console.WriteLine();
        }
        
        if (logInfo)
        {
            Stopwatch swExport = Stopwatch.StartNew();
            LogExtractor.WriteLogTable(logRows, logOutput, preInfoLines.ToArray(), null);
            swExport.Stop();

            if (errorLines.Count > 0)
            {
                File.AppendAllLines(logOutput, new[] { " " });
                File.AppendAllLines(logOutput, errorLines);
            }

            var postInfo = new[]
            {
                $"Decryption Speed: {FormatTime(swDecrypt.ElapsedMilliseconds)}",
                $"Export Speed: {FormatTime(swExport.ElapsedMilliseconds)}",
                $"Logged INF files: {logRows.Count}",
                $"Completed. Saved output to '{logOutput}'"
            };

            File.AppendAllLines(logOutput, new[] { "" });
            File.AppendAllLines(logOutput, postInfo.Select(line => "[INFO] " + line));
        }
    }

    static void PrintUsage()
    {
        Console.WriteLine("Usage: DEINF2.0.exe <file-or-folder> [-l] [-lo logFilePath] [-s] [-fo decryptedOutputFolder]");
        Console.WriteLine("  -l         Log INF file info");
        Console.WriteLine("  -lo PATH   Output log file path (optional, default is log.txt in current folder)");
        Console.WriteLine("  -s         Save decrypted INF files");
        Console.WriteLine("  -fo PATH   Output folder for decrypted files (optional, default is DECRYPTED in current folder)");
        Console.WriteLine();
        Console.WriteLine("Examples:");
        Console.WriteLine(@"  DEINF.exe inputDir -l");
        Console.WriteLine(@"  DEINF.exe inputDir -s");
        Console.WriteLine(@"  DEINF.exe inputDir -l -lo C:\out\log.txt");
        Console.WriteLine(@"  DEINF.exe inputDir -s -fo C:\out\decrypted");
        Console.WriteLine(@"  DEINF.exe inputDir -l -s -lo log.txt -fo DECRYPTED");
    }

    static string FormatTime(long ms)
    {
        if (ms >= 60000)
            return $"{ms / 60000}m {(ms % 60000) / 1000.0:F2}s";
        else if (ms >= 1000)
            return $"{ms / 1000.0:F2}s";
        else
            return $"{ms}ms";
    }
}
