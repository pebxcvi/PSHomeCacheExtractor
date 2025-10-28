# PSHome Cache Extractor

## PlayStation®Home Cache Logger
...

> [!IMPORTANT]
> Download Release -> https://github.com/pebxcvi/PSHomeCacheExtractor/releases/tag/v3.5.6

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
   - Created by dbenham -> https://stackoverflow.com/users/1012053/dbenham
		
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
- Used prior to OBJECTDYNAMIC in super old versions
- Dynamic Media from Objects
    - Message Of The Day content
    - Music
    - Commerce Point ( Store ) thumbnails
    - Object thumbnails
    - Various Screen/Poster content ( Images )

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
```

## Encryption Overview
...

> [!NOTE]
> Code -> https://github.com/GitHubProUser67/MultiServer3/tree/Super-Branch/AuxiliaryServices/HomeTools

...

### 1) INF files
- Encrypted with Libsecure Blowfish using a unique keyset

### 2) SceneList.XML
- Encrypted with Libsecure Blowfish using a unique keyset

### 3) Scene Descriptor Files 
- SceneSDATName_TXXX.SDC
- XML; Encrypted with Libsecure Blowfish using a unique keyset

### 4) Object Descriptor Files
- Object_TXXX.ODC
- XML; Encrypted with Libsecure Blowfish using a unique keyset

### 5) Navigator_*region*.XML
- Encrypted prior to April 2011 with Libsecure Blowfish using a unique keyset
- Not encrypted from Mid-April 2011 onwards

### 6) ProfanityDictionary_*lang*.BIN
- Binary BIN from what we beleive to be from a program apart of the PS3 SDK
- Earlier Profanity Dictionaries were XXTEA encrypted with a static key and served directly from the scee-home.playstation.net and secure.cprod.homeps3.online.scee.com domains
- Newer Profanity Dictionaries were AES128 encrypted .EBIN's and served via the profanityfilter API updater service under the update-prod.pfs.online.scee.com domain. The API was configured within the TSS file

### 7) ObjectCatalogue_5_*region*.HCDB
- SQLite database ( .SQL )
- Encrypted with Libsecure Blowfish using a unique keyset and compressed with EdgeLzma ( SEGS )
- Used from Mid-November 2010 onwards

### 8) ObjectCatalogue.BAR
- BAR Archive; Encrypted with Libsecure Blowfish using a unique keyset
- The BAR Archive contains a single XML
- Used prior to November 2010

### 9) Scenes and Objects

**`BAR Archive :`**

- Not encrypted; No Sony NPDRM encryption
- Only found in HDK/QA versions
- LUA files inside were not encrypted

**`SDAT Archive :`**

- **BAR Archive with Sony NPDRM encryption only; Used prior to October 2013**

    - SDATA V2.4 and V2.2

    - From version 1.35 onwards, LUA files were encrypted using an Encryption Proxy layer that applied Blowfish-based encryption and EdgeZlib compression. It was indicated by a flag in the TOC ( Table of Contents )

- **BAR Archive with Sony NPDRM and SHARC encryption; Used Mid-October 2013 onwards**

    - SDATA V4.0 and V2.4

    - SHARC encryption consists of three layers :

        **`Layer 1:`** AES256 encryption applied to both the Header ( Metadata section at the beginning of each archive ) and the TOC ( Table of Contents; lookup table containing metadata such as file offsets, sizes, compression types, along with the Keys and IVs used for the custom XTEA encryption ). The Header is decrypted first using AES256, followed by the TOC. The TOC is then decrypted with the same AES key and an incremented IV to reveal each file's Key and IV used in the custom XTEA encryption

        **`Layer 2:`** Custom XTEA encryption applied individually to each file using its own unique Key and IV ( Values retrieved from the decrypted TOC )

        **`Layer 3:`** EdgeZlib compression applied to each file's data prior to encryption

    - LUA files were encrypted in an additional Blowfish-based layer indicated by a flag in the TOC

### 10) Configs_*lang*.SHARC
- BAR Archive with SHARC encryption described above
- Used Mid-September 2013 onwards
- Contains a ProfanityDictionary_*lang*.BIN encrypted with Libsecure XXTEA using a unique keyset

### 11) Configs_*lang*.BAR
- BAR Archive; Not encrypted
- Used prior to September 2013
- Contains a ProfanityDictionary_*lang*.BIN encrypted with Libsecure XXTEA using a unique keyset
   
### 12) Core Files

<details>
<summary><b>RETAIL - OPEN BETA</b></summary>
-
	
**`BAR ARCHIVES WITH SHARC ENCRYPTION :`**
| Version | Title ID | Archives | Cache References | PKG References | 
|----------|-----------|----------|----------|----------|
| 1.87 | NPIA00005 | COREDATA.SHARC<br>SHADERS.SHARC ||NPIA00005 01.87.pkg|
| 1.86 | NPIA00005 | COREDATA.SHARC<br>SHADERS.SHARC<br>SCENE_APARTMENT.SHARC<br>CORE_OBJECTS.SHARC ||NPIA00005 01.86.pkg|
| 1.85 | NPIA00005 | COREDATA.SHARC<br>SHADERS.SHARC<br>SCENE_APARTMENT.SHARC ||NPIA00005 01.85.pkg|
| 1.82 | NPIA00005 | COREDATA.SHARC<br>SHADERS.SHARC<br>SCENE_APARTMENT.SHARC ||NPIA00005 01.82.pkg|


**`BAR ARCHIVES WITH NO ENCRYPTION :`**
| Version | Title ID | Archives | Cache References | PKG References | 
|----------|-----------|----------|----------|----------|
| 1.81 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR |
| 1.80 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR |
| 1.75 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR ||NPIA00005 01.75.pkg|
| 1.70 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR |
| 1.66 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR |
| 1.65 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR |
| 1.62 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR |
| 1.61 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR |
| 1.55 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR |
| 1.52 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR |
| 1.51 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR |
| 1.50 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR |
| 1.41 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR ||NPIA00005 01.41.pkg|
| 1.40 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR |
| 1.36 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR |
| 1.35 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR ||NPIA00005 01.35.pkg|
| 1.32 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR |
| 1.30 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR |MrJunezJP2
| 1.22 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR<br>ARCADEPUZZLE.BAR<br>CHESS_DRAUGHTS.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>JAVA.BAR |StratosA<br>Rew13<br>Spbuilder
| 1.11 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR<br>ARCADEPUZZLE.BAR<br>CHESS_DRAUGHTS.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>JAVA.BAR |ModdedWarfare<br>Dark-Star_1337
| 1.10 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR<br>ARCADEPUZZLE.BAR<br>CHESS_DRAUGHTS.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>JAVA.BAR<br>OBJECTS_DEFAULT_AVATAR.BAR |Joe1452|NPIA00005 01.10.pkg|
| 1.05 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR<br>ARCADEPUZZLE.BAR<br>CHESS_DRAUGHTS.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>JAVA.BAR<br>OBJECTS_DEFAULT_AVATAR.BAR |NovaDaemon1.05<br>Cypher2

</details>

<details>
<summary><b>RETAIL - CLOSED BETA</b></summary>
-
	
**`BAR ARCHIVES WITH NO ENCRYPTION :`**
| Version | Title ID | Archives | Cache References | PKG References |
|----------|-----------|----------|----------|----------|
| 1.02 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR<br>ARCADEPUZZLE.BAR<br>CHESS_DRAUGHTS.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>JAVA.BAR<br>OBJECTS_DEFAULT_AVATAR.BAR | | NPIA00005 01.02.pkg |
| 1.00 | NPIA00005 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>POOL_BOWLING.BAR<br>DYNFILES.BAR<br>SPURIOUS.BAR<br>ARCADEPUZZLE.BAR<br>CHESS_DRAUGHTS.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>JAVA.BAR<br>OBJECTS_DEFAULT_AVATAR.BAR | | NPIA00005 01.00.pkg |
| 0.98 | NPIA00005 | NPBOOT.BAR<br>DYNFILES.BAR<br>SHADERS.BAR<br>JAVA.BAR<br>SCENE_APARTMENT.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>OBJECTS_DEFAULT_AVATAR.BAR<br>ARCADEBOUNCER.BAR<br>ARCADESTOCKCAR.BAR<br>ARCADEEVAC.BAR<br>ARCADEPUZZLE.BAR | | NPIA00005 00.98.pkg |
| 0.94 | NPEA00013 | NPBOOT.BAR<br>DYNFILES.BAR<br>SHADERS.BAR<br>JAVA.BAR<br>SCENE_APARTMENT.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>OBJECTS_DEFAULT_AVATAR.BAR<br>ARCADEBOUNCER.BAR<br>ARCADESTOCKCAR.BAR<br>ARCADEEVAC.BAR<br>ARCADEPUZZLE.BAR | | NPEA00013 Beta 00.94.pkg |
| 0.83 | NPIA00005 | NPBOOT.BAR<br>DYNFILES.BAR<br>SHADERS.BAR<br>JAVA.BAR<br>SCENE_APARTMENT.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>OBJECTS.BAR<br>ARCADEBOUNCER.BAR<br>ARCADESTOCKCAR.BAR<br>ARCADEEVAC.BAR<br>ARCADEPUZZLE.BAR | | NPIA00005 00.83.pkg |

</details>

<details>
<summary><b>RETAIL - LIMITED TIME BETA</b></summary>
-
	
**`BAR ARCHIVES WITH SHARC ENCRYPTION :`**
| Version | Title ID | Archives | Cache References | PKG References |
|----------|-----------|----------|----------|----------|
| 1.82 | NPEA00013 | COREDATA.SHARC<br>SHADERS.SHARC<br>SCENE_APARTMENT.SHARC | Soul2 |

**`BAR ARCHIVES WITH NO ENCRYPTION :`**
| Version | Title ID | Archives | Cache References | PKG References |
|----------|-----------|----------|----------|----------|
| 1.75 | NPEA00013 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR | JrMans2<br>Megalia |

</details>

<details>
<summary><b>GDC DEMO</b></summary>
-
	
**`BAR ARCHIVES WITH NO ENCRYPTION :`**
| Version | Title ID | Archives | Cache References | PKG References |
|----------|-----------|----------|----------|----------|
| 0.41 | NPEA00013 | NPBOOT.BAR<br>DYNFILES.BAR<br>SHADERS.BAR<br>JAVA.BAR<br>CHARACTERS.BAR<br>FURNITURE.BAR<br>SCENE_APARTMENT.BAR<br>SCENE_CENTRAL_LOBBY.BAR<br>SCENE_CINEMA.BAR<br>SCENE_CINEMA_AUDITORIUM.BAR<br>SCENE_GAMES_ROOM.BAR<br>ARCADEBLACKHOLE.BAR<br>ARCADECARRIAGERETURN.BAR<br>ARCADECONTINUUM.BAR<br>ARCADEEVAC.BAR<br>ARCADERUBBERBOB.BAR<br>ARCADESTOCKCAR.BAR | GoldenFields | NPEA00013 Beta GDC Demo 2007 0.41.pkg |

</details>

<details>
<summary><b>DEVELOPER - HDK</b></summary>
-
	
**`BAR ARCHIVES WITH NO ENCRYPTION :`**

| Version | Title ID | Archives | Cache References | PKG References | 
|----------|-----------|----------|----------|----------|
| 1.86 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>CONFIG_HDK.BAR<br>DEV_ARCHIVE.BAR|QuantumDoja2<br>Soul4DECH2500|HomeDeveloperBuild186.pkg|
| 1.82 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>CONFIG_HDK.BAR<br>DEV_ARCHIVE.BAR|PixelButts|
| 1.80 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>CONFIG_HDK.BAR<br>DEV_ARCHIVE.BAR||HomeDeveloperBuild_180.pkg|
| 1.75 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>CONFIG_HDK.BAR<br>DEV_ARCHIVE.BAR||HomeDeveloperBuild_175.pkg|
| 1.70 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>CONFIG_HDK.BAR<br>DEV_ARCHIVE.BAR||Home.DeveloperBuild_1.70.pkg|
| 1.66 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>CONFIG_HDK.BAR<br>DEV_ARCHIVE.BAR<br>POOL_BOWLING.BAR||Home.DeveloperBuild_1.66.pkg|
| 1.65 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>CONFIG_HDK.BAR<br>DEV_ARCHIVE.BAR<br>POOL_BOWLING.BAR||Home.DeveloperBuild_BETA_1.65.pkg|
| 1.62 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>DEV_ARCHIVE.BAR<br>POOL_BOWLING.BAR||Home.DeveloperBuild_1.62.pkg|
| 1.60 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>LOCAL_CORE_OBJECTS.BAR<br>DEV_ARCHIVE.BAR<br>POOL_BOWLING.BAR|Spounts|
| 1.41 | NPIA00010 | COREDATA.BAR<br>HADERS.BAR<br>SCENE_APARTMENT.BAR<br>DEV_ARCHIVE.BAR<br>POOL_BOWLING.BAR<br>SPURIOUS.BAR<br>DYNFILES.BAR<br>OBJECTS_DEFAULT_INVENTORY.BAR|Dusty_3|
| 1.35 | NPIA00010 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>DEV_ARCHIVE.BAR<br>POOL_BOWLING.BAR<br>SPURIOUS.BAR<br>DYNFILES.BAR<br>OBJECTS_DEFAULT_INVENTORY.BAR||Home.DeveloperBuild_BETA_1.3.5.pkg| 
| 1.32 | NPEA00013 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>DEV_ARCHIVE.BAR<br>POOL_BOWLING.BAR<br>SPURIOUS.BAR<br>DYNFILES.BAR<br>OBJECTS_DEFAULT_INVENTORY.BAR|SingStar<br>Developer|
| 1.00 | NPEA00013 | COREDATA.BAR<br>SHADERS.BAR<br>SCENE_APARTMENT.BAR<br>OBJECTS_DEV.BAR<br>POOL_BOWLING.BAR<br>SPURIOUS.BAR<br>DYNFILES.BAR<br>JAVA.BAR<br>OBJECTS_DEFAULT_INVENTORY.BAR<br>CHESS_DRAUGHTS.BAR|Dusty_2|


</details>
<details>
<summary><b>DEVELOPER - QA</b></summary>
-
	
**`BAR ARCHIVES WITH SHARC ENCRYPTION :`**
| Version | Title ID | Archives | Cache References | PKG References | 
|----------|-----------|----------|----------|----------|
| 1.86 | NPIA00005 | COREDATA.SHARC<br>SHADERS.SHARC<br>SCENE_APARTMENT.SHARC<br>CORE_OBJECTS.SHARC |QuantumDoja1|
| 1.85 | NPIA00005 | COREDATA.SHARC<br>SHADERS.SHARC<br>SCENE_APARTMENT.SHARC |Soul3|

</details>
