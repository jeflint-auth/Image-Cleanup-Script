# Image Organizer Setup Guide

This guide walks you through setting up and running the image organizer script on Windows 10.

---

## Prerequisites

- **Python 3.10+** (you mentioned having 3.14, that's perfect)
- **Notepad++** (for editing config files)
- **Internet connection** (for API calls)

---

## Step 1: Download the Script Files

Create a folder for the script. I recommend:

```
C:\Scripts\ImageOrganizer\
```

Place these files in that folder:
- `image_organizer.py` (the main script)
- `requirements.txt` (dependencies list)
- `config.json` (configuration)
- `SETUP.md` (this file)

---

## Step 2: Open Command Prompt

1. Press `Win + R`
2. Type `cmd` and press Enter
3. Navigate to the script folder:

```cmd
cd C:\Scripts\ImageOrganizer
```

---

## Step 3: Install Dependencies

Run this command:

```cmd
pip install -r requirements.txt
```

You should see it download and install `requests` and `Pillow`.

If you get an error about pip not being found, try:

```cmd
python -m pip install -r requirements.txt
```

---

## Step 4: Get a SauceNAO API Key (Free)

1. Go to: https://saucenao.com/user.php
2. Create a free account (or log in if you have one)
3. Go to: https://saucenao.com/user.php?page=search-api
4. Copy your API key

**Free tier limits:**
- 200 searches per day
- 6 seconds between requests

This is enough for ~200 images per day. For 8,900 images, you'd need ~45 days at free tier, OR:
- Run filename parsing only first (instant, no API)
- Use API only for the truly unidentified ones
- Or pay $6/month for 5,000 searches/day

---

## Step 5: Configure the Script

1. Open `config.json` in Notepad++
2. Replace `YOUR_API_KEY_HERE` with your actual SauceNAO API key
3. Verify the paths are correct:

```json
{
    "source_directory": "G:\\My Drive\\Images",
    "output_directory": "G:\\My Drive\\Worked Images",
    "csv_output": "image_mapping.csv",
    
    "saucenao_api_key": "paste_your_key_here",
    "min_similarity": 70.0
}
```

**IMPORTANT:** Windows paths need double backslashes (`\\`) in JSON!

4. Save the file

---

## Step 6: Test Run (Recommended First!)

Before running on all 8,900 files, do a test with a small batch.

Create a test folder with 20-30 images:
```
G:\My Drive\Test Images\
```

Update `config.json` temporarily:
```json
"source_directory": "G:\\My Drive\\Test Images",
```

Then run:

```cmd
python image_organizer.py --mode scan --skip-api
```

This will:
- Scan the test folder
- Parse filenames only (no API calls)
- Generate `image_mapping.csv`

Open the CSV in Excel or Notepad++ and verify it looks correct.

---

## Step 7: Full Scan (Filename Parsing Only)

Once the test looks good, update `config.json` back to your real paths and run:

```cmd
python image_organizer.py --mode scan --skip-api
```

This scans all 8,900 files using filename parsing only. It's fast (minutes, not hours) and uses no API quota.

Review the CSV. You'll see:
- `confidence: high` = good identification
- `confidence: medium` = partial identification
- `confidence: none` = needs API lookup or manual review
- `needs_review: yes` = you should double-check this one

---

## Step 8: API Identification (Optional)

For files that couldn't be identified by filename, run:

```cmd
python image_organizer.py --mode scan --max-api 200
```

This will:
- Re-scan all files
- Use API for up to 200 unidentified images
- Takes ~20 minutes (6 sec per image)

You can run this multiple days to chip away at the unidentified pile.

---

## Step 9: Review the CSV

Open `image_mapping.csv` in Excel or a spreadsheet app.

**Columns:**
| Column | Description |
|--------|-------------|
| original_path | Where the file is now |
| new_full_path | Where it will be copied to |
| confidence | high / medium / low / none |
| needs_review | yes / no |
| origin_media | anime / video_games / comics / etc |
| publisher | Marvel / DC / Square Enix / etc |
| series | Dragon Ball / Final Fantasy / etc |
| characters | Character names (semicolon separated) |
| artist | Artist name if known |
| description | Brief description |
| source | filename / saucenao |
| notes | Additional info |
| file_hash | For duplicate detection |

**What to fix:**
- Wrong series/character identification
- Missing information you know
- Files that should go somewhere else

**Tip:** Sort by `needs_review` to see problem files first.

Save your changes!

---

## Step 10: Execute the Moves

Once you're happy with the CSV:

```cmd
python image_organizer.py --mode execute
```

It will:
1. Read the CSV
2. Ask for confirmation
3. **COPY** (not move) files to new locations
4. Create folder structure automatically

**Your originals are untouched!** The script copies, never deletes.

---

## Step 11: Verify and Clean Up

1. Spot-check the organized folders
2. Make sure everything looks right
3. If satisfied, you can delete the originals (manually, when ready)

---

## Troubleshooting

### "Python not found"

Make sure Python is in your PATH. Try:
```cmd
py image_organizer.py --mode scan
```

Or use the full path:
```cmd
C:\Users\YourName\AppData\Local\Programs\Python\Python314\python.exe image_organizer.py --mode scan
```

### "No module named requests"

Run:
```cmd
pip install requests
```

### "Config file not found"

Make sure you're in the script directory:
```cmd
cd C:\Scripts\ImageOrganizer
```

### "SauceNAO error" or "daily limit reached"

- Wait 24 hours for limit reset
- Or skip API: `--skip-api`
- Or get a paid API key

### Script is slow

- Google Drive sync adds overhead
- Consider copying files locally first (Option B from earlier)
- Filename parsing is instant; API is slow

---

## Command Reference

| Command | What it does |
|---------|--------------|
| `--mode scan` | Scan files and generate CSV |
| `--mode execute` | Run the moves from CSV |
| `--mode full` | Scan, pause for review, then execute |
| `--skip-api` | Don't use SauceNAO (filename only) |
| `--max-api 200` | Limit API calls |
| `--csv path.csv` | Use a different CSV file |
| `--config path.json` | Use a different config file |

---

## For Your Laptop

When running on a different machine:

1. Copy the script folder
2. Install dependencies: `pip install -r requirements.txt`
3. Edit `config.json` with the correct paths for that machine
4. Run as normal

---

## Questions?

Bring the CSV or any errors back to Claude and we'll figure it out!
