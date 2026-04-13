Image Organizer
A Python script to organize large collections of downloaded artwork by franchise, character, and artist — using filename parsing and reverse image search APIs.
The Problem
You've got 8,000+ images with filenames like:
3c92ff6da807182368f7aa5a93aa9a4a.jpg
7f154278ce9cc1db8b7599a7f233dc267.png
1381795_10152156746178437_7655151879560591051_n.jpg
No idea what's in them without opening each one.
The Solution
This script:

Scans your image folders
Identifies content via filename parsing + SauceNAO reverse image search
Generates a CSV for you to review before anything moves
Organizes files into a browsable folder structure

Before
Downloads/
├── 3c92ff6da807182.jpg
├── a8f2b3c9d4e5.png
└── 1381795_101521...n.jpg

After
Organized/
├── anime/
│   └── Dragon Ball/
│       └── Master Roshi/
│           └── Y Saito - Kamehameha 001.jpg
├── video_games/
│   └── Final Fantasy/
│       └── Cloud Strife/
│           └── Cloud Strife - Church 001.jpg
├── comics/
│   └── Marvel/
│       └── Deadpool/
│           └── Greg Horn - Disco with Dazzler 001.jpg
├── _nsfw/
│   └── (same structure, auto-sorted by rating)
└── _other_files/
    ├── videos/
    └── misc/
Features

Filename parsing — extracts metadata from booru-style tags, DeviantArt URLs, FurAffinity patterns
SauceNAO API integration — reverse image search for unidentified files
NSFW auto-sorting — explicit/questionable content routes to _nsfw/ folder
Non-image handling — videos, PSDs, archives go to _other_files/
CSV review step — nothing moves until you approve it
Non-destructive — copies files, never deletes originals
Duplicate detection — MD5 hash tracking

Supported File Types
TypeExtensionsImages.jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .tifVideos.mp4, .webm, .mov, .avi, .mkv, .wmv, .flv, .m4vSource files.psd, .ai, .eps, .svg, .clip, .sai, .kra, .xcfOther.pdf, .zip, .rar, .7z, .swf, .txt
Installation
Requirements

Python 3.10+
pip

Setup
bashgit clone https://github.com/jeflint-auth/image-organizer.git
cd image-organizer
pip install -r requirements.txt
Configuration
Edit config.json:
json{
    "source_directory": "G:\\My Drive\\Images",
    "output_directory": "G:\\My Drive\\Worked Images",
    "csv_output": "image_mapping.csv",
    "saucenao_api_key": "YOUR_API_KEY_HERE",
    "min_similarity": 70.0
}
Get a free SauceNAO API key at: https://saucenao.com/user.php?page=search-api
Usage
Step 1: Scan (filename parsing only — fast)
bashpython image_organizer.py --mode scan --skip-api
Step 2: Scan with API (slower, better identification)
bashpython image_organizer.py --mode scan --max-api 200
Step 3: Review the CSV
Open image_mapping.csv in Excel or any spreadsheet app. Check the mappings, fix any errors.
Step 4: Execute
bashpython image_organizer.py --mode execute
Command Reference
FlagDescription--mode scanScan files and generate CSV--mode executeCopy files based on CSV--mode fullScan, pause for review, then execute--skip-apiFilename parsing only (no API calls)--max-api NLimit to N API requests--config FILEUse alternate config file--csv FILEUse alternate CSV file for execute
CSV Columns
ColumnDescriptionoriginal_pathCurrent file locationnew_full_pathDestination pathconfidencehigh / medium / low / noneneeds_reviewyes / noratingsafe / questionable / explicit / unknownorigin_mediaanime / video_games / comics / etc.seriesFranchise namecharactersCharacter names (semicolon-separated)artistArtist name if identifiedfile_hashMD5 hash for duplicate detection
Folder Structure Rules

Origin — top level by media type (anime, video_games, comics, etc.)
Publisher — for comics (Marvel, DC, Image)
Series — franchise name
Characters — solo: Cloud Strife/, duo: Usagi & Chibiusa/, 3+: Group/
Misc — subfolder when artist is unknown
Filename — [Artist] - [Character] - [Description] 001.jpg

API Limits
SauceNAO Free Tier:

200 searches/day
6 seconds between requests

For large collections, run filename parsing first (--skip-api), then chip away at unknowns with --max-api 200 over multiple days.
Safety

Non-destructive — always copies, never moves or deletes
CSV review — you approve everything before execution
Originals untouched — delete them manually only when satisfied

Contributing
Issues and PRs welcome. This was built for a specific use case (organizing years of downloaded fanart) but should be adaptable.
License
MIT
Acknowledgments

SauceNAO for reverse image search API
Built with assistance from Claude (Anthropic)
