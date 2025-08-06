# PSHome Cache Extractor
## PlayStation®Home Cache Logger

For each data file within a PlayStation®Home CACHE, there is an associated "INF" file of the same name. Each INF file includes the data file’s original path, file name, and, in many cases, a date.

Some INF files are encrypted, while others from older versions of PlayStation®Home are already decrypted.

The purpose of this logger is to decrypt encrypted INF files, log and clean up all INF contents, and then map (copy) the data to its original CDN path structure.

The batch script serves as the main controller, leveraging various supplemental scripts/programs.

With that in mind, this PSHome Cache Extractor is only supported on Windows x64/x86 systems.

> [!NOTE]
> Only supports Windows x64/x86 .

> [!IMPORTANT]
> 1) The ffprobe.exe may get falsely picked up by Discord and Google Drive antivirus. 
> 2) Due to the EXEs not being signed with a CA ( Certificate Authority ) certificate ( which costs a fortune ), some antivirus may falsely detect it falsely as a virus unfortunately.

The PlayStation®Home Cache Logger was put together by Rew from the Home Laboratory Playstation Home Revival Group.

Discord -> https://dsc.gg/homelaboratory

## Usage Overview

In all scenarios, it looks for ```\NPIA00005\USRDIR\CACHE```. 

It does support HDK ```NPIA00010``` and ```NPEA00013``` beta caches as well just in case.

```Examples:
Rew's Cache\NPIA00005\USRDIR\CACHE
TSFRJ Home Cache 1.80\NPIA00005\USRDIR\CACHE
```
**Scenarios it supports :**

**Single Cache Mode :**

Caches/     
├── BIN/    
├── Cache Folder/   
│   └── NPIA00005/  
│       └── CACHE_EXTRACTORVX.X.X.BAT  ← CLICK ME   

**Unlimited Cache Mode - Combined :**

Caches/  
├── BIN/    
├── Rew's Cache/PIA00005/  
├── Rew's Cache/Rew's Cache/PIA00005/  
├── TSFRJ Home Cache 1.80/NPIA00005/  
├── TSFRJ Home Cache 1.80/TSFRJ Home Cache 1.80/NPIA00005/  
└── CACHE_EXTRACTORVX.X.X.BAT  ← CLICK ME   

**Unlimited Cache Mode - Separate :**

Caches/     
├── BIN/    
├── Rew's Cache/NPIA00005/  
├── Rew's Cache/Rew's Cache/NPIA00005/  
├── TSFRJ Home Cache 1.80/NPIA00005/  
├── TSFRJ Home Cache 1.80/TSFRJ Home Cache 1.80/NPIA00005/  
└── CACHE_EXTRACTORVX.X.X.BAT  ← CLICK ME

## Supplemental Scripts

The batch script calls the following scripts, all of which are required for proper operation :

1) BIN\DEFINF2.0\DEINF2.0.exe - C# INF decrypter and logger
	
	- Github repositories utilized :
		
	  1) MultiServer3 -> https://github.com/GitHubProUser67/MultiServer3

         - ToolsImplentation.cs, HomeToolsInterface.cs, StringUtils.cs, CharUtils.cs, ByteUtils.cs, & LIBSECRE.cs
	  3) BouncyCastle -> https://github.com/bcgit/bc-csharp
	  4) ShellProgressBar -> https://github.com/Mpdreamz/shellprogressbar
   
   - The DEINF2.0.exe uses Net 6 -> https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/sdk-6.0.428-windows-x64-installer
    
2) Python based EXEs built from the CX-Freeze Python library.
    - CX-Freeze Info -> https://cx-freeze.readthedocs.io/en/stable/ )
    - Python 3.11 itself gets bundled into the BIN\PSHomeCacheTools\lib\ folder.
    - The Pillow Python Library is also utilized here. ( https://pypi.org/project/pillow/ )
	
    - BIN\PSHomeCacheTools\   
    ├── file_analysis.exe   
    ├── check_for_new_objects.exe   
    ├── cache_copy_single.exe   
    ├── cache_copy_combined.exe   
    ├── log_sdats.exe   
    ├── log_thumbnails.exe  
    ├── merge_inflogs.exe   
    └── custom_query.exe

3) BIN\ffprobe.exe
   - Download -> https://github.com/BtbN/FFmpeg-Builds/releases
   - Info -> https://www.ffmpeg.org/ffprobe.html )

4) BIN\JREPL\JREPL.BAT - Batch/Jscript Hybrid
   - Created by dbenham https://stackoverflow.com/users/1012053/dbenham )
	
		
