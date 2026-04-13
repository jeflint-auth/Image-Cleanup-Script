#!/usr/bin/env python3
"""
Image Organizer Script
======================
Scans a folder of images, identifies content via filename parsing and 
reverse image search APIs, generates a CSV mapping file for review,
then executes the file organization based on approved mappings.

Author: Claude (Anthropic) for Janice
Version: 1.0.0
"""

import os
import sys
import json
import csv
import re
import shutil
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ImageInfo:
    """Holds identification data for a single image."""
    original_path: str
    filename: str
    extension: str
    file_size: int
    file_hash: str
    
    # Identification results
    origin_media: str = ""          # anime, video_games, comics, etc.
    publisher: str = ""             # Marvel, DC, Square Enix, etc.
    series: str = ""                # Dragon Ball, Final Fantasy VII, etc.
    characters: List[str] = None    # List of character names
    artist: str = ""                # Artist name if known
    description: str = ""           # Brief description
    
    # Metadata
    confidence: str = "none"        # high, medium, low, none
    source: str = ""                # filename, saucenao, iqdb, manual
    needs_review: bool = True
    notes: str = ""
    rating: str = ""                # safe, questionable, explicit, unknown
    
    # Output
    new_folder: str = ""
    new_filename: str = ""
    new_full_path: str = ""
    
    def __post_init__(self):
        if self.characters is None:
            self.characters = []


# =============================================================================
# FILENAME PARSING
# =============================================================================

