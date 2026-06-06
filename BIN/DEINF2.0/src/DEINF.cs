using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections.Generic;
using System.Diagnostics;
using ShellProgressBar;

class DEINF
{
    const string VERSION = "2.0";

    static readonly string[] CacheFolderNames =
    {
        "CLANS",
        "GLOBALS",
        "HTTP",
        "OBJECTDEFS",
        "OBJECTDYNAMIC",
        "OBJECTTHUMBS",
        "PROFILE",
        "SCENES",
        "VIDEO",
        "WORLDMAP"
    };

    private sealed class ToolConfig
    {
        public bool PauseOnExit { get; set; } = true;
        public bool Recursive { get; set; } = true;
        public bool LogInfo { get; set; } = true;
        public string DefaultLogFile { get; set; } = "log.txt";
        public string CacheLogOutputFolder { get; set; } = "INFLOGS";
        public bool SaveFiles { get; set; } = false;
        public string FileOutputFolder { get; set; } = "DECRYPTED";
    }

    private sealed class DragDropFileJob
    {
        public string FilePath { get; set; } = string.Empty;
        public string InputRoot { get; set; } = string.Empty;
        public string OutputRoot { get; set; } = string.Empty;
        public bool PreserveFolderStructure { get; set; } = false;
    }

    static void PauseIfNeeded(bool pauseOnExit)
    {
        if (!pauseOnExit)
            return;

        Console.WriteLine();
        Console.WriteLine("Press any key to close...");
        Console.ReadKey(true);
    }

    static void Main(string[] args)
    {
        string exeDir = AppContext.BaseDirectory;
        string configPath = Path.Combine(exeDir, "config-deinf.ini");

        bool useConfigFile = !HasAnyOptionArgs(args);

        ToolConfig config;

        if (useConfigFile)
        {
            EnsureConfigExists(configPath);
            config = LoadConfig(configPath);
        }
        else
        {
            config = new ToolConfig();
        }

        var easternZone = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");
        var runDate = TimeZoneInfo.ConvertTimeFromUtc(DateTime.UtcNow, easternZone).ToString("M/d/yyyy h:mm tt");

        if (args.Length < 1)
        {
            PrintUsage();
           if (useConfigFile)
               PauseIfNeeded(config.PauseOnExit);
            return;
        }

        if (useConfigFile)
        {
            RunDragDropMode(args, runDate, config, configPath, exeDir);
            PauseIfNeeded(config.PauseOnExit);
            return;
        }

        RunCommandLineMode(args, runDate);
    }

    private static bool HasAnyOptionArgs(string[] args)
    {
        if (args == null)
            return false;

        foreach (string arg in args)
        {
            if (string.IsNullOrWhiteSpace(arg))
                continue;

            if (arg.StartsWith("-", StringComparison.Ordinal) ||
                arg.StartsWith("/", StringComparison.Ordinal))
            {
                return true;
            }
        }

        return false;
    }

    private static void EnsureConfigExists(string configPath)
    {
        if (File.Exists(configPath))
            return;

        StringBuilder sb = new StringBuilder();

        sb.AppendLine("pauseonexit=true");
        sb.AppendLine("; - Pauses before closing.");
        sb.AppendLine("; ");
        sb.AppendLine("recursive=true");
        sb.AppendLine("; - Searches dropped folders recursively.");
        sb.AppendLine("; ");
        sb.AppendLine("loginfo=true");
        sb.AppendLine("; - Creates INF log output.");
        sb.AppendLine("; ");
        sb.AppendLine("defaultlogfile=log.txt");
        sb.AppendLine("; - Used when the dropped folder/file is not named CACHE.");
        sb.AppendLine("; - Takes full or relative path.");
        sb.AppendLine("; ");
        sb.AppendLine("cachelogoutputfolder=INFLOGS");
        sb.AppendLine("; - Used when the dropped folder is named CACHE.");
        sb.AppendLine("; - Takes full or relative path of folder.");
        sb.AppendLine("; - Creates separate logs based into cachelogoutputfolder based on the subfolders :");
        sb.AppendLine(";     CLANS");
        sb.AppendLine(";     GLOBALS");
        sb.AppendLine(";     HTTP");
        sb.AppendLine(";     OBJECTDEFS");
        sb.AppendLine(";     OBJECTDYNAMIC");
        sb.AppendLine(";     OBJECTTHUMBS");
        sb.AppendLine(";     PROFILE");
        sb.AppendLine(";     SCENES");
        sb.AppendLine(";     VIDEO");
        sb.AppendLine(";     WORLDMAP");
        sb.AppendLine("; ");
        sb.AppendLine("savefiles=false");
        sb.AppendLine("; - Saves decrypted INF files.");
        sb.AppendLine("; ");
        sb.AppendLine("fileoutputfolder=DECRYPTED");
        sb.AppendLine("; - Output folder used only when savefiles=true.");
        sb.AppendLine("; - Takes full or relative path of folder.");
        sb.AppendLine("; - Preserves the dropped folder structure.");
        sb.AppendLine("; ");

        File.WriteAllText(configPath, sb.ToString(), new UTF8Encoding(false));
    }

