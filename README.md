# Image Organizer

A Python script to organize large collections of downloaded artwork by franchise, character, and artist — using filename parsing and reverse image search APIs.

## The Problem

You've got 8,000+ images with filenames like:
```
3c92ff6da807182368f7aa5a93aa9a4a.jpg
7f154278ce9cc1db8b7599a7f233dc267.png
1381795_10152156746178437_7655151879560591051_n.jpg
```

No idea what's in them without opening each one.

## The Solution

This script:
1. **Scans** your image folders
2. **Identifies** content via filename parsing + SauceNAO reverse image search
3. **Generates a CSV** for you to review before anything moves
4. **Organizes** files into a browsable folder structure

### Before
```
Downloads/
├── 3c92ff6da807182.jpg
├── a8f2b3c9d4e5.png
└── 1381795_101521...n.jpg
```

### After
```
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
├── crossovers/
│   └── Group/
│       └── Artist - Group 001.jpg
├── _unsorted/
│   ├── by_artist/
│   │   └── ArtistName/
│   └── unknown/
├── _nsfw/
│   └── (same structure, auto-sorted by rating)
└── _other_files/
    ├── videos/
    └── misc/
```

## Features

- **Filename parsing** — extracts metadata from booru-style tags, DeviantArt URLs, FurAffinity patterns
- **SauceNAO API integration** — reverse image search for unidentified files
- **Crossover detection** — images with characters from multiple franchises route to `crossovers/`
- **Series aliases** — converts Japanese titles to English (e.g., Kyatto Ninden Teyandee → Samurai Pizza Cats)
- **NSFW auto-sorting** — explicit/questionable content routes to `_nsfw/` folder
- **Non-image handling** — videos, PSDs, archives go to `_other_files/`
- **Folder exclusions** — skip folders you don't want processed (your own projects, already-organized folders)
- **Smart review flagging** — flags artist-only results, non-ASCII names, and low-confidence matches
- **CSV review step** — nothing moves until you approve it
- **Non-destructive** — copies files, never deletes originals
- **Duplicate detection** — MD5 hash tracking

## Supported File Types

| Type | Extensions |
|------|------------|
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.tif` |
| Videos | `.mp4`, `.webm`, `.mov`, `.avi`, `.mkv`, `.wmv`, `.flv`, `.m4v` |
| Source files | `.psd`, `.ai`, `.eps`, `.svg`, `.clip`, `.sai`, `.kra`, `.xcf` |
| Other | `.pdf`, `.zip`, `.rar`, `.7z`, `.swf`, `.txt` |

## Installation

### Requirements
- Python 3.10+
- pip

### Setup
```bash
git clone https://github.com/jeflint-auth/image-organizer.git
cd image-organizer
pip install -r requirements.txt
```

### Configuration
Edit `config.json`:
```json
{
    "source_directory": "G:\\My Drive\\Images",
    "output_directory": "G:\\My Drive\\Worked Images",
    "csv_output": "image_mapping.csv",
    "saucenao_api_key": "YOUR_API_KEY_HERE",
    "min_similarity": 70.0,
    "excluded_folders": ["My Projects", "Already Sorted", "Chronicles of Loth"]
}
```

**Config Options:**
| Option | Description |
|--------|-------------|
| `source_directory` | Folder to scan for images |
| `output_directory` | Where organized files will be copied |
| `csv_output` | Name of the mapping CSV file |
| `saucenao_api_key` | Your SauceNAO API key |
| `min_similarity` | Minimum match confidence (0-100, default 70) |
| `excluded_folders` | List of folder names to skip during scan |

Get a free SauceNAO API key at: https://saucenao.com/user.php?page=search-api

## Usage

### Step 1: Scan (filename parsing only — fast)
```bash
python image_organizer.py --mode scan --skip-api
```

### Step 2: Scan with API (slower, better identification)
```bash
python image_organizer.py --mode scan --max-api 200
```

### Step 3: Review the CSV
Open `image_mapping.csv` in Excel or any spreadsheet app. Check the mappings, fix any errors.

**Review Tips:**
- Filter by `needs_review = yes` to see flagged items
- Check `notes` column for context (e.g., "Non-English artist name - consider romanizing")
- Manually correct artist names, series, or origin_media as needed

### Step 4: Execute
```bash
python image_organizer.py --mode execute
```

## Command Reference

| Flag | Description |
|------|-------------|
| `--mode scan` | Scan files and generate CSV |
| `--mode execute` | Copy files based on CSV |
| `--mode full` | Scan, pause for review, then execute |
| `--skip-api` | Filename parsing only (no API calls) |
| `--max-api N` | Limit to N API requests |
| `--config FILE` | Use alternate config file |
| `--csv FILE` | Use alternate CSV file for execute |

## CSV Columns

| Column | Description |
|--------|-------------|
| `original_path` | Current file location |
| `new_full_path` | Destination path |
| `confidence` | `high` / `medium` / `low` / `none` |
| `needs_review` | `yes` / `no` — flagged for manual review |
| `rating` | `safe` / `questionable` / `explicit` / `unknown` |
| `origin_media` | `anime` / `video_games` / `comics` / `crossovers` / etc. |
| `series` | Franchise name |
| `characters` | Character names (semicolon-separated) |
| `artist` | Artist name if identified |
| `notes` | Source URL, warnings, and context |
| `file_hash` | MD5 hash for duplicate detection |

## Folder Structure Rules

- **Origin** — top level by media type (anime, video_games, comics, furries, crossovers)
- **Publisher** — for comics (Marvel, DC, Image, Dark Horse)
- **Series** — franchise name
- **Characters** — solo: `Cloud Strife/`, duo: `Usagi & Chibiusa/`, 3+: `Group/`
- **Filename** — `[Artist] - [Character] - [Description] 001.jpg`

**Special Folders:**
- `crossovers/` — images mixing characters from different franchises
- `_unsorted/by_artist/` — Pixiv results with only artist info
- `_unsorted/unknown/` — couldn't identify anything
- `_nsfw/` — mirrors full structure for explicit/questionable content
- `_other_files/videos/` and `_other_files/misc/` — non-image files

## API Limits

**SauceNAO Free Tier:**
- 200 searches/day
- ~10-12 seconds between requests

**SauceNAO Enhanced ($62/year):**
- 5,000 searches/day

For large collections (30,000+ files), consider the enhanced tier. Otherwise, run filename parsing first (`--skip-api`), then chip away at unknowns with `--max-api 200` over multiple days.

## Safety

- **Non-destructive** — always copies, never moves or deletes
- **CSV review** — you approve everything before execution
- **Originals untouched** — delete them manually only when satisfied

## Contributing

Issues and PRs welcome. This was built for a specific use case (organizing years of downloaded fanart) but should be adaptable.

## License

MIT

## Acknowledgments

- [SauceNAO](https://saucenao.com/) for reverse image search API
- Built with assistance from Claude (Anthropic)