class FilenameParser:
    """
    Extracts information from filenames that contain embedded metadata.
    Handles common patterns from boorus, DeviantArt, FurAffinity, etc.
    """
    
    # Booru-style pattern: "123456 - tag1 tag2 tag3.jpg"
    BOORU_PATTERN = re.compile(r'^(\d+)\s*[-_]\s*(.+)$')
    
    # DeviantArt pattern: "title_by_artist-d8abc12.jpg"
    DEVIANTART_PATTERN = re.compile(r'^(.+?)_by_([a-zA-Z0-9_-]+)-[a-z0-9]+\.(jpg|png|gif)$', re.IGNORECASE)
    
    # FurAffinity pattern: "1234567890_artist_title.jpg"
    FURAFFINITY_PATTERN = re.compile(r'^(\d{10,})_([a-zA-Z0-9_-]+)_(.+)$')
    
    # Tumblr pattern: "tumblr_abc123xyz_1280.jpg"
    TUMBLR_PATTERN = re.compile(r'^tumblr_[a-zA-Z0-9]+.*$', re.IGNORECASE)
    
    # Twitter/X pattern: "username-status-1234567890-img1.jpg" or similar
    TWITTER_PATTERN = re.compile(r'^([a-zA-Z0-9_]+)[-_]status[-_](\d+)', re.IGNORECASE)
    
    # Pure hash pattern (no useful info)
    HASH_PATTERN = re.compile(r'^[a-f0-9]{20,}$', re.IGNORECASE)
    
    # Wikipedia/wiki pattern: "123px-Name.jpg"
    WIKI_PATTERN = re.compile(r'^(\d+)px[-_](.+)$', re.IGNORECASE)
    
    # Known series keywords for quick matching
    KNOWN_SERIES = {
        # Anime
        'dragon_ball': ('anime', 'Dragon Ball'),
        'dragonball': ('anime', 'Dragon Ball'),
        'sailor_moon': ('anime', 'Sailor Moon'),
        'sailormoon': ('anime', 'Sailor Moon'),
        'ranma': ('anime', 'Ranma 1-2'),
        'evangelion': ('anime', 'Evangelion'),
        'naruto': ('anime', 'Naruto'),
        'one_piece': ('anime', 'One Piece'),
        'onepiece': ('anime', 'One Piece'),
        'bleach': ('anime', 'Bleach'),
        'inuyasha': ('anime', 'Inuyasha'),
        'cowboy_bebop': ('anime', 'Cowboy Bebop'),
        'gundam': ('anime', 'Gundam'),
        'macross': ('anime', 'Macross'),
        'lupin': ('anime', 'Lupin III'),
        'yu_yu_hakusho': ('anime', 'Yu Yu Hakusho'),
        'hellsing': ('anime', 'Hellsing'),
        'trigun': ('anime', 'Trigun'),
        
        # Video Games
        'final_fantasy': ('video_games', 'Final Fantasy'),
        'finalfantasy': ('video_games', 'Final Fantasy'),
        'guilty_gear': ('video_games', 'Guilty Gear'),
        'guiltygear': ('video_games', 'Guilty Gear'),
        'pokemon': ('video_games', 'Pokemon'),
        'zelda': ('video_games', 'Legend of Zelda'),
        'metroid': ('video_games', 'Metroid'),
        'street_fighter': ('video_games', 'Street Fighter'),
        'streetfighter': ('video_games', 'Street Fighter'),
        'mortal_kombat': ('video_games', 'Mortal Kombat'),
        'tekken': ('video_games', 'Tekken'),
        'kingdom_hearts': ('video_games', 'Kingdom Hearts'),
        'sonic': ('video_games', 'Sonic'),
        'megaman': ('video_games', 'Mega Man'),
        'mega_man': ('video_games', 'Mega Man'),
        'castlevania': ('video_games', 'Castlevania'),
        'dragon_quest': ('video_games', 'Dragon Quest'),
        'dragonquest': ('video_games', 'Dragon Quest'),
        'warcraft': ('video_games', 'Warcraft'),
        'world_of_warcraft': ('video_games', 'World of Warcraft'),
        'wow': ('video_games', 'World of Warcraft'),
        'overwatch': ('video_games', 'Overwatch'),
        'league_of_legends': ('video_games', 'League of Legends'),
        'lol': ('video_games', 'League of Legends'),
        
        # Comics - Marvel
        'marvel': ('comics', 'Marvel'),
        'avengers': ('comics', 'Marvel'),
        'x-men': ('comics', 'Marvel'),
        'xmen': ('comics', 'Marvel'),
        'spider-man': ('comics', 'Marvel'),
        'spiderman': ('comics', 'Marvel'),
        'deadpool': ('comics', 'Marvel'),
        'thanos': ('comics', 'Marvel'),
        'iron_man': ('comics', 'Marvel'),
        'ironman': ('comics', 'Marvel'),
        'captain_america': ('comics', 'Marvel'),
        'thor': ('comics', 'Marvel'),
        'hulk': ('comics', 'Marvel'),
        
        # Comics - DC
        'dc_comics': ('comics', 'DC'),
        'batman': ('comics', 'DC'),
        'superman': ('comics', 'DC'),
        'wonder_woman': ('comics', 'DC'),
        'justice_league': ('comics', 'DC'),
        'teen_titans': ('comics', 'DC'),
        'flash': ('comics', 'DC'),
        'green_lantern': ('comics', 'DC'),
        'aquaman': ('comics', 'DC'),
    }
    
    # Known character names
    KNOWN_CHARACTERS = {
        # Dragon Ball
        'goku': 'Goku',
        'vegeta': 'Vegeta',
        'bulma': 'Bulma',
        'gohan': 'Gohan',
        'piccolo': 'Piccolo',
        'krillin': 'Krillin',
        'roshi': 'Master Roshi',
        'master_roshi': 'Master Roshi',
        'frieza': 'Frieza',
        'cell': 'Cell',
        'trunks': 'Trunks',
        
        # Sailor Moon
        'usagi': 'Usagi Tsukino',
        'sailor_moon': 'Usagi Tsukino',
        'chibiusa': 'Chibiusa',
        'ami': 'Ami Mizuno',
        'sailor_mercury': 'Ami Mizuno',
        'rei': 'Rei Hino',
        'sailor_mars': 'Rei Hino',
        'makoto': 'Makoto Kino',
        'sailor_jupiter': 'Makoto Kino',
        'minako': 'Minako Aino',
        'sailor_venus': 'Minako Aino',
        
        # Final Fantasy
        'cloud': 'Cloud Strife',
        'cloud_strife': 'Cloud Strife',
        'tifa': 'Tifa Lockhart',
        'aerith': 'Aerith Gainsborough',
        'sephiroth': 'Sephiroth',
        'squall': 'Squall Leonhart',
        'rinoa': 'Rinoa Heartilly',
        'lightning': 'Lightning',
        
        # Ranma
        'ranma': 'Ranma Saotome',
        'ranma_saotome': 'Ranma Saotome',
        'akane': 'Akane Tendo',
        'shampoo': 'Shampoo',
        
        # Guilty Gear
        'sol_badguy': 'Sol Badguy',
        'sol': 'Sol Badguy',
        'ky_kiske': 'Ky Kiske',
        'ky': 'Ky Kiske',
        'dizzy': 'Dizzy',
        'may': 'May',
        'baiken': 'Baiken',
        'i-no': 'I-No',
    }
    
    def parse(self, filename: str) -> Dict:
        """
        Parse a filename and extract any available metadata.
        Returns a dict with extracted info.
        """
        result = {
            'artist': '',
            'characters': [],
            'series': '',
            'origin_media': '',
            'description': '',
            'source': 'filename',
            'confidence': 'none',
            'rating': 'unknown'
        }
        
        # Strip extension
        name_without_ext = os.path.splitext(filename)[0]
        name_lower = name_without_ext.lower()
        
        # Check for rating tags in filename
        if any(tag in name_lower for tag in ['rating_explicit', 'rating_e', '_explicit_', ' explicit ']):
            result['rating'] = 'explicit'
        elif any(tag in name_lower for tag in ['rating_questionable', 'rating_q', '_questionable_']):
            result['rating'] = 'questionable'
        elif any(tag in name_lower for tag in ['rating_safe', 'rating_s', '_safe_']):
            result['rating'] = 'safe'
        
        # Strip extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Check if it's a pure hash (no useful info)
        if self.HASH_PATTERN.match(name_without_ext):
            return result
        
        # Try DeviantArt pattern
        da_match = self.DEVIANTART_PATTERN.match(filename)
        if da_match:
            result['description'] = da_match.group(1).replace('_', ' ').replace('-', ' ')
            result['artist'] = da_match.group(2).replace('_', ' ')
            result['confidence'] = 'medium'
            return result
        
        # Try FurAffinity pattern
        fa_match = self.FURAFFINITY_PATTERN.match(name_without_ext)
        if fa_match:
            result['artist'] = fa_match.group(2).replace('_', ' ')
            result['description'] = fa_match.group(3).replace('_', ' ').replace('-', ' ')
            result['confidence'] = 'medium'
            return result
        
        # Try Wiki pattern (remove the dimension prefix)
        wiki_match = self.WIKI_PATTERN.match(name_without_ext)
        if wiki_match:
            name_without_ext = wiki_match.group(2)
        
        # Try booru pattern
        booru_match = self.BOORU_PATTERN.match(name_without_ext)
        if booru_match:
            tags = booru_match.group(2).lower().replace('-', '_').split('_')
            tags = [t.strip() for t in tags if t.strip()]
            
            # Look for known series
            for tag in tags:
                if tag in self.KNOWN_SERIES:
                    result['origin_media'], result['series'] = self.KNOWN_SERIES[tag]
                    result['confidence'] = 'high'
                    break
            
            # Look for known characters
            for tag in tags:
                if tag in self.KNOWN_CHARACTERS:
                    result['characters'].append(self.KNOWN_CHARACTERS[tag])
            
            if result['characters']:
                result['confidence'] = 'high' if result['series'] else 'medium'
            
            return result
        
        # General keyword search in filename
        search_name = name_without_ext.lower().replace('-', '_').replace(' ', '_')
        
        for keyword, (origin, series) in self.KNOWN_SERIES.items():
            if keyword in search_name:
                result['origin_media'] = origin
                result['series'] = series
                result['confidence'] = 'medium'
                break
        
        for keyword, character in self.KNOWN_CHARACTERS.items():
            if keyword in search_name:
                result['characters'].append(character)
                result['confidence'] = 'medium'
        
        return result