    private static ToolConfig LoadConfig(string configPath)
    {
        ToolConfig config = new ToolConfig();

        if (!File.Exists(configPath))
            return config;

        foreach (string rawLine in File.ReadLines(configPath))
        {
            string line = rawLine.Trim();

            if (line.Length == 0)
                continue;
            if (line.StartsWith(";") || line.StartsWith("#"))
                continue;
            if (line.StartsWith("[") && line.EndsWith("]"))
                continue;

            int equalsIndex = line.IndexOf('=');
            if (equalsIndex <= 0)
                continue;

            string key = line.Substring(0, equalsIndex).Trim();
            string value = line.Substring(equalsIndex + 1).Trim();

            if (key.Equals("pauseonexit", StringComparison.OrdinalIgnoreCase))
            {
                if (TryParseBool(value, out bool parsedPauseOnExit))
                    config.PauseOnExit = parsedPauseOnExit;
            }
            else if (key.Equals("recursive", StringComparison.OrdinalIgnoreCase))
            {
                if (TryParseBool(value, out bool parsedRecursive))
                    config.Recursive = parsedRecursive;
            }
            else if (key.Equals("loginfo", StringComparison.OrdinalIgnoreCase))
            {
                if (TryParseBool(value, out bool parsedLogInfo))
                    config.LogInfo = parsedLogInfo;
            }
            else if (key.Equals("defaultlogfile", StringComparison.OrdinalIgnoreCase))
            {
                config.DefaultLogFile = value;
            }
            else if (key.Equals("cachelogoutputfolder", StringComparison.OrdinalIgnoreCase))
            {
                config.CacheLogOutputFolder = value;
            }
            else if (key.Equals("savefiles", StringComparison.OrdinalIgnoreCase))
            {
                if (TryParseBool(value, out bool parsedSaveFiles))
                    config.SaveFiles = parsedSaveFiles;
            }
            else if (key.Equals("fileoutputfolder", StringComparison.OrdinalIgnoreCase))
            {
                config.FileOutputFolder = value;
            }
        }

        if (string.IsNullOrWhiteSpace(config.DefaultLogFile))
            config.DefaultLogFile = "log.txt";

        if (string.IsNullOrWhiteSpace(config.CacheLogOutputFolder))
            config.CacheLogOutputFolder = "INFLOGS";

        if (string.IsNullOrWhiteSpace(config.FileOutputFolder))
            config.FileOutputFolder = "DECRYPTED";

        return config;
    }

