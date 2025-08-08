# PSHome Cache Extractor

## PlayStation®Home Cache Logger
...

> [!IMPORTANT]
> Download Release -> https://github.com/pebxcvi/PSHomeCacheExtractor/releases/tag/v3.5.5

...
## Overview

For each data file within a PlayStation®Home Cache, there is an associated "INF" file of the same name. Each INF file includes the data file’s original path, file name, and, in many cases, a date.

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

## Usage

In all scenarios, it looks for ```\NPIA00005\USRDIR\CACHE```. 

It does support HDK ```NPIA00010``` and ```NPEA00013``` Beta Caches as well just in case.

```Examples:
Rew's Cache\NPIA00005\USRDIR\CACHE
TSFRJ Home Cache 1.80\NPIA00005\USRDIR\CACHE
```
**Scenarios it supports :**

### Single Cache Mode
```
Caches/     
├── BIN/    
├── Cache Folder/   
│ └── NPIA00005/  
│ └── CACHE_EXTRACTORVX.X.X.BAT  ← CLICK ME   
```
<img src="https://github.com/pebxcvi/PSHomeCacheExtractor/blob/main/SingleCacheMode.png" alt="SingleCacheMode.png" width="500">

### Unlimited Cache Mode

<img src="https://github.com/pebxcvi/PSHomeCacheExtractor/blob/main/UnlimitedCacheMode.png" alt="UnlimitedCacheMode.png" width="500">

### Unlimited Cache Mode - Separate

```
Caches/     
├── BIN/    
├── Rew's Cache/NPIA00005/  
├── Rew's Cache/Rew's Cache/NPIA00005/  
├── TSFRJ Home Cache 1.80/NPIA00005/  
├── TSFRJ Home Cache 1.80/TSFRJ Home Cache 1.80/NPIA00005/  
└── CACHE_EXTRACTORVX.X.X.BAT  ← CLICK ME
```
<img src="https://github.com/pebxcvi/PSHomeCacheExtractor/blob/main/UnlimitedCacheModeSeparate.png" alt="UnlimitedCacheModeSeparate.png" width="500">

### Unlimited Cache Mode - Combined
```
Caches/  
├── BIN/    
├── Rew's Cache/PIA00005/  
├── Rew's Cache/Rew's Cache/PIA00005/  
├── TSFRJ Home Cache 1.80/NPIA00005/  
├── TSFRJ Home Cache 1.80/TSFRJ Home Cache 1.80/NPIA00005/  
└── CACHE_EXTRACTORVX.X.X.BAT  ← CLICK ME   
```
<img src="https://github.com/pebxcvi/PSHomeCacheExtractor/blob/main/UnlimitedCacheModeCombined.png" alt="UnlimitedCacheModeCombined.png" width="500">

## Public Cache Archive

https://github.com/pebxcvi/PSHomeCacheDepot

A vast majority of PlayStation®Home raw caches are archived publicly in this google drive with logs included. ( [Google Drive](https://drive.google.com/drive/u/1/folders/1Wuk2GNsXOZ_qLJFqtg0gExRpZqxL3sec) )

You can find individual download links here. ( [Google Sheets](https://docs.google.com/spreadsheets/d/1uR7IRGjkl_n5CMBua6zIQV5EKXdSk8_D-sTDoJGMe7c/edit?usp=sharing) ) 

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
    - CX-Freeze Info -> https://cx-freeze.readthedocs.io/en/stable/
    - Python 3.11 itself gets bundled into the BIN\PSHomeCacheTools\lib\ folder.
    - The Pillow Python Library is also utilized here -> https://pypi.org/project/pillow/
	
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
   - Info -> https://www.ffmpeg.org/ffprobe.html

4) BIN\JREPL\JREPL.BAT - Batch/Jscript Hybrid
   - Created by dbenham https://stackoverflow.com/users/1012053/dbenham
		
## Cache Breakdown

### Folder Definitions

**```CLANS```**
- Clubhouse Furniture Layout XMLs & Clubhouse Save Data XMLs from older PlayStation®Home versions.

**```GLOBALS```** 
- Core files 
    - SceneList XMLs
    - ObjectCatalogue ( BAR OR HCDB )
    - DefaultInventory ( BAR )
    - Configs ( BAR OR SHARC )
    - Profanity Dictionary ( BIN )
    - Navigator/NavigatorRoot XMLs
    - ServiceIds XMLs 
    - RegionMap XMLs
- Screen Link XMLs
- Message Of The Day XMLs or TXTs
- Commerce Point ( Store ) XMLs & thumbnails

**```HTTP```**

**```OBJECTDEFS```**

- Objects ( SDAT OR BAR ) & their descriptor files ( ODC )

**```OBJECTDYNAMIC```**
- Dynamic Media from Objects
    - Message Of The Day content
    - Music
    - Commerce Point ( Store ) thumbnails
    - Object thumbnails
    - Various Screen/Poster content ( Images )

**```PROFILE```**
								
- Avatar headshots from the Save Data Service
- PSN Profile Avatar Images
- Misc Profile setting XMLs from older PlayStation®Home versions

**```SCENES```**							
- Scenes ( SDAT OR BAR ) & their descriptor files ( SDC )
- Scene thumbnails
- Scene Version XMLs

**```VIDEO```**
- Various Screen/Poster content ( Videos & Images )					

**```WORLDMAP```**							
- Navigator content 
- Scene thumbnails 

### Folder Structures

**Example of the Cache structure :**
```
USRDIR/CACHE/   
├── SETTINGS
│   
├── CLANS/  
│ └──STATE  
│ └──RESERVED  
│   
├── GLOBALS/    
│ └──1125735730_INF  
│ └──1125735730_DAT.XML  
│ └──STATE      
│ └──RESERVED 
│  
├── HTTP/   
│ └──STATE  
│ └──RESERVED
│      
├── OBJECTDEFS/     
│ └──10122905_INF   
│ └──10122905_DAT.ODC   
│ └──11028318_INF   
│ └──11028318_DAT.sdat  
│ └──STATE  
│ └──RESERVED 
│  
├── OBJECTDYNAMIC/  
│ └──220756008_INF  
│ └──220756008_DAT.DDS  
│ └──STATE  
│ └──RESERVED
│   
├── OBJECTTHUMBS/   
│ └──15244468_INF   
│ └──15244468_DAT.PNG   
│ └──STATE  
│ └──RESERVED
│   
├── PROFILE/    
│ └──1491203350_INF  
│ └──1491203350_DAT.JPG     
│ └──STATE    
│ └──RESERVED 
│  
├── SCENES/     
│ └──25932842_INF      
│ └──25932842_DAT.SDC   
│ └──45060018_INF      
│ └──45060018_DAT.sdat  
│ └──STATE     
│ └──RESERVED
│   
├── VIDEO/      
│ └──1038606639_INF        
│ └──1038606639_DAT.MP4  
│ └──STATE      
│ └──RESERVED
│   
├── WORLDMAP/   
│ └──657739169_INF  
│ └──657739169_DAT.DDS  
│ └──STATE  
│ └──RESERVED   
```		
### File Extensions

**Known file extensions in Cache :**

```
.sdat
.bar
.odc
.sdc
.hcdb
.txt
.xml
.mp4
.m4v
.mp3
.dds
.png
.jpg
.jpeg
.bin
.do
.hsml
.dat