# =============================================================================
# REVERSE IMAGE SEARCH APIs
# =============================================================================

class SauceNAOClient:
    """Client for SauceNAO reverse image search API."""
    
    BASE_URL = "https://saucenao.com/search.php"
    
    def __init__(self, api_key: str, min_similarity: float = 70.0):
        self.api_key = api_key
        self.min_similarity = min_similarity
        self.requests_remaining = 200  # Free tier daily limit
        self.last_request_time = 0
        self.request_interval = 6  # Seconds between requests (free tier)
    
    def search(self, image_path: str) -> Optional[Dict]:
        """
        Search for an image on SauceNAO.
        Returns parsed result or None if no match found.
        """
        if not self.api_key:
            return None
        
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        
        self.last_request_time = time.time()
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                params = {
                    'api_key': self.api_key,
                    'output_type': 2,  # JSON
                    'numres': 5,
                    'db': 999,  # All databases
                }
                
                response = requests.post(self.BASE_URL, params=params, files=files, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Update rate limit info
                if 'header' in data:
                    self.requests_remaining = data['header'].get('long_remaining', 0)
                
                # Parse results
                if 'results' in data and data['results']:
                    for result in data['results']:
                        similarity = float(result['header'].get('similarity', 0))
                        if similarity >= self.min_similarity:
                            return self._parse_result(result)
                
                return None
                
        except Exception as e:
            print(f"SauceNAO error for {image_path}: {e}")
            return None
    
    def _parse_result(self, result: Dict) -> Dict:
        """Parse a SauceNAO result into our format."""
        data = result.get('data', {})
        header = result.get('header', {})
        
        parsed = {
            'similarity': float(header.get('similarity', 0)),
            'source': 'saucenao',
            'confidence': 'high' if float(header.get('similarity', 0)) >= 85 else 'medium',
            'artist': '',
            'characters': [],
            'series': '',
            'origin_media': '',
            'source_url': '',
            'rating': 'unknown',
        }
        
        # Index-specific parsing
        index_id = header.get('index_id', 0)
        
        # Pixiv (index 5, 6)
        if index_id in [5, 6]:
            parsed['artist'] = data.get('member_name', '') or data.get('author_name', '')
            parsed['origin_media'] = 'anime'  # Pixiv is mostly anime-style
        
        # DeviantArt (index 34)
        elif index_id == 34:
            parsed['artist'] = data.get('author_name', '')
        
        # Anime/Manga (index 21, 22, etc.)
        elif index_id in [21, 22]:
            parsed['series'] = data.get('source', '')
            parsed['origin_media'] = 'anime'
            if 'characters' in data:
                if isinstance(data['characters'], list):
                    parsed['characters'] = data['characters']
                else:
                    parsed['characters'] = [data['characters']]
        
        # Danbooru/Gelbooru/etc (index 9, 12, 25, 26)
        elif index_id in [9, 12, 25, 26]:
            if 'creator' in data:
                parsed['artist'] = data['creator'] if isinstance(data['creator'], str) else ', '.join(data['creator'])
            if 'characters' in data:
                if isinstance(data['characters'], list):
                    parsed['characters'] = data['characters']
                else:
                    parsed['characters'] = [data['characters']]
            if 'material' in data:
                parsed['series'] = data['material'] if isinstance(data['material'], str) else ', '.join(data['material'])
            # Extract rating from booru data
            if 'rating' in data:
                rating_map = {'s': 'safe', 'q': 'questionable', 'e': 'explicit'}
                parsed['rating'] = rating_map.get(data['rating'], data['rating'])
        
        # FurAffinity (index 40)
        elif index_id == 40:
            parsed['artist'] = data.get('author_name', '')
            parsed['origin_media'] = 'furries'
            # FA doesn't return rating directly, but we can check for adult flag
            if data.get('fa_id'):
                parsed['rating'] = 'unknown'  # Would need secondary lookup
        
        # e621 (index 29) - furry booru with ratings
        elif index_id == 29:
            if 'creator' in data:
                parsed['artist'] = data['creator'] if isinstance(data['creator'], str) else ', '.join(data['creator'])
            if 'characters' in data:
                if isinstance(data['characters'], list):
                    parsed['characters'] = data['characters']
                else:
                    parsed['characters'] = [data['characters']]
            parsed['origin_media'] = 'furries'
            if 'rating' in data:
                rating_map = {'s': 'safe', 'q': 'questionable', 'e': 'explicit'}
                parsed['rating'] = rating_map.get(data['rating'], data['rating'])
        
        # External URLs
        if 'ext_urls' in data and data['ext_urls']:
            parsed['source_url'] = data['ext_urls'][0]
        
        return parsed


# =============================================================================
# PATH BUILDING
# =============================================================================

class PathBuilder:
    """Builds destination paths according to the organizational rules."""
    
    def __init__(self, base_output_dir: str):
        self.base_dir = Path(base_output_dir)
    
    def build(self, info: ImageInfo, existing_files: Dict[str, int]) -> Tuple[str, str]:
        """
        Build the destination folder and filename for an image.
        Returns (folder_path, filename).
        """
        # Determine folder hierarchy
        parts = []
        
        # NSFW prefix - routes explicit/questionable content to separate tree
        if info.rating in ['explicit', 'questionable']:
            parts.append('_nsfw')
        
        # Top-level origin folder
        origin = info.origin_media or '_unsorted'
        if origin == '_unsorted':
            # Try to categorize unsorted
            if info.notes and 'anime' in info.notes.lower():
                origin = '_unsorted/possibly_anime'
            elif info.notes and 'furry' in info.notes.lower():
                origin = '_unsorted/possibly_furry'
            else:
                origin = '_unsorted/unknown'
        parts.append(origin)
        
        # Publisher (for comics) or skip
        if info.publisher:
            parts.append(self._sanitize_path(info.publisher))
        
        # Series
        if info.series:
            parts.append(self._sanitize_path(info.series))
        
        # Character folder
        if info.characters:
            if len(info.characters) == 1:
                char_folder = self._sanitize_path(info.characters[0])
            elif len(info.characters) == 2:
                char_folder = self._sanitize_path(f"{info.characters[0]} & {info.characters[1]}")
            else:
                char_folder = "Group"
            parts.append(char_folder)
        
        # Misc subfolder if no artist
        if not info.artist and info.characters:
            parts.append("Misc")
        
        # Build folder path
        folder_path = str(self.base_dir.joinpath(*parts))
        
        # Build filename
        filename = self._build_filename(info, folder_path, existing_files)
        
        return folder_path, filename
    
    def _build_filename(self, info: ImageInfo, folder_path: str, existing_files: Dict[str, int]) -> str:
        """Build the filename with proper incrementing."""
        parts = []
        
        # Artist
        if info.artist:
            parts.append(self._sanitize_filename(info.artist))
        
        # Character(s)
        if info.characters:
            if len(info.characters) == 1:
                parts.append(self._sanitize_filename(info.characters[0]))
            elif len(info.characters) == 2:
                parts.append(self._sanitize_filename(f"{info.characters[0]} & {info.characters[1]}"))
            else:
                parts.append("Group")
        
        # Description
        if info.description:
            parts.append(self._sanitize_filename(info.description[:50]))
        
        # If we have nothing, use original filename base
        if not parts:
            parts.append(os.path.splitext(info.filename)[0][:30])
        
        base_name = " - ".join(parts)
        
        # Get increment
        key = f"{folder_path}/{base_name}".lower()
        increment = existing_files.get(key, 0) + 1
        existing_files[key] = increment
        
        # Build final filename
        filename = f"{base_name} {increment:03d}{info.extension}"
        
        return filename
    
    def _sanitize_path(self, s: str) -> str:
        """Sanitize a string for use in a folder path."""
        # Remove/replace invalid characters
        invalid = '<>:"/\\|?*'
        for char in invalid:
            s = s.replace(char, '')
        return s.strip()[:100]
    
    def _sanitize_filename(self, s: str) -> str:
        """Sanitize a string for use in a filename."""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            s = s.replace(char, '')
        return s.strip()[:50]


# =============================================================================
# MAIN SCANNER
# =============================================================================

class ImageOrganizer:
    """Main class that orchestrates the image organization process."""
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'}
    
    VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v'}
    
    OTHER_EXTENSIONS = {
        '.psd', '.ai', '.eps', '.svg',           # Source/vector files
        '.clip', '.sai', '.kra', '.xcf',          # Art program files
        '.swf', '.fla',                           # Flash
        '.pdf',                                   # Documents
        '.zip', '.rar', '.7z',                    # Archives
        '.txt', '.md', '.nfo',                    # Text files
    }
    
    def __init__(self, config: dict):
        self.config = config
        self.source_dir = Path(config['source_directory'])
        self.output_dir = Path(config['output_directory'])
        self.csv_path = Path(config.get('csv_output', 'image_mapping.csv'))
        
        self.filename_parser = FilenameParser()
        self.saucenao = SauceNAOClient(
            api_key=config.get('saucenao_api_key', ''),
            min_similarity=config.get('min_similarity', 70.0)
        )
        self.path_builder = PathBuilder(str(self.output_dir))
        
        self.images: List[ImageInfo] = []
        self.existing_files: Dict[str, int] = {}
        self.stats = {
            'total_scanned': 0,
            'filename_parsed': 0,
            'api_identified': 0,
            'unidentified': 0,
            'duplicates': 0,
            'errors': 0,
        }
    
    def scan(self) -> None:
        """Scan source directory for images and other files."""
        print(f"Scanning {self.source_dir}...")
        
        for root, dirs, files in os.walk(self.source_dir):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                filepath = os.path.join(root, filename)
                
                if ext in self.IMAGE_EXTENSIONS:
                    self._process_file(filepath, filename, ext, file_type='image')
                    self.stats['total_scanned'] += 1
                elif ext in self.VIDEO_EXTENSIONS:
                    self._process_file(filepath, filename, ext, file_type='video')
                    self.stats['total_scanned'] += 1
                elif ext in self.OTHER_EXTENSIONS:
                    self._process_file(filepath, filename, ext, file_type='other')
                    self.stats['total_scanned'] += 1
                    
                if self.stats['total_scanned'] % 100 == 0:
                    print(f"  Scanned {self.stats['total_scanned']} files...")
        
        print(f"Scan complete. Found {self.stats['total_scanned']} files.")
    
    def _process_file(self, filepath: str, filename: str, ext: str, file_type: str = 'image') -> None:
        """Process a single file."""
        try:
            # Get file info
            file_size = os.path.getsize(filepath)
            file_hash = self._get_file_hash(filepath)
            
            # Create info object
            info = ImageInfo(
                original_path=filepath,
                filename=filename,
                extension=ext,
                file_size=file_size,
                file_hash=file_hash
            )
            
            # For non-images, route to _other_files folder
            if file_type == 'video':
                info.origin_media = '_other_files/videos'
                info.confidence = 'low'
                info.needs_review = True
                info.notes = 'Video file - filename parsing only'
            elif file_type == 'other':
                info.origin_media = '_other_files/misc'
                info.confidence = 'low'
                info.needs_review = True
                info.notes = f'Non-image file ({ext})'
            
            # Try filename parsing (works for all file types)
            parsed = self.filename_parser.parse(filename)
            if parsed['confidence'] != 'none':
                info.artist = parsed['artist']
                info.characters = parsed['characters']
                info.series = parsed['series']
                # Only override origin_media for images
                if file_type == 'image':
                    info.origin_media = parsed['origin_media']
                info.description = parsed['description']
                info.confidence = parsed['confidence']
                info.source = 'filename'
                info.needs_review = parsed['confidence'] != 'high'
                self.stats['filename_parsed'] += 1
            
            # Always grab rating if detected, even if other parsing failed
            if parsed.get('rating') and parsed['rating'] != 'unknown':
                info.rating = parsed['rating']
            
            # Use parent folder as hint if available
            parent_folder = os.path.basename(os.path.dirname(filepath)).lower()
            if not info.origin_media or info.origin_media.startswith('_other_files'):
                if file_type == 'image':
                    info.notes = f"Parent folder: {parent_folder}"
                else:
                    info.notes = f"{info.notes}; Parent folder: {parent_folder}"
            
            self.images.append(info)
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            self.stats['errors'] += 1
    
    def _get_file_hash(self, filepath: str) -> str:
        """Get MD5 hash of file (for duplicate detection)."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def identify_with_api(self, max_requests: int = 0) -> None:
        """
        Use SauceNAO API to identify images that couldn't be parsed from filename.
        Set max_requests to limit API calls (0 = unlimited within daily quota).
        Skips non-image files (videos, PSDs, etc.)
        """
        if not self.config.get('saucenao_api_key'):
            print("No SauceNAO API key configured. Skipping API identification.")
            return
        
        # Only process images with no identification, skip videos/other files
        unidentified = [
            img for img in self.images 
            if img.confidence == 'none' 
            and img.extension.lower() in self.IMAGE_EXTENSIONS
            and not img.origin_media.startswith('_other_files')
        ]
        print(f"Attempting API identification for {len(unidentified)} images...")
        
        requests_made = 0
        for i, info in enumerate(unidentified):
            if max_requests > 0 and requests_made >= max_requests:
                print(f"Reached max requests limit ({max_requests})")
                break
            
            if self.saucenao.requests_remaining <= 0:
                print("SauceNAO daily limit reached.")
                break
            
            result = self.saucenao.search(info.original_path)
            requests_made += 1
            
            if result:
                info.artist = result.get('artist', '')
                info.characters = result.get('characters', [])
                info.series = result.get('series', '')
                info.origin_media = result.get('origin_media', '')
                info.confidence = result.get('confidence', 'medium')
                info.source = 'saucenao'
                info.notes = result.get('source_url', '')
                info.rating = result.get('rating', 'unknown')
                info.needs_review = info.confidence != 'high'
                self.stats['api_identified'] += 1
            else:
                self.stats['unidentified'] += 1
            
            if (i + 1) % 10 == 0:
                print(f"  API checked {i + 1}/{len(unidentified)} "
                      f"(remaining today: {self.saucenao.requests_remaining})")
        
        print(f"API identification complete. Identified: {self.stats['api_identified']}, "
              f"Unidentified: {self.stats['unidentified']}")
    
    def build_paths(self) -> None:
        """Build destination paths for all images."""
        print("Building destination paths...")
        
        for info in self.images:
            folder, filename = self.path_builder.build(info, self.existing_files)
            info.new_folder = folder
            info.new_filename = filename
            info.new_full_path = os.path.join(folder, filename)
        
        print("Path building complete.")
    
    def export_csv(self) -> None:
        """Export the mapping to CSV for review."""
        print(f"Exporting to {self.csv_path}...")
        
        fieldnames = [
            'original_path', 'new_full_path', 'confidence', 'needs_review', 'rating',
            'origin_media', 'publisher', 'series', 'characters', 'artist',
            'description', 'source', 'notes', 'file_hash'
        ]
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for info in self.images:
                row = {
                    'original_path': info.original_path,
                    'new_full_path': info.new_full_path,
                    'confidence': info.confidence,
                    'needs_review': 'yes' if info.needs_review else 'no',
                    'rating': info.rating or 'unknown',
                    'origin_media': info.origin_media,
                    'publisher': info.publisher,
                    'series': info.series,
                    'characters': '; '.join(info.characters) if info.characters else '',
                    'artist': info.artist,
                    'description': info.description,
                    'source': info.source,
                    'notes': info.notes,
                    'file_hash': info.file_hash,
                }
                writer.writerow(row)
        
        print(f"Exported {len(self.images)} entries to CSV.")
    
    def print_stats(self) -> None:
        """Print statistics summary."""
        print("\n" + "=" * 50)
        print("SCAN STATISTICS")
        print("=" * 50)
        print(f"Total images scanned:    {self.stats['total_scanned']}")
        print(f"Identified by filename:  {self.stats['filename_parsed']}")
        print(f"Identified by API:       {self.stats['api_identified']}")
        print(f"Unidentified:            {self.stats['unidentified']}")
        print(f"Errors:                  {self.stats['errors']}")
        print("=" * 50)
    
    def execute_moves(self, csv_path: str = None) -> None:
        """
        Execute the file moves based on a reviewed CSV.
        This is a separate step to allow manual review.
        """
        csv_to_use = csv_path or str(self.csv_path)
        print(f"Reading mappings from {csv_to_use}...")
        
        moves = []
        with open(csv_to_use, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                moves.append((row['original_path'], row['new_full_path']))
        
        print(f"Found {len(moves)} files to move.")
        confirm = input("Proceed with file copy? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("Aborted.")
            return
        
        success = 0
        errors = 0
        
        for i, (src, dst) in enumerate(moves):
            try:
                # Create destination directory
                dst_dir = os.path.dirname(dst)
                os.makedirs(dst_dir, exist_ok=True)
                
                # Copy file (not move - safer)
                shutil.copy2(src, dst)
                success += 1
                
                if (i + 1) % 100 == 0:
                    print(f"  Copied {i + 1}/{len(moves)} files...")
                    
            except Exception as e:
                print(f"Error copying {src}: {e}")
                errors += 1
        
        print(f"\nComplete! Copied: {success}, Errors: {errors}")
        print(f"Originals are untouched in {self.source_dir}")
        print(f"Organized copies are in {self.output_dir}")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize images by content identification')
    parser.add_argument('--config', '-c', default='config.json', help='Path to config file')
    parser.add_argument('--mode', '-m', choices=['scan', 'execute', 'full'], default='scan',
                        help='Mode: scan (generate CSV), execute (run moves from CSV), full (both)')
    parser.add_argument('--csv', help='CSV file path (for execute mode)')
    parser.add_argument('--max-api', type=int, default=0, help='Max API requests (0=unlimited)')
    parser.add_argument('--skip-api', action='store_true', help='Skip API identification')
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        print("Please create a config.json file. See SETUP.md for instructions.")
        sys.exit(1)
    
    organizer = ImageOrganizer(config)
    
    if args.mode in ['scan', 'full']:
        # Scan phase
        organizer.scan()
        
        if not args.skip_api:
            organizer.identify_with_api(max_requests=args.max_api)
        
        organizer.build_paths()
        organizer.export_csv()
        organizer.print_stats()
        
        print(f"\nCSV exported to: {organizer.csv_path}")
        print("Please review the CSV, make any corrections, then run with --mode execute")
    
    if args.mode == 'execute':
        csv_path = args.csv or str(organizer.csv_path)
        organizer.execute_moves(csv_path)
    
    if args.mode == 'full':
        print("\n" + "=" * 50)
        print("Review the CSV now, then press Enter to continue with execution,")
        print("or Ctrl+C to abort and review manually.")
        input("Press Enter to continue...")
        organizer.execute_moves()


if __name__ == '__main__':
    main()