    private static bool TryParseBool(string value, out bool result)
    {
        if (bool.TryParse(value, out result))
            return true;

        if (string.Equals(value, "1", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(value, "yes", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(value, "y", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(value, "on", StringComparison.OrdinalIgnoreCase))
        {
            result = true;
            return true;
        }

        if (string.Equals(value, "0", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(value, "no", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(value, "n", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(value, "off", StringComparison.OrdinalIgnoreCase))
        {
            result = false;
            return true;
        }

        result = false;
        return false;
    }

    static string ResolveOutputPath(string exeDir, string pathFromConfig)
    {
        if (Path.IsPathRooted(pathFromConfig))
            return pathFromConfig;

        return Path.Combine(exeDir, pathFromConfig);
    }

    static string MakeSafeFileName(string name)
    {
        if (string.IsNullOrWhiteSpace(name))
            return string.Empty;

        foreach (char c in Path.GetInvalidFileNameChars())
            name = name.Replace(c, '_');

        return name.Trim();
    }


    static string GetCommonParentPath(List<string> paths)
    {
        if (paths == null || paths.Count == 0)
            return string.Empty;
    
        List<string> fullPaths = paths
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .Select(p =>
            {
                string full = Path.GetFullPath(p);
    
                if (File.Exists(full))
                    return Path.GetDirectoryName(full) ?? full;
    
                return full.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            })
            .ToList();
    
        if (fullPaths.Count == 0)
            return string.Empty;
    
        string[] firstParts = fullPaths[0]
            .Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    
        int commonLength = firstParts.Length;
    
        foreach (string path in fullPaths.Skip(1))
        {
            string[] parts = path.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    
            commonLength = Math.Min(commonLength, parts.Length);
    
            for (int i = 0; i < commonLength; i++)
            {
                if (!string.Equals(firstParts[i], parts[i], StringComparison.OrdinalIgnoreCase))
                {
                    commonLength = i;
                    break;
                }
            }
        }
    
        if (commonLength <= 0)
            return fullPaths[0];
    
        string common = string.Join(Path.DirectorySeparatorChar.ToString(), firstParts.Take(commonLength));
    
        if (common.EndsWith(":"))
            common += Path.DirectorySeparatorChar;
    
        return common;
    }

    static void RunDragDropMode(
        string[] args,
        string runDate,
        ToolConfig config,
        string configPath,
        string exeDir)
    {
        string defaultLogOutput = ResolveOutputPath(exeDir, config.DefaultLogFile);
        string cacheLogsRoot = ResolveOutputPath(exeDir, config.CacheLogOutputFolder);
        string decryptedRoot = ResolveOutputPath(exeDir, config.FileOutputFolder);

        int processedJobs = 0;
        List<string> normalInputs = new List<string>();
        
        foreach (string inputPath in args)
        {
            if (File.Exists(inputPath))
            {
                normalInputs.Add(inputPath);
                processedJobs++;
            }
            else if (Directory.Exists(inputPath))
            {
                string folderName = Path.GetFileName(
                    inputPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                );

                if (folderName.Equals("CACHE", StringComparison.OrdinalIgnoreCase))
                {
                    Directory.CreateDirectory(cacheLogsRoot);

                    foreach (string cacheFolderName in CacheFolderNames)
                    {
                        string subFolder = Path.Combine(inputPath, cacheFolderName);

                        if (!Directory.Exists(subFolder))
                            continue;

                        string logOutput = Path.Combine(
                            cacheLogsRoot,
                            "log_" + cacheFolderName.ToUpperInvariant() + ".txt"
                        );

                        string fileOutput = Path.Combine(decryptedRoot, "CACHE", cacheFolderName);

                        ProcessInput(
                            subFolder,
                            config.LogInfo,
                            logOutput,
                            config.SaveFiles,
                            fileOutput,
                            config.Recursive,
                            runDate,
                            args,
                            "Drag/drop CACHE\\" + cacheFolderName,
                            null,
                            false,
                            true,
                            FormatEffectiveDragDropParameters(
                                subFolder,
                                config.LogInfo,
                                logOutput,
                                config.SaveFiles,
                                fileOutput
                            )
                        );

                        processedJobs++;
                    }
                }
                else
                {
                    normalInputs.Add(inputPath);
                    processedJobs++;
                }
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("[ERROR] Input not found: " + inputPath);
                Console.ResetColor();
            }
        }

        if (normalInputs.Count > 0)
        {
          ProcessDragDropInputsAsOneLog(
              normalInputs,
              config.LogInfo,
              defaultLogOutput,
              config.SaveFiles,
              decryptedRoot,
              config.Recursive,
              runDate,
              args,
              FormatEffectiveDragDropParameters(
                  GetCommonParentPath(normalInputs),
                  config.LogInfo,
                  defaultLogOutput,
                  config.SaveFiles,
                  decryptedRoot
              ),
              GetCommonParentPath(normalInputs)
          );
        }

        if (processedJobs == 0)
        {
            Console.WriteLine("[WARNING] No valid drag/drop files or folders were processed.");
        }

        Console.WriteLine();
        Console.WriteLine("Done.");
    }

    static void RunCommandLineMode(string[] args, string runDate)
    {
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
                    if (i + 1 < args.Length)
                    {
                        logOutput = args[++i];
                    }
                    else
                    {
                        Console.WriteLine("[ERROR] -lo flag requires an output path.");
                        return;
                    }
                    break;

                case "-s":
                    saveFiles = true;
                    break;

                case "-fo":
                    if (i + 1 < args.Length)
                    {
                        fileOutput = args[++i];
                    }
                    else
                    {
                        Console.WriteLine("[ERROR] -fo flag requires an output folder.");
                        return;
                    }
                    break;

                default:
                    if (inputPath == null)
                        inputPath = args[i];
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

        ProcessInput(
            inputPath,
            logInfo,
            logOutput,
            saveFiles,
            fileOutput,
            false,
            runDate,
            args,
            null,
            preInfoLines,
            false,
            false
        );
    }

    static string FormatCommandLineArgs(string[] args)
    {
        if (args == null || args.Length == 0)
            return string.Empty;

        return string.Join(" ", args.Select(QuoteArgIfNeeded));
    }

    static string QuoteArgIfNeeded(string arg)
    {
        if (arg == null)
            return "\"\"";

        bool needsQuotes =
            arg.Length == 0 ||
            arg.Any(char.IsWhiteSpace) ||
            arg.Contains("\"");

        if (!needsQuotes)
            return arg;

        return "\"" + arg.Replace("\"", "\\\"") + "\"";
    }

    static string FormatEffectiveDragDropParameters(
        string inputPath,
        bool logInfo,
        string logOutput,
        bool saveFiles,
        string fileOutput
    )
    {
        List<string> parts = new List<string>();

        parts.Add(inputPath);

        if (logInfo)
        {
            parts.Add("-l");
            parts.Add("-lo");
            parts.Add(logOutput);
        }

        if (saveFiles)
        {
            parts.Add("-s");
            parts.Add("-fo");
            parts.Add(fileOutput);
        }

        return string.Join(", ", parts);
    }

    static void ProcessDragDropInputsAsOneLog(
        List<string> inputPaths,
        bool logInfo,
        string logOutput,
        bool saveFiles,
        string decryptedRoot,
        bool recursive,
        string runDate,
        string[] args,
        string parameterDisplayOverride,
        string primaryInputDisplay
    )
    {
        List<string> preInfoLines = new List<string>
        {
            $"DEINF Version {VERSION}",
            "Home Laboratory",
            "C# Implementation",
            $"Run Date {runDate}",
            $"Parameters: [{parameterDisplayOverride}]"
        };

        List<DragDropFileJob> fileJobs = new List<DragDropFileJob>();

        foreach (string inputPath in inputPaths)
        {
            if (File.Exists(inputPath))
            {
                if (Path.GetFileName(inputPath).Contains("_INF"))
                {
                    fileJobs.Add(new DragDropFileJob
                    {
                        FilePath = inputPath,
                        InputRoot = Path.GetDirectoryName(inputPath) ?? string.Empty,
                        OutputRoot = Path.Combine(decryptedRoot, "FILES"),
                        PreserveFolderStructure = false
                    });
                }
            }
            else if (Directory.Exists(inputPath))
            {
                string folderName = Path.GetFileName(
                    inputPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                );

                string safeFolderName = MakeSafeFileName(folderName);

                if (string.IsNullOrWhiteSpace(safeFolderName))
                    safeFolderName = "folder";

                string fileOutput = Path.Combine(decryptedRoot, safeFolderName);

                SearchOption searchOption = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;

                foreach (string file in Directory.GetFiles(inputPath, "*", searchOption)
                    .Where(f => Path.GetFileName(f).Contains("_INF")))
                {
                    fileJobs.Add(new DragDropFileJob
                    {
                        FilePath = file,
                        InputRoot = inputPath,
                        OutputRoot = fileOutput,
                        PreserveFolderStructure = true
                    });
                }
            }
        }

        if (fileJobs.Count == 0)
        {
            Console.WriteLine();
            Console.WriteLine("[WARNING] No INF files found in dropped input(s)");
            Console.WriteLine();

            if (logInfo && !string.IsNullOrWhiteSpace(logOutput))
            {
                string logDir = Path.GetDirectoryName(logOutput);

                if (!string.IsNullOrWhiteSpace(logDir))
                    Directory.CreateDirectory(logDir);

                var preInfo = preInfoLines
                    .Concat(new[] { "[WARNING] No INF files found" })
                    .ToArray();

                var postInfo = new[]
                {
                    $"Completed. Saved output to '{logOutput}'"
                };

                LogExtractor.WriteLogTable(new List<LogRow>(), logOutput, preInfo, postInfo);
            }

            return;
        }

        Console.WriteLine();
        Console.WriteLine($"Processing : {primaryInputDisplay}");
        Console.WriteLine($"INF files  : {fileJobs.Count}");

        if (logInfo && !string.IsNullOrWhiteSpace(logOutput))
        {
            string logDir = Path.GetDirectoryName(logOutput);

            if (!string.IsNullOrWhiteSpace(logDir))
                Directory.CreateDirectory(logDir);
        }

        Stopwatch swDecrypt = Stopwatch.StartNew();

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

        using (var pbar = new ProgressBar(fileJobs.Count, "Processing INF files...", options))
        {
            for (int i = 0; i < fileJobs.Count; i++)
            {
                DragDropFileJob job = fileJobs[i];
                string file = job.FilePath;

                var fileInfo = new FileInfo(file);

                if (fileInfo.Length == 0)
                {
                    errorLines.Add($"[ERROR] {Path.GetFileName(file)} has 0 bytes");
                }
                else if (fileInfo.Length > 1536)
                {
                    try
                    {
                        byte[] header = new byte[16];

                        using (var fs = new FileStream(file, FileMode.Open, FileAccess.Read))
                        {
                            fs.Read(header, 0, header.Length);
                        }

                        string headerText = System.Text.Encoding.ASCII.GetString(header);

                        if (headerText.Contains("DDS"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a DDS");
                        }
                        else if (headerText.Contains("PNG"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a PNG");
                        }
                        else if (headerText.Contains("NPD"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a SDAT");
                        }
                        else if (headerText.Contains("ftypmp42"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a VIDEO");
                        }
                        else
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is not a INF");
                        }
                    }
                    catch (Exception ex)
                    {
                        errorLines.Add($"[ERROR] Failed to read header from {Path.GetFileName(file)} — {ex.Message}");
                    }
                }
                else
                {
                    if (saveFiles)
                    {
                        string thisFileOutput = job.OutputRoot;

                        if (job.PreserveFolderStructure && Directory.Exists(job.InputRoot))
                        {
                            string relativeDir = GetRelativeDirectory(job.InputRoot, file);

                            if (!string.IsNullOrWhiteSpace(relativeDir))
                                thisFileOutput = Path.Combine(job.OutputRoot, relativeDir);
                        }

                        Directory.CreateDirectory(thisFileOutput);

                        ToolsImplementation.DecryptOrCopy(file, thisFileOutput, false);
                    }

                    if (logInfo)
                    {
                        var row = LogExtractor.ExtractLogInfo(file, errorLines);

                        if (row != null)
                            logRows.Add(row);
                    }
                }

                pbar.Tick($" {i + 1} / {fileJobs.Count} INF files processed.");
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

    static void ProcessInput(
        string inputPath,
        bool logInfo,
        string logOutput,
        bool saveFiles,
        string fileOutput,
        bool recursive,
        string runDate,
        string[] args,
        string modeLabel,
        List<string> customPreInfoLines = null,
        bool appendLog = false,
        bool preserveFolderStructure = false,
        string parameterDisplayOverride = null
        )
    {
        List<string> preInfoLines = customPreInfoLines ?? new List<string>
        {
            $"DEINF Version {VERSION}",
            "Home Laboratory",
            "C# Implementation",
            $"Run Date {runDate}",
            $"Parameters: [{(parameterDisplayOverride ?? FormatCommandLineArgs(args))}]"
        };

        List<string> files = new List<string>();

        if (File.Exists(inputPath))
        {
            if (Path.GetFileName(inputPath).Contains("_INF"))
                files.Add(inputPath);
        }
        else if (Directory.Exists(inputPath))
        {
            SearchOption searchOption = recursive ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly;

            files.AddRange(
                Directory.GetFiles(inputPath, "*", searchOption)
                    .Where(f => Path.GetFileName(f).Contains("_INF"))
            );
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
                string logDir = Path.GetDirectoryName(logOutput);

                if (!string.IsNullOrWhiteSpace(logDir))
                    Directory.CreateDirectory(logDir);

                var preInfo = preInfoLines
                    .Concat(new[] { "[WARNING] No INF files found" })
                    .ToArray();

                var postInfo = new[]
                {
                    $"Completed. Saved output to '{logOutput}'"
                };

                WriteLogTableWithOptionalAppend(
                    new List<LogRow>(),
                    logOutput,
                    preInfo,
                    postInfo,
                    appendLog
                );
            }

            return;
        }

        Console.WriteLine();
        Console.WriteLine($"Processing : {inputPath}");
        Console.WriteLine($"INF files  : {files.Count}");

        if (logInfo && !string.IsNullOrWhiteSpace(logOutput))
        {
            string logDir = Path.GetDirectoryName(logOutput);

            if (!string.IsNullOrWhiteSpace(logDir))
                Directory.CreateDirectory(logDir);
        }

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
                else if (fileInfo.Length > 1536)
                {
                    try
                    {
                        byte[] header = new byte[16];

                        using (var fs = new FileStream(file, FileMode.Open, FileAccess.Read))
                        {
                            fs.Read(header, 0, header.Length);
                        }

                        string headerText = System.Text.Encoding.ASCII.GetString(header);

                        if (headerText.Contains("DDS"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a DDS");
                        }
                        else if (headerText.Contains("PNG"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a PNG");
                        }
                        else if (headerText.Contains("NPD"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a SDAT");
                        }
                        else if (headerText.Contains("ftypmp42"))
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is a VIDEO");
                        }
                        else
                        {
                            errorLines.Add($"[ERROR] {Path.GetFileName(file)} is not a INF");
                        }
                    }
                    catch (Exception ex)
                    {
                        errorLines.Add($"[ERROR] Failed to read header from {Path.GetFileName(file)} — {ex.Message}");
                    }
                }
                else
                {
                    if (saveFiles)
                    {
                        string thisFileOutput = fileOutput;

                        if (preserveFolderStructure && Directory.Exists(inputPath))
                        {
                            string relativeDir = GetRelativeDirectory(inputPath, file);

                            if (!string.IsNullOrWhiteSpace(relativeDir))
                                thisFileOutput = Path.Combine(fileOutput, relativeDir);
                        }

                        Directory.CreateDirectory(thisFileOutput);

                        ToolsImplementation.DecryptOrCopy(file, thisFileOutput, false);
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

            WriteLogTableWithOptionalAppend(
                logRows,
                logOutput,
                preInfoLines.ToArray(),
                null,
                appendLog
            );

            swExport.Stop();

            if (errorLines.Count > 0)
            {
                File.AppendAllLines(logOutput, new[] { " " });
                File.AppendAllLines(logOutput, errorLines);
            }

            if (!appendLog)
            {
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
    }

    static string GetRelativeDirectory(string rootFolder, string filePath)
    {
        try
        {
            string root = Path.GetFullPath(rootFolder)
                .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
                + Path.DirectorySeparatorChar;

            string fileFull = Path.GetFullPath(filePath);
            string fileDir = Path.GetDirectoryName(fileFull);

            if (string.IsNullOrWhiteSpace(fileDir))
                return string.Empty;

            if (!fileDir.StartsWith(root, StringComparison.OrdinalIgnoreCase))
                return string.Empty;

            string relativeDir = fileDir.Substring(root.Length);

            return relativeDir.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        }
        catch
        {
            return string.Empty;
        }
    }

    static void WriteLogTableWithOptionalAppend(
        List<LogRow> logRows,
        string logOutput,
        string[] preInfo,
        string[] postInfo,
        bool append
    )
    {
        if (!append)
        {
            LogExtractor.WriteLogTable(logRows, logOutput, preInfo, postInfo);
            return;
        }

        string logDir = Path.GetDirectoryName(logOutput);

        if (!string.IsNullOrWhiteSpace(logDir))
            Directory.CreateDirectory(logDir);

        string tempLog = Path.Combine(
            string.IsNullOrWhiteSpace(logDir) ? Directory.GetCurrentDirectory() : logDir,
            "__deinf_temp_" + Guid.NewGuid().ToString("N") + ".txt"
        );

        LogExtractor.WriteLogTable(logRows, tempLog, preInfo, null);

        if (!File.Exists(logOutput) || new FileInfo(logOutput).Length == 0)
        {
            File.Copy(tempLog, logOutput, true);
        }
        else
        {
            List<string> existingLines = File.ReadAllLines(logOutput).ToList();
            List<string> tempLines = File.ReadAllLines(tempLog).ToList();

            string finalSeparator = tempLines.LastOrDefault(line => line.StartsWith("|=")) ?? "";

            List<string> newDataRows = tempLines
                .Where(line =>
                    line.StartsWith("| ") &&
                    !line.Contains("URI Hash") &&
                    !line.Contains("URI Path"))
                .ToList();

            int lastSeparatorIndex = existingLines.FindLastIndex(line => line.StartsWith("|="));

            if (lastSeparatorIndex >= 0)
            {
                existingLines.RemoveRange(lastSeparatorIndex, existingLines.Count - lastSeparatorIndex);
            }

            existingLines.AddRange(newDataRows);

            if (!string.IsNullOrWhiteSpace(finalSeparator))
                existingLines.Add(finalSeparator);

            File.WriteAllLines(logOutput, existingLines);
        }

        try
        {
            File.Delete(tempLog);
        }
        catch
        {
            // Ignore temp cleanup errors.
        }
    }

    static void PrintUsage()
    {  
        Console.WriteLine("DEINF2.0");
        Console.WriteLine();
        Console.WriteLine("Usage: DEINF2.0.exe <file-or-folder> [-l] [-lo logFilePath] [-s] [-fo decryptedOutputFolder]");
        Console.WriteLine("  -l         Log INF file info");
        Console.WriteLine("  -lo PATH   Output log file path (optional, default is log.txt in current folder)");
        Console.WriteLine("  -s         Save decrypted INF files");
        Console.WriteLine("  -fo PATH   Output folder for decrypted files (optional, default is DECRYPTED)");
        Console.WriteLine();
        Console.WriteLine("Examples:");
        Console.WriteLine(@"  DEINF.exe inputDir -l");
        Console.WriteLine(@"  DEINF.exe inputDir -s");
        Console.WriteLine(@"  DEINF.exe inputDir -l -lo C:\out\log.txt");
        Console.WriteLine(@"  DEINF.exe inputDir -s -fo C:\out\decrypted");
        Console.WriteLine(@"  DEINF.exe inputDir -l -s -lo log.txt -fo DECRYPTED");
        Console.WriteLine();
        Console.WriteLine("config-deinf.ini:");
        Console.WriteLine();
        Console.WriteLine("  pauseonexit=true");
        Console.WriteLine("     - Pauses before closing.");
        Console.WriteLine();
        Console.WriteLine("  recursive=true");
        Console.WriteLine("     - Searches dropped folders recursively.");
        Console.WriteLine();
        Console.WriteLine("  loginfo=true");
        Console.WriteLine("     - Creates INF log output.");
        Console.WriteLine();
        Console.WriteLine("  defaultlogfile=log.txt");
        Console.WriteLine("     - Used when the dropped folder/file is not named CACHE.");
        Console.WriteLine("     - Takes full or relative path of file.");
        Console.WriteLine();
        Console.WriteLine("  cachelogoutputfolder=INFLOGS");
        Console.WriteLine("     - Used when the dropped folder is named CACHE.");
        Console.WriteLine("     - Takes full or relative path of folder.");
        Console.WriteLine("     - Creates separate logs into cachelogoutputfolder based on the subfolders :");
        Console.WriteLine("         CLANS");
        Console.WriteLine("         GLOBALS");
        Console.WriteLine("         HTTP");
        Console.WriteLine("         OBJECTDEFS");
        Console.WriteLine("         OBJECTDYNAMIC");
        Console.WriteLine("         OBJECTTHUMBS");
        Console.WriteLine("         PROFILE");
        Console.WriteLine("         SCENES");
        Console.WriteLine("         VIDEO");
        Console.WriteLine("         WORLDMAP");
        Console.WriteLine();
        Console.WriteLine("  savefiles=false");
        Console.WriteLine("     - Saves decrypted INF files.");
        Console.WriteLine();
        Console.WriteLine("  fileoutputfolder=DECRYPTED");
        Console.WriteLine("     - Output folder used only when savefiles=true.");
        Console.WriteLine("     - Takes full or relative path of folder.");
        Console.WriteLine("     - Preserves the dropped folder structure.");
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