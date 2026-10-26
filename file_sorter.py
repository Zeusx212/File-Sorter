"""
File Sorter, Media Organizer & Bulk Renamer v3.2
A modern desktop app to organize files into category folders,
structure TV shows, Anime & movies with database metadata, and
perform powerful bulk file renaming with live preview.

Key features
────────────
 • Tab 1: General File Sorter (by category: Images, Docs, Code, etc.)
 • Tab 2: Media Sorter (TV Series, Anime & Movies with TVDB/Kitsu integration)
 • Tab 3: Bulk File Renamer (Find/Replace, Regex, Case, Numbering, Prefix/Suffix)
 • Free TV Database metadata via TVMaze (show info, episode titles)
 • Free Anime Database metadata via Kitsu API (canonical titles, ratings, episode guides)
 • TV & Anime Database Lookup tools (browse show overviews, ratings, seasons, episodes)
 • High-contrast dark / light theme with custom Sun / Moon icon toggle
 • Card-based toolbar & table design with pixel-aligned columns
 • Duplicate detection, CSV report export, and full multi-level Undo history
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import threading
import time
import tkinter as tk
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw
import customtkinter as ctk

# ═══════════════════════════════════════════════════════════════════════════
#  CONSTANTS & DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════

APP_NAME = "File Sorter"
APP_VERSION = "3.2.1"
SETTINGS_FILE = Path.home() / ".file_sorter_settings.json"
HISTORY_FILENAME = ".file_sorter_history.json"
MEDIA_HISTORY_FILENAME = ".media_sorter_history.json"
RENAMER_HISTORY_FILENAME = ".bulk_renamer_history.json"

FONT_FAMILY = "Segoe UI"

# General Sorter Table Columns (label, width)
FILE_TABLE_COLS = [
    ("", 28),
    ("File Name", 240),
    ("Size", 75),
    ("Ext", 60),
    ("Target Category", 130),
    ("Dup", 50),
    ("Status", 70),
]

# Media Sorter Table Columns (label, width)
MEDIA_TABLE_COLS = [
    ("", 28),
    ("Original File", 210),
    ("Type", 75),
    ("Detected Title", 140),
    ("S / Ep", 65),
    ("Episode Title (DB)", 160),
    ("New Destination Path", 230),
    ("Status", 65),
]

# Bulk Renamer Table Columns (label, width)
RENAME_TABLE_COLS = [
    ("", 28),
    ("Original File", 250),
    ("Size", 75),
    ("New Filename Preview", 320),
    ("Change", 75),
    ("Status", 70),
]

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    ".ts", ".mpg", ".mpeg", ".3gp",
}

DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".tiff",
        ".tif", ".webp", ".heic", ".heif", ".raw", ".cr2", ".nef", ".psd",
    ],
    "Videos": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
        ".mpg", ".mpeg", ".3gp", ".ts",
    ],
    "Music": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus",
        ".aiff", ".mid", ".midi",
    ],
    "Documents": [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt",
        ".rtf", ".odt", ".ods", ".odp", ".csv", ".epub", ".pages", ".tex",
        ".md", ".log",
    ],
    "Archives": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso",
        ".dmg", ".cab", ".lz", ".zst",
    ],
    "Code": [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
        ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".rb",
        ".php", ".swift", ".kt", ".lua", ".sql", ".sh", ".bat", ".ps1",
        ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ],
    "Executables": [
        ".exe", ".msi", ".apk", ".app", ".deb", ".rpm", ".appimage",
        ".com", ".gadget",
    ],
    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ],
    "3D Models": [
        ".obj", ".fbx", ".stl", ".blend", ".3ds", ".dae", ".gltf", ".glb",
    ],
    "Torrents": [".torrent"],
    "Disk Images": [".img", ".vhd", ".vhdx", ".vmdk"],
    "Shortcuts": [".lnk", ".url"],
}

# ── Unified theme palettes ──────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg": "#0f172a",          # Deep slate
        "sidebar": "#1e293b",     # Slate sidebar
        "card": "#1e293b",        # Slate cards
        "card_alt": "#334155",    # Header & card-alt background
        "header": "#1e3a8a",      # Royal blue titlebar
        "accent": "#38bdf8",      # Sky blue
        "accent_hover": "#0284c7",
        "btn_primary": "#2563eb",
        "btn_primary_hover": "#1d4ed8",
        "success": "#16a34a",     # Forest green
        "success_hover": "#15803d",
        "warning": "#d97706",     # Muted amber
        "warning_hover": "#b45309",
        "danger": "#ef4444",
        "danger_hover": "#dc2626",
        "text": "#ffffff",        # High-contrast white
        "text_dim": "#cbd5e1",    # Clean silver
        "text_muted": "#94a3b8",  # Slate-400
        "border": "#334155",      # Slate border
        "input_bg": "#0f172a",    # Dark input background
        "row_even": "#1e293b",
        "row_odd": "#172033",
        "row_hover": "#25334d",
        "scrollbar": "#475569",
        "scrollbar_hover": "#64748b",
        "chart_bg": "#0f172a",
        "badge_tv": "#2563eb",
        "badge_movie": "#7c3aed",
        "badge_anime": "#ec4899",
        "badge_video": "#64748b",
        "badge_changed": "#0284c7",
        "badge_same": "#475569",
    },
    "light": {
        "bg": "#f8fafc",
        "sidebar": "#ffffff",
        "card": "#ffffff",
        "card_alt": "#e2e8f0",
        "header": "#2563eb",
        "accent": "#0284c7",
        "accent_hover": "#0369a1",
        "btn_primary": "#2563eb",
        "btn_primary_hover": "#1d4ed8",
        "success": "#16a34a",
        "success_hover": "#15803d",
        "warning": "#d97706",
        "warning_hover": "#b45309",
        "danger": "#dc2626",
        "danger_hover": "#b91c1c",
        "text": "#0f172a",
        "text_dim": "#334155",
        "text_muted": "#64748b",
        "border": "#cbd5e1",
        "input_bg": "#f1f5f9",
        "row_even": "#ffffff",
        "row_odd": "#f8fafc",
        "row_hover": "#f1f5f9",
        "scrollbar": "#94a3b8",
        "scrollbar_hover": "#64748b",
        "chart_bg": "#f1f5f9",
        "badge_tv": "#0284c7",
        "badge_movie": "#9333ea",
        "badge_anime": "#db2777",
        "badge_video": "#64748b",
        "badge_changed": "#0284c7",
        "badge_same": "#94a3b8",
    },
}

CHART_COLORS = [
    "#38bdf8", "#34d399", "#fbbf24", "#f87171", "#c084fc",
    "#f472b6", "#2dd4bf", "#fb923c", "#818cf8", "#22d3ee",
    "#a3e635", "#fb7185",
]


# ═══════════════════════════════════════════════════════════════════════════
#  GRAPHICS & ICONS
# ═══════════════════════════════════════════════════════════════════════════

def _create_sun_icon(size: int = 18, color: tuple = (255, 255, 255)) -> Image.Image:
    scale = 4
    s = size * scale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = s / 2, s / 2
    r = s * 0.22
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    for i in range(8):
        angle = i * (math.pi / 4)
        x1 = cx + math.cos(angle) * (r + s * 0.08)
        y1 = cy + math.sin(angle) * (r + s * 0.08)
        x2 = cx + math.cos(angle) * (r + s * 0.20)
        y2 = cy + math.sin(angle) * (r + s * 0.20)
        d.line([(x1, y1), (x2, y2)], fill=color, width=round(2.5 * scale))
    return im.resize((size, size), Image.Resampling.LANCZOS)


def _create_moon_icon(size: int = 18, color: tuple = (255, 255, 255)) -> Image.Image:
    scale = 4
    s = size * scale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = s / 2, s / 2
    r = s * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.ellipse([cx - r * 0.2, cy - r * 1.1, cx + r * 1.5, cy + r * 0.7], fill=(0, 0, 0, 0))
    return im.resize((size, size), Image.Resampling.LANCZOS)


def _font(size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def human_size(nbytes: int | float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}" if unit != "B" else f"{int(nbytes)} B"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


def file_hash(path: Path) -> str:
    h = hashlib.md5(usedforsecurity=False)
    h.update(path.name.encode())
    h.update(str(path.stat().st_size).encode())
    return h.hexdigest()


def sanitize_filename(name: str) -> str:
    """Strip or replace illegal Windows filename characters (< > : \" / \\ | ? *)."""
    s = re.sub(r"[:]", " -", name)
    s = re.sub(r'[<>"/\\|?*]', "", s)
    return re.sub(r"\s+", " ", s).strip()

# ═══════════════════════════════════════════════════════════════════════════
#  HIGH-PERFORMANCE SAFE FILE SCANNER FOR LARGE DRIVES (1TB+ / 100K+ FILES)
# ═══════════════════════════════════════════════════════════════════════════

SKIP_DIRS = {
    "$recycle.bin", "system volume information", "recovery", "$windows.~bt",
    "$winreagent", "windows", "perflogs", "program files", "program files (x86)",
    "appdata", ".git", "node_modules", ".cache"
}

def is_system_file(name: str) -> bool:
    nl = name.lower()
    return (
        nl in (
            "pagefile.sys", "swapfile.sys", "hiberfil.sys", "dumpstack.log.tmp",
            "desktop.ini", "thumbs.db",
            HISTORY_FILENAME.lower(), MEDIA_HISTORY_FILENAME.lower(), RENAMER_HISTORY_FILENAME.lower(),
        )
        or nl.startswith("$")
    )

def safe_iter_files(folder: str, recursive: bool = True, cancel_event: threading.Event | None = None):
    """
    Safely iterate files without crashing on Windows system/locked folders,
    skipping protected/inaccessible directories, and checking cancellation.
    Yields (entry_name, full_path, size_bytes).
    """
    folder = os.path.abspath(folder)
    if not recursive:
        try:
            with os.scandir(folder) as it:
                for entry in it:
                    if cancel_event and cancel_event.is_set():
                        return
                    try:
                        if entry.is_file(follow_symlinks=False):
                            if is_system_file(entry.name):
                                continue
                            try:
                                sz = entry.stat().st_size
                            except OSError:
                                sz = 0
                            yield entry.name, entry.path, sz
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            return
        return

    for root, dirs, files in os.walk(folder, topdown=True, onerror=lambda e: None):
        if cancel_event and cancel_event.is_set():
            return
        # In-place directory pruning
        dirs[:] = [
            d for d in dirs
            if d.lower() not in SKIP_DIRS and not d.startswith("$") and not d.startswith(".")
        ]
        for fname in files:
            if cancel_event and cancel_event.is_set():
                return
            if is_system_file(fname):
                continue
            full_path = os.path.join(root, fname)
            try:
                sz = os.path.getsize(full_path)
            except OSError:
                sz = 0
            yield fname, full_path, sz


# ═══════════════════════════════════════════════════════════════════════════
#  TV & MOVIE DATABASE (TVMaze API)
# ═══════════════════════════════════════════════════════════════════════════

# In-memory cache for TV show queries: { "show_name_lower": { "name": ..., "episodes": {(s,e): title} } }
_TV_SHOW_CACHE: dict[str, dict] = {}


def fetch_show_data(show_name: str) -> dict:
    """Fetch show metadata and episode titles from TVMaze API (no API key required)."""
    key = show_name.strip().lower()
    if key in _TV_SHOW_CACHE:
        return _TV_SHOW_CACHE[key]

    url = f"https://api.tvmaze.com/singlesearch/shows?q={urllib.parse.quote(show_name)}&embed=episodes"
    req = urllib.request.Request(url, headers={"User-Agent": "FileSorter/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            episodes = {}
            for ep in data.get("_embedded", {}).get("episodes", []):
                s = ep.get("season")
                e = ep.get("number")
                title = ep.get("name")
                if s is not None and e is not None and title:
                    episodes[(s, e)] = sanitize_filename(title)
            summary = re.sub(r"<[^>]+>", "", data.get("summary") or "").strip()
            result = {
                "name": data.get("name") or show_name,
                "premiered": data.get("premiered") or "",
                "status": data.get("status") or "",
                "rating": data.get("rating", {}).get("average") or "N/A",
                "network": (data.get("network") or data.get("webChannel") or {}).get("name") or "Unknown",
                "genres": ", ".join(data.get("genres") or []),
                "summary": summary,
                "episodes": episodes,
            }
            _TV_SHOW_CACHE[key] = result
            return result
    except Exception:
        # Fallback when offline or show not found
        result = {"name": show_name, "episodes": {}}
        _TV_SHOW_CACHE[key] = result
        return result


# ═══════════════════════════════════════════════════════════════════════════
#  ANIME DATABASE (Kitsu API)
# ═══════════════════════════════════════════════════════════════════════════

_ANIME_CACHE: dict[str, dict] = {}


def fetch_anime_data(anime_title: str) -> dict:
    """Fetch anime metadata and initial episodes from Kitsu API (no API key required)."""
    key = anime_title.strip().lower()
    if key in _ANIME_CACHE:
        return _ANIME_CACHE[key]

    url = f"https://kitsu.io/api/edge/anime?filter[text]={urllib.parse.quote(anime_title)}&page[limit]=1"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FileSorter/3.1", "Accept": "application/vnd.api+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data", [])
            if not items:
                res = {"id": "", "name": anime_title, "episodes": {}}
                _ANIME_CACHE[key] = res
                return res

            anime = items[0]
            anime_id = anime.get("id", "")
            attr = anime.get("attributes", {})
            canonical_title = attr.get("canonicalTitle") or anime_title
            synopsis = attr.get("synopsis") or ""
            rating = attr.get("averageRating") or "N/A"
            if rating != "N/A":
                try:
                    rating = f"{float(rating):.1f}%"
                except Exception:
                    pass
            status = (attr.get("status") or "Unknown").capitalize()
            total_eps = attr.get("episodeCount") or "?"
            start_date = attr.get("startDate") or ""
            year = start_date[:4] if start_date else ""

            episodes = {}
            # Fetch first batch of episodes
            ep_url = f"https://kitsu.io/api/edge/anime/{anime_id}/episodes?page[limit]=20"
            ep_req = urllib.request.Request(
                ep_url,
                headers={"User-Agent": "FileSorter/3.1", "Accept": "application/vnd.api+json"},
            )
            try:
                with urllib.request.urlopen(ep_req, timeout=6) as ep_resp:
                    ep_data = json.loads(ep_resp.read().decode("utf-8"))
                    for item in ep_data.get("data", []):
                        ep_attr = item.get("attributes", {})
                        num = ep_attr.get("number")
                        title = ep_attr.get("canonicalTitle")
                        if num is not None and title:
                            episodes[int(num)] = sanitize_filename(title)
            except Exception:
                pass

            result = {
                "id": anime_id,
                "name": canonical_title,
                "year": year,
                "rating": rating,
                "status": status,
                "total_episodes": total_eps,
                "summary": synopsis,
                "episodes": episodes,
            }
            _ANIME_CACHE[key] = result
            return result
    except Exception:
        res = {"id": "", "name": anime_title, "episodes": {}}
        _ANIME_CACHE[key] = res
        return res


def fetch_anime_episode(anime_id: str, ep_number: int, cache_entry: dict) -> str:
    """Fetch specific anime episode title by number if not already cached."""
    if ep_number in cache_entry.get("episodes", {}):
        return cache_entry["episodes"][ep_number]
    if not anime_id:
        return ""
    url = f"https://kitsu.io/api/edge/episodes?filter[media_id]={anime_id}&filter[number]={ep_number}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FileSorter/3.1", "Accept": "application/vnd.api+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data", [])
            if items:
                title = items[0].get("attributes", {}).get("canonicalTitle")
                if title:
                    s_title = sanitize_filename(title)
                    cache_entry.setdefault("episodes", {})[ep_number] = s_title
                    return s_title
    except Exception:
        pass
    return ""


# ═══════════════════════════════════════════════════════════════════════════
#  MEDIA FILENAME PARSER
# ═══════════════════════════════════════════════════════════════════════════

RELEASE_GROUP_PAT = re.compile(r"^\s*\[([a-zA-Z0-9_\- ]+)\]\s*")
BRACKET_TAGS_PAT = re.compile(r"\s*(\[[^\]]*\]|\([^\)]*\))\s*$")
ANIME_ABS_EP_PAT = re.compile(r"^(.*?)[._ -]+(?:Ep|Episode)?[._ -]*(\d{1,4})(?:v\d)?$", re.IGNORECASE)

TV_PATTERNS = [
    # S01E02 or S01E02-E03 or s1e2
    re.compile(r"^(.*?)[._ -]+[sS](\d{1,2})[._ -]*[eE](\d{1,3})(?:[._ -]*[eE]?(\d{1,3}))?", re.IGNORECASE),
    # 1x02 or 01x02
    re.compile(r"^(.*?)[._ -]+(\d{1,2})x(\d{1,3})", re.IGNORECASE),
    # Season 1 Episode 2
    re.compile(r"^(.*?)[._ -]+Season[._ -]?(\d{1,2})[._ -]+Episode[._ -]?(\d{1,3})", re.IGNORECASE),
]

MOVIE_PATTERN = re.compile(r"^(.*?)[._ -]+[\(\[]?(19\d\d|20\d\d)[\)\]]?", re.IGNORECASE)

# Release tags to clean up
COMMON_TAGS = re.compile(
    r"\b(1080p|720p|480p|2160p|4k|uhd|bluray|blu-ray|web-dl|webrip|hdtv|dvdrip|x264|x265|hevc|ddp5\.1|aac|dts|remux|hdr|flac|10-bit|8-bit|dual-audio|multi-sub)\b",
    re.IGNORECASE,
)


def clean_media_title(raw: str) -> str:
    cleaned = COMMON_TAGS.sub("", raw)
    cleaned = re.sub(r"[._]", " ", cleaned).strip()
    cleaned = re.sub(r"-\s*$", "", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.title()


def parse_media_filename(filename: str) -> dict:
    """Parse video filename into TV show episode, Anime episode, or movie details."""
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower()

    # Check release group [Group]
    m_grp = RELEASE_GROUP_PAT.match(stem)
    rel_group = m_grp.group(1).strip() if m_grp else None
    working_stem = RELEASE_GROUP_PAT.sub("", stem) if m_grp else stem

    # Strip trailing bracketed hashes / resolutions for episode detection
    clean_tail = BRACKET_TAGS_PAT.sub("", working_stem)
    while BRACKET_TAGS_PAT.search(clean_tail):
        clean_tail = BRACKET_TAGS_PAT.sub("", clean_tail)

    # 1. Check TV show patterns (SxxExx)
    for pat in TV_PATTERNS:
        m = pat.match(clean_tail) or pat.match(working_stem)
        if m:
            raw_title = m.group(1)
            season = int(m.group(2))
            episode = int(m.group(3))
            clean_name = clean_media_title(raw_title)
            if rel_group:
                return {
                    "type": "Anime",
                    "title": clean_name,
                    "season": season,
                    "episode": episode,
                    "year": None,
                    "group": rel_group,
                    "is_absolute": False,
                    "ext": ext,
                }
            return {
                "type": "TV Show",
                "title": clean_name,
                "season": season,
                "episode": episode,
                "year": None,
                "group": None,
                "is_absolute": False,
                "ext": ext,
            }

    # 2. Check Absolute Episode Anime (e.g. Title - 05 or Title - 1085 or Title Ep 25)
    m_abs = ANIME_ABS_EP_PAT.match(clean_tail)
    if m_abs:
        cand_title = m_abs.group(1).strip()
        ep_num = int(m_abs.group(2))
        if rel_group or not (1900 <= ep_num <= 2099 and not (" - " in working_stem or "Episode" in working_stem or "Ep" in working_stem)):
            clean_name = clean_media_title(cand_title)
            return {
                "type": "Anime",
                "title": clean_name,
                "season": 1,
                "episode": ep_num,
                "year": None,
                "group": rel_group,
                "is_absolute": True,
                "ext": ext,
            }

    # 3. Check Movie patterns (Title + Year)
    m_mov = MOVIE_PATTERN.match(working_stem)
    if m_mov:
        raw_title = m_mov.group(1)
        year = m_mov.group(2)
        clean_name = clean_media_title(raw_title)
        return {
            "type": "Movie",
            "title": clean_name,
            "season": None,
            "episode": None,
            "year": year,
            "group": rel_group,
            "is_absolute": False,
            "ext": ext,
        }

    # 4. Fallback: treat as standalone video
    clean_name = clean_media_title(working_stem)
    return {
        "type": "Video",
        "title": clean_name,
        "season": None,
        "episode": None,
        "year": None,
        "group": rel_group,
        "is_absolute": False,
        "ext": ext,
    }


def scan_media_folder(
    folder: str,
    recursive: bool = True,
    fetch_tvdb: bool = True,
    fetch_anime: bool = True,
    create_season_folders: bool = True,
    structure_by_type: bool = True,
    progress_cb=None,
    cancel_event: threading.Event | None = None,
) -> list[dict]:
    """Scan folder for video files and build destination paths with TVDB/Kitsu metadata."""
    folder_path = Path(folder)
    video_files: list[tuple[str, str, int]] = []

    for name, full_path, size in safe_iter_files(folder, recursive=recursive, cancel_event=cancel_event):
        if cancel_event and cancel_event.is_set():
            break
        if os.path.splitext(name)[1].lower() in VIDEO_EXTENSIONS:
            video_files.append((name, full_path, size))

    total = len(video_files)
    plan: list[dict] = []
    last_cb = 0.0

    # Cache metadata queries by show name
    tvdb_cache: dict[str, dict] = {}
    anime_cache: dict[str, dict] = {}

    for i, (fname, fpath, size) in enumerate(video_files):
        if cancel_event and cancel_event.is_set():
            break

        parsed = parse_media_filename(fname)
        m_type = parsed["type"]
        title = parsed["title"]
        s_num = parsed["season"]
        e_num = parsed["episode"]
        year = parsed["year"]
        ext = parsed["ext"]

        ep_title = ""
        official_show_title = title

        # TV Show lookup
        if m_type == "TV Show":
            if fetch_tvdb:
                if title not in tvdb_cache:
                    tvdb_cache[title] = fetch_show_data(title)
                show_data = tvdb_cache[title]
                official_show_title = show_data.get("name") or title
                episodes = show_data.get("episodes", {})
                ep_title = episodes.get((s_num, e_num), "")

            se_tag = f"S{s_num:02d}E{e_num:02d}"
            if ep_title:
                new_filename = f"{official_show_title} - {se_tag} - {ep_title}{ext}"
            else:
                new_filename = f"{official_show_title} - {se_tag}{ext}"

            dir_parts = []
            if structure_by_type:
                dir_parts.append("TV Shows")
            dir_parts.append(sanitize_filename(official_show_title))
            if create_season_folders:
                dir_parts.append(f"Season {s_num:02d}")

            dest_dir = folder_path.joinpath(*dir_parts)
            dest_file = dest_dir / sanitize_filename(new_filename)

        elif m_type == "Anime":
            is_absolute = parsed.get("is_absolute", False)
            if fetch_anime:
                if title not in anime_cache:
                    anime_cache[title] = fetch_anime_data(title)
                anime_data = anime_cache[title]
                official_show_title = anime_data.get("name") or title
                if anime_data.get("id"):
                    ep_title = fetch_anime_episode(anime_data["id"], e_num, anime_data)
                else:
                    ep_title = anime_data.get("episodes", {}).get(e_num, "")

            if is_absolute or (s_num == 1 and e_num > 30):
                tag = f"Ep {e_num:02d}" if e_num < 100 else f"Ep {e_num}"
            else:
                tag = f"S{s_num:02d}E{e_num:02d}"

            if ep_title:
                new_filename = f"{official_show_title} - {tag} - {ep_title}{ext}"
            else:
                new_filename = f"{official_show_title} - {tag}{ext}"

            dir_parts = []
            if structure_by_type:
                dir_parts.append("Anime")
            dir_parts.append(sanitize_filename(official_show_title))
            if create_season_folders and not is_absolute:
                dir_parts.append(f"Season {s_num:02d}")

            dest_dir = folder_path.joinpath(*dir_parts)
            dest_file = dest_dir / sanitize_filename(new_filename)

        elif m_type == "Movie":
            movie_tag = f"{title} ({year})" if year else title
            new_filename = f"{movie_tag}{ext}"

            dir_parts = []
            if structure_by_type:
                dir_parts.append("Movies")
            dir_parts.append(sanitize_filename(movie_tag))

            dest_dir = folder_path.joinpath(*dir_parts)
            dest_file = dest_dir / sanitize_filename(new_filename)

        else:
            dir_parts = ["Videos"] if structure_by_type else []
            dest_dir = folder_path.joinpath(*dir_parts)
            dest_file = dest_dir / f"{title}{ext}"

        try:
            rel_dest = str(dest_file.relative_to(folder_path))
        except Exception:
            rel_dest = str(dest_file)

        if m_type == "TV Show":
            se_disp = f"S{s_num:02d}E{e_num:02d}"
        elif m_type == "Anime":
            if parsed.get("is_absolute") or (s_num == 1 and e_num > 30):
                se_disp = f"Ep {e_num:02d}" if e_num < 100 else f"Ep {e_num}"
            else:
                se_disp = f"S{s_num:02d}E{e_num:02d}"
        elif m_type == "Movie":
            se_disp = year or "-"
        else:
            se_disp = "-"

        plan.append({
            "name": fname,
            "src": fpath,
            "dest": str(dest_file),
            "rel_dest": rel_dest,
            "type": m_type,
            "title": official_show_title,
            "se_tag": se_disp,
            "ep_title": ep_title or "-",
            "size": size,
            "selected": True,
        })

        now = time.monotonic()
        if progress_cb and (i == total - 1 or now - last_cb >= 0.05):
            last_cb = now
            progress_cb(i + 1, total)

    plan.sort(key=lambda x: (x["type"], x["title"], x["name"].lower()))
    return plan


def execute_media_sort(plan: list[dict], folder: str, progress_cb=None) -> list[dict]:
    selected = [e for e in plan if e.get("selected", True)]
    history: list[dict] = []
    total = len(selected)
    last_cb = 0.0

    for i, entry in enumerate(selected):
        dest_path = Path(entry["dest"])
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            final_dest = dest_path
            if final_dest.exists() and str(final_dest) != entry["src"]:
                stem = final_dest.stem
                ext = final_dest.suffix
                counter = 1
                while final_dest.exists():
                    final_dest = dest_path.parent / f"{stem} ({counter}){ext}"
                    counter += 1

            shutil.move(entry["src"], str(final_dest))
            history.append({"src": entry["src"], "dest": str(final_dest)})
        except (OSError, PermissionError, shutil.Error):
            pass

        now = time.monotonic()
        if progress_cb and (i == total - 1 or now - last_cb >= 0.05):
            last_cb = now
            progress_cb(i + 1, total)

    if history:
        history_file = Path(folder) / MEDIA_HISTORY_FILENAME
        record = {"timestamp": datetime.datetime.now().isoformat(), "moves": history}
        all_records = []
        if history_file.exists():
            try:
                all_records = json.loads(history_file.read_text(encoding="utf-8"))
            except Exception:
                all_records = []
        all_records.append(record)
        try:
            history_file.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
        except Exception:
            pass
    return history


def undo_media_sort(folder: str, progress_cb=None) -> int:
    history_file = Path(folder) / MEDIA_HISTORY_FILENAME
    if not history_file.exists():
        return 0
    try:
        all_records = json.loads(history_file.read_text(encoding="utf-8"))
    except Exception:
        return 0
    if not all_records:
        return 0

    last = all_records.pop()
    moves = last.get("moves", [])
    total = len(moves)
    restored = 0
    last_cb = 0.0

    for i, entry in enumerate(moves):
        dest_file = Path(entry["dest"])
        src_file = Path(entry["src"])
        try:
            if dest_file.exists():
                src_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dest_file), str(src_file))
                restored += 1
                parent = dest_file.parent
                while parent != Path(folder):
                    try:
                        parent.rmdir()
                        parent = parent.parent
                    except OSError:
                        break
        except (OSError, PermissionError, shutil.Error):
            pass

        now = time.monotonic()
        if progress_cb and (i == total - 1 or now - last_cb >= 0.05):
            last_cb = now
            progress_cb(i + 1, total)

    try:
        if all_records:
            history_file.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
        else:
            history_file.unlink(missing_ok=True)
    except Exception:
        pass
    return restored

def build_ext_map(categories: dict[str, list[str]]) -> dict[str, str]:
    m: dict[str, str] = {}
    for cat, exts in categories.items():
        for ext in exts:
            m[ext.lower()] = cat
    return m


def scan_general_folder(
    folder: str,
    ext_map: dict[str, str],
    recursive: bool = False,
    sort_uncategorised_to_misc: bool = False,
    progress_cb=None,
    cancel_event: threading.Event | None = None,
) -> list[dict]:
    plan: list[dict] = []
    folder_path = Path(folder)
    seen_hashes: dict[tuple[str, int], str] = {}
    count = 0
    last_report_time = 0.0

    for name, full_path, size in safe_iter_files(folder, recursive=recursive, cancel_event=cancel_event):
        if cancel_event and cancel_event.is_set():
            break

        ext = os.path.splitext(name)[1].lower()
        category = ext_map.get(ext)
        if not category:
            if sort_uncategorised_to_misc:
                category = "Misc"
            else:
                continue

        count += 1
        key = (name.lower(), size)
        is_dup = key in seen_hashes
        dup_of = seen_hashes.get(key, "")
        if not is_dup:
            seen_hashes[key] = name

        dest_dir = folder_path / category
        plan.append({
            "name": name,
            "src": full_path,
            "dest": str(dest_dir / name),
            "category": category,
            "size": size,
            "duplicate": is_dup,
            "duplicate_of": dup_of,
            "selected": True,
        })

        if progress_cb:
            now = time.monotonic()
            if count % 200 == 0 or now - last_report_time >= 0.15:
                last_report_time = now
                progress_cb(count)

    plan.sort(key=lambda x: (x["category"], x["name"].lower()))
    return plan


def execute_general_sort(plan: list[dict], folder: str, progress_cb=None) -> list[dict]:
    selected = [e for e in plan if e.get("selected", True)]
    history: list[dict] = []
    total = len(selected)
    last_cb = 0.0

    for i, entry in enumerate(selected):
        dest_dir = str(Path(entry["dest"]).parent)
        try:
            os.makedirs(dest_dir, exist_ok=True)
            final_dest = entry["dest"]
            if os.path.exists(final_dest):
                stem = Path(entry["name"]).stem
                ext = Path(entry["name"]).suffix
                counter = 1
                while os.path.exists(final_dest):
                    final_dest = str(Path(dest_dir) / f"{stem} ({counter}){ext}")
                    counter += 1
            shutil.move(entry["src"], final_dest)
            history.append({"src": entry["src"], "dest": final_dest})
        except (OSError, PermissionError, shutil.Error):
            pass

        now = time.monotonic()
        if progress_cb and (i == total - 1 or now - last_cb >= 0.05):
            last_cb = now
            progress_cb(i + 1, total)

    if history:
        history_path = Path(folder) / HISTORY_FILENAME
        record = {"timestamp": datetime.datetime.now().isoformat(), "moves": history}
        all_records = []
        if history_path.exists():
            try:
                all_records = json.loads(history_path.read_text(encoding="utf-8"))
            except Exception:
                all_records = []
        all_records.append(record)
        try:
            history_path.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
        except Exception:
            pass
    return history


def undo_general_sort(folder: str, progress_cb=None) -> int:
    history_path = Path(folder) / HISTORY_FILENAME
    if not history_path.exists():
        return 0
    try:
        all_records = json.loads(history_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    if not all_records:
        return 0

    last = all_records.pop()
    moves = last.get("moves", [])
    total = len(moves)
    restored = 0
    last_cb = 0.0

    for i, entry in enumerate(moves):
        dest_file = Path(entry["dest"])
        src_file = Path(entry["src"])
        try:
            if dest_file.exists():
                src_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dest_file), str(src_file))
                restored += 1
                try:
                    dest_file.parent.rmdir()
                except OSError:
                    pass
        except (OSError, PermissionError, shutil.Error):
            pass

        now = time.monotonic()
        if progress_cb and (i == total - 1 or now - last_cb >= 0.05):
            last_cb = now
            progress_cb(i + 1, total)

    try:
        if all_records:
            history_path.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
        else:
            history_path.unlink(missing_ok=True)
    except Exception:
        pass
    return restored

def apply_rename_rules(filename: str, idx: int, rules: dict) -> str:
    """Compute new filename by applying search/replace, casing, numbering, etc."""
    p = Path(filename)
    stem = p.stem
    ext = p.suffix

    find_text = rules.get("find", "")
    repl_text = rules.get("replace", "")
    match_case = rules.get("match_case", False)
    use_regex = rules.get("use_regex", False)
    prefix = rules.get("prefix", "")
    suffix = rules.get("suffix", "")
    case_mode = rules.get("case_mode", "No Change")
    space_mode = rules.get("space_mode", "Keep spaces")
    lowercase_ext = rules.get("lowercase_ext", False)
    add_numbering = rules.get("add_numbering", False)
    num_pos = rules.get("num_pos", "suffix")
    num_start = rules.get("num_start", 1)
    num_pad = rules.get("num_pad", 2)

    # 1. Find & Replace
    if find_text:
        if use_regex:
            try:
                flags = 0 if match_case else re.IGNORECASE
                stem = re.sub(find_text, repl_text, stem, flags=flags)
            except Exception:
                pass
        else:
            if match_case:
                stem = stem.replace(find_text, repl_text)
            else:
                pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                stem = pattern.sub(repl_text, stem)

    # 2. Case transformation
    if case_mode == "lowercase":
        stem = stem.lower()
    elif case_mode == "UPPERCASE":
        stem = stem.upper()
    elif case_mode == "Title Case":
        stem = stem.title()
    elif case_mode == "Capitalize Words":
        stem = " ".join(w.capitalize() for w in stem.split(" "))

    # 3. Spaces handling
    if space_mode == "Replace with _ (underscore)":
        stem = re.sub(r"\s+", "_", stem)
    elif space_mode == "Replace with - (hyphen)":
        stem = re.sub(r"\s+", "-", stem)
    elif space_mode == "Remove spaces":
        stem = re.sub(r"\s+", "", stem)

    # 4. Prefix & Suffix
    if prefix:
        stem = prefix + stem
    if suffix:
        stem = stem + suffix

    # 5. Numbering
    if add_numbering:
        n = num_start + idx
        num_str = f"{n:0{num_pad}d}"
        if num_pos == "prefix":
            stem = f"{num_str}_{stem}"
        else:
            stem = f"{stem}_{num_str}"

    # 6. Extension
    if lowercase_ext:
        ext = ext.lower()

    return sanitize_filename(stem) + ext


def scan_renamer_folder(
    folder: str,
    recursive: bool = False,
    rules: dict | None = None,
    progress_cb=None,
    cancel_event: threading.Event | None = None,
) -> list[dict]:
    """Scan folder for files and compute preview of renamed files based on active rules."""
    plan: list[dict] = []
    active_rules = rules or {}
    raw_files: list[tuple[str, str, int]] = []
    count = 0
    last_report_time = 0.0

    for name, full_path, size in safe_iter_files(folder, recursive=recursive, cancel_event=cancel_event):
        if cancel_event and cancel_event.is_set():
            break
        raw_files.append((name, full_path, size))
        count += 1
        if progress_cb:
            now = time.monotonic()
            if count % 200 == 0 or now - last_report_time >= 0.15:
                last_report_time = now
                progress_cb(count)

    raw_files.sort(key=lambda x: x[0].lower())
    seen_new_names: dict[str, int] = defaultdict(int)

    for idx, (name, full_path, size) in enumerate(raw_files):
        new_name = apply_rename_rules(name, idx, active_rules) if active_rules else name
        changed = (new_name != name)
        status = "Pending"
        dest_path = Path(full_path).parent / new_name

        seen_new_names[str(dest_path).lower()] += 1
        if seen_new_names[str(dest_path).lower()] > 1:
            status = "Duplicate Name"
        elif dest_path.exists() and str(dest_path) != full_path:
            status = "Target Exists"

        plan.append({
            "name": name,
            "new_name": new_name,
            "src": full_path,
            "dest": str(dest_path),
            "size": size,
            "changed": changed,
            "status": status,
            "selected": True,
        })

    return plan


def execute_bulk_rename(plan: list[dict], folder: str, progress_cb=None) -> list[dict]:
    """Execute the renaming plan safely using two-step moves to avoid collisions."""
    selected = [e for e in plan if e.get("selected", True) and e.get("changed", False)]
    total = len(selected)
    history: list[dict] = []

    if not selected:
        return history

    temp_moves: list[tuple[dict, Path, Path, Path]] = []
    for i, entry in enumerate(selected):
        src_path = Path(entry["src"])
        final_dest = Path(entry["dest"])

        if final_dest.exists() and str(final_dest) != str(src_path):
            stem = final_dest.stem
            ext = final_dest.suffix
            counter = 1
            while final_dest.exists():
                final_dest = final_dest.parent / f"{stem} ({counter}){ext}"
                counter += 1

        temp_dest = src_path.parent / f"__renamer_tmp_{i}_{hashlib.md5(str(src_path).encode()).hexdigest()[:6]}_{src_path.name}"
        temp_moves.append((entry, src_path, temp_dest, final_dest))

    # Pass 1: rename to temp
    for entry, src_path, temp_dest, final_dest in temp_moves:
        try:
            if src_path.exists():
                os.rename(str(src_path), str(temp_dest))
        except (OSError, PermissionError):
            pass

    # Pass 2: rename from temp to final
    last_cb = 0.0
    for i, (entry, src_path, temp_dest, final_dest) in enumerate(temp_moves):
        try:
            if temp_dest.exists():
                os.rename(str(temp_dest), str(final_dest))
                history.append({"src": str(src_path), "dest": str(final_dest)})
        except (OSError, PermissionError):
            pass

        now = time.monotonic()
        if progress_cb and (i == total - 1 or now - last_cb >= 0.05):
            last_cb = now
            progress_cb(i + 1, total)

    if history:
        history_file = Path(folder) / RENAMER_HISTORY_FILENAME
        record = {"timestamp": datetime.datetime.now().isoformat(), "moves": history}
        all_records = []
        if history_file.exists():
            try:
                all_records = json.loads(history_file.read_text(encoding="utf-8"))
            except Exception:
                all_records = []
        all_records.append(record)
        try:
            history_file.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
        except Exception:
            pass
    return history


def undo_bulk_rename(folder: str, progress_cb=None) -> int:
    """Revert the last bulk rename in reverse order."""
    history_file = Path(folder) / RENAMER_HISTORY_FILENAME
    if not history_file.exists():
        return 0
    try:
        all_records = json.loads(history_file.read_text(encoding="utf-8"))
    except Exception:
        return 0
    if not all_records:
        return 0

    last = all_records.pop()
    moves = last.get("moves", [])
    total = len(moves)
    restored = 0
    last_cb = 0.0

    for i, entry in enumerate(reversed(moves)):
        dest_file = Path(entry["dest"])
        src_file = Path(entry["src"])
        try:
            if dest_file.exists():
                os.rename(str(dest_file), str(src_file))
                restored += 1
        except (OSError, PermissionError):
            pass

        now = time.monotonic()
        if progress_cb and (i == total - 1 or now - last_cb >= 0.05):
            last_cb = now
            progress_cb(i + 1, total)

    try:
        if all_records:
            history_file.write_text(json.dumps(all_records, indent=2), encoding="utf-8")
        else:
            history_file.unlink(missing_ok=True)
    except Exception:
        pass
    return restored

def load_settings() -> dict:
    defaults = {
        "theme": "dark",
        "last_folder": "",
        "last_media_folder": "",
        "last_renamer_folder": "",
        "active_tab": "files",
        "recursive": False,
        "sort_misc": False,
        "media_recursive": True,
        "media_fetch_tvdb": True,
        "media_fetch_anime": True,
        "media_season_folders": True,
        "media_structure_by_type": True,
        "renamer_recursive": False,
        "renamer_case": "No Change",
        "renamer_spaces": "Keep spaces",
        "renamer_lower_ext": False,
        "renamer_numbering": False,
        "renamer_num_pos": "suffix",
        "renamer_num_start": 1,
        "renamer_num_pad": 2,
        "custom_categories": {},
        "window_geometry": "1120x740",
    }
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            defaults.update(saved)
        except Exception:
            pass
    return defaults


def save_settings(settings: dict):
    try:
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
#  APPLICATION CLASS
# ═══════════════════════════════════════════════════════════════════════════

class FileSorterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        self._theme = self.settings.get("theme", "dark")
        self.T = THEMES[self._theme]
        ctk.set_appearance_mode(self._theme)

        self.title(f"{APP_NAME}  v{APP_VERSION} — Files, Media & Renamer")
        geo = self.settings.get("window_geometry", "1120x740")
        self.geometry(geo)
        self.minsize(1000, 660)
        self.configure(fg_color=self.T["bg"])

        self.categories = dict(DEFAULT_CATEGORIES)
        custom = self.settings.get("custom_categories", {})
        if custom:
            self.categories.update(custom)
        self.ext_map = build_ext_map(self.categories)

        # Active tab state: "files", "media", or "renamer"
        self.active_tab = self.settings.get("active_tab", "files")

        # General sorter state
        self.current_folder: str | None = self.settings.get("last_folder") or None
        self.current_plan: list[dict] = []
        self._check_vars: list[tk.BooleanVar] = []

        # Media sorter state
        self.current_media_folder: str | None = self.settings.get("last_media_folder") or None
        self.current_media_plan: list[dict] = []
        self._media_check_vars: list[tk.BooleanVar] = []

        # Bulk renamer state
        self.current_renamer_folder: str | None = self.settings.get("last_renamer_folder") or None
        self.current_renamer_plan: list[dict] = []
        self._renamer_check_vars: list[tk.BooleanVar] = []

        self._is_busy = False

        # Pagination & Large Drive Virtualization State
        self.general_page = 1
        self.general_page_size = 100
        self.general_filtered_plan: list[dict] = []
        self._general_scanning = False
        self._general_scan_cancel = threading.Event()

        self.media_page = 1
        self.media_page_size = 100
        self.media_filtered_plan: list[dict] = []
        self._media_scanning = False
        self._media_scan_cancel = threading.Event()

        self.renamer_page = 1
        self.renamer_page_size = 100
        self.renamer_filtered_plan: list[dict] = []
        self._renamer_scanning = False
        self._renamer_scan_cancel = threading.Event()
        self._renamer_debounce_id = None

        # Pillow Antialiased Sun / Moon Icons
        self._sun_icon = ctk.CTkImage(
            light_image=_create_sun_icon(18, (255, 255, 255)),
            dark_image=_create_sun_icon(18, (255, 255, 255)),
            size=(18, 18),
        )
        self._moon_icon = ctk.CTkImage(
            light_image=_create_moon_icon(18, (255, 255, 255)),
            dark_image=_create_moon_icon(18, (255, 255, 255)),
            size=(18, 18),
        )

        self._build_ui()

        # Restore folder entries
        if self.current_folder and Path(self.current_folder).is_dir():
            self.folder_entry.insert(0, self.current_folder)
            self._set_btn_state(self.scan_btn, True, self.T["btn_primary"])
            self._update_general_undo_state()

        if self.current_media_folder and Path(self.current_media_folder).is_dir():
            self.media_folder_entry.insert(0, self.current_media_folder)
            self._set_btn_state(self.media_scan_btn, True, self.T["btn_primary"])
            self._update_media_undo_state()

        if self.current_renamer_folder and Path(self.current_renamer_folder).is_dir():
            self.renamer_folder_entry.insert(0, self.current_renamer_folder)
            self._set_btn_state(self.renamer_scan_btn, True, self.T["btn_primary"])
            self._update_renamer_undo_state()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_theme(self):
        self.T = THEMES[self._theme]
        ctk.set_appearance_mode(self._theme)
        self.settings["theme"] = self._theme
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        if self.current_folder:
            self.folder_entry.insert(0, self.current_folder)
            self._set_btn_state(self.scan_btn, True, self.T["btn_primary"])
            self._update_general_undo_state()
            if self.current_plan:
                self._populate_file_table(self.current_plan)
                self._update_general_stats(self.current_plan)

        if self.current_media_folder:
            self.media_folder_entry.insert(0, self.current_media_folder)
            self._set_btn_state(self.media_scan_btn, True, self.T["btn_primary"])
            self._update_media_undo_state()
            if self.current_media_plan:
                self._populate_media_table(self.current_media_plan)

        if self.current_renamer_folder:
            self.renamer_folder_entry.insert(0, self.current_renamer_folder)
            self._set_btn_state(self.renamer_scan_btn, True, self.T["btn_primary"])
            self._update_renamer_undo_state()
            if self.current_renamer_plan:
                self._populate_renamer_table(self.current_renamer_plan)


    def _get_cat_color(self, category: str) -> str:
        idx = abs(hash(category)) % len(CHART_COLORS)
        return CHART_COLORS[idx]
    def _toggle_theme(self):
        self._theme = "light" if self._theme == "dark" else "dark"
        self._apply_theme()

    def _set_btn_state(self, btn: ctk.CTkButton, enabled: bool, active_color: str, text_color: str = "#ffffff"):
        if enabled:
            btn.configure(
                state="normal",
                fg_color=active_color,
                hover_color=self.T["accent_hover"],
                text_color=text_color,
                border_width=0,
            )
        else:
            btn.configure(
                state="disabled",
                fg_color=self.T["card_alt"],
                text_color=self.T["text_muted"],
                border_width=1,
                border_color=self.T["border"],
            )

    # ── UI Construction ─────────────────────────────────────────────────────
    def _build_ui(self):
        T = self.T
        self.configure(fg_color=T["bg"])

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # ════════════════════════════════════════════════════════════════
        #  SIDEBAR
        # ════════════════════════════════════════════════════════════════
        sidebar = ctk.CTkFrame(main, width=270, fg_color=T["sidebar"],
                               corner_radius=0, border_width=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        # Title bar & Theme Icon
        title_frame = ctk.CTkFrame(sidebar, fg_color=T["header"],
                                   corner_radius=0, height=56)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)

        ctk.CTkLabel(
            title_frame, text=APP_NAME,
            font=_font(18, "bold"), text_color="#ffffff",
        ).pack(side="left", padx=14)

        ctk.CTkLabel(
            title_frame, text=f"v{APP_VERSION}",
            font=_font(12), text_color="#93c5fd",
        ).pack(side="left")

        theme_icon = self._sun_icon if self._theme == "dark" else self._moon_icon
        theme_btn = ctk.CTkButton(
            title_frame, text="", image=theme_icon,
            width=34, height=34, corner_radius=6,
            fg_color="#0f172a" if self._theme == "dark" else "#1e3a8a",
            hover_color=T["accent_hover"],
            border_width=1, border_color="#334155" if self._theme == "dark" else "#93c5fd",
            command=self._toggle_theme,
        )
        theme_btn.pack(side="right", padx=12)

        # ── Navigation Tabs in Sidebar ──────────────────────────────────
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=12, pady=(12, 6))

        self.tab_files_btn = ctk.CTkButton(
            nav_frame, text="Files & Folders", height=36,
            font=_font(13, "bold"), corner_radius=6,
            command=lambda: self._switch_tab("files"),
        )
        self.tab_files_btn.pack(fill="x", pady=2)

        self.tab_media_btn = ctk.CTkButton(
            nav_frame, text="Media (TV & Movies)", height=36,
            font=_font(13, "bold"), corner_radius=6,
            command=lambda: self._switch_tab("media"),
        )
        self.tab_media_btn.pack(fill="x", pady=2)

        self.tab_renamer_btn = ctk.CTkButton(
            nav_frame, text="Bulk Renamer", height=36,
            font=_font(13, "bold"), corner_radius=6,
            command=lambda: self._switch_tab("renamer"),
        )
        self.tab_renamer_btn.pack(fill="x", pady=2)

        # Separator
        ctk.CTkFrame(sidebar, height=1, fg_color=T["border"]).pack(
            fill="x", padx=14, pady=10)

        # ── Tab 1 Sidebar Controls (General Sorter) ─────────────────────
        self.side_files_frame = ctk.CTkFrame(sidebar, fg_color="transparent")

        ctk.CTkLabel(
            self.side_files_frame, text="FILE OPTIONS",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", padx=14, pady=(4, 6))

        self.recursive_var = tk.BooleanVar(value=self.settings.get("recursive", False))
        ctk.CTkCheckBox(
            self.side_files_frame, text="Scan subfolders (recursive)",
            variable=self.recursive_var, font=_font(13), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        self.misc_var = tk.BooleanVar(value=self.settings.get("sort_misc", False))
        ctk.CTkCheckBox(
            self.side_files_frame, text="Sort unknown to Misc",
            variable=self.misc_var, font=_font(13), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        ctk.CTkFrame(self.side_files_frame, height=1, fg_color=T["border"]).pack(
            fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            self.side_files_frame, text="DISTRIBUTION",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", padx=14, pady=(0, 6))

        self.stats_frame = ctk.CTkScrollableFrame(
            self.side_files_frame, fg_color="transparent",
            scrollbar_button_color=T["scrollbar"],
            scrollbar_button_hover_color=T["scrollbar_hover"],
        )
        self.stats_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        ctk.CTkLabel(
            self.stats_frame, text="No scan data yet",
            font=_font(13), text_color=T["text_muted"],
        ).pack(pady=20)

        # ── Tab 2 Sidebar Controls (Media Sorter) ───────────────────────
        self.side_media_frame = ctk.CTkFrame(sidebar, fg_color="transparent")

        ctk.CTkLabel(
            self.side_media_frame, text="MEDIA OPTIONS",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", padx=14, pady=(4, 6))

        self.media_tvdb_var = tk.BooleanVar(value=self.settings.get("media_fetch_tvdb", True))
        ctk.CTkCheckBox(
            self.side_media_frame, text="Fetch TV episode titles (TVDB)",
            variable=self.media_tvdb_var, font=_font(13), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        self.media_anime_var = tk.BooleanVar(value=self.settings.get("media_fetch_anime", True))
        ctk.CTkCheckBox(
            self.side_media_frame, text="Fetch Anime titles (Kitsu DB)",
            variable=self.media_anime_var, font=_font(13), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        self.media_season_var = tk.BooleanVar(value=self.settings.get("media_season_folders", True))
        ctk.CTkCheckBox(
            self.side_media_frame, text="Create Season subfolders",
            variable=self.media_season_var, font=_font(13), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        self.media_struct_var = tk.BooleanVar(value=self.settings.get("media_structure_by_type", True))
        ctk.CTkCheckBox(
            self.side_media_frame, text="Separate TV / Anime / Movies",
            variable=self.media_struct_var, font=_font(13), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        self.media_rec_var = tk.BooleanVar(value=self.settings.get("media_recursive", True))
        ctk.CTkCheckBox(
            self.side_media_frame, text="Scan subfolders (recursive)",
            variable=self.media_rec_var, font=_font(13), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        ctk.CTkFrame(self.side_media_frame, height=1, fg_color=T["border"]).pack(
            fill="x", padx=14, pady=10)

        # TV & Anime Database Search tool buttons
        ctk.CTkLabel(
            self.side_media_frame, text="DATABASE TOOLS",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", padx=14, pady=(0, 6))

        ctk.CTkButton(
            self.side_media_frame, text="Search TV Database...", height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            text_color="#ffffff",
            command=self._open_tvdb_browser,
        ).pack(fill="x", padx=12, pady=3)

        ctk.CTkButton(
            self.side_media_frame, text="Search Anime Database...", height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color="#ec4899", hover_color="#db2777",
            text_color="#ffffff",
            command=self._open_animedb_browser,
        ).pack(fill="x", padx=12, pady=3)

        # ── Tab 3 Sidebar Controls (Bulk Renamer) ───────────────────────
        self.side_renamer_frame = ctk.CTkFrame(sidebar, fg_color="transparent")

        ctk.CTkLabel(
            self.side_renamer_frame, text="RENAMING OPTIONS",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", padx=14, pady=(4, 6))

        # Case Transform
        ctk.CTkLabel(
            self.side_renamer_frame, text="Case Transformation:",
            font=_font(11, "bold"), text_color=T["text_muted"],
        ).pack(anchor="w", padx=14, pady=(2, 2))
        self.renamer_case_var = tk.StringVar(value=self.settings.get("renamer_case", "No Change"))
        self.renamer_case_drop = ctk.CTkOptionMenu(
            self.side_renamer_frame,
            values=["No Change", "lowercase", "UPPERCASE", "Title Case", "Capitalize Words"],
            variable=self.renamer_case_var,
            font=_font(12), height=32, corner_radius=6,
            fg_color=T["card_alt"], button_color=T["border"],
            text_color=T["text"], dropdown_fg_color=T["card"],
            dropdown_text_color=T["text"],
            command=lambda _: self._on_renamer_rule_change(),
        )
        self.renamer_case_drop.pack(fill="x", padx=14, pady=(0, 6))

        # Space Handling
        ctk.CTkLabel(
            self.side_renamer_frame, text="Space Handling:",
            font=_font(11, "bold"), text_color=T["text_muted"],
        ).pack(anchor="w", padx=14, pady=(2, 2))
        self.renamer_space_var = tk.StringVar(value=self.settings.get("renamer_spaces", "Keep spaces"))
        self.renamer_space_drop = ctk.CTkOptionMenu(
            self.side_renamer_frame,
            values=["Keep spaces", "Replace with _ (underscore)", "Replace with - (hyphen)", "Remove spaces"],
            variable=self.renamer_space_var,
            font=_font(12), height=32, corner_radius=6,
            fg_color=T["card_alt"], button_color=T["border"],
            text_color=T["text"], dropdown_fg_color=T["card"],
            dropdown_text_color=T["text"],
            command=lambda _: self._on_renamer_rule_change(),
        )
        self.renamer_space_drop.pack(fill="x", padx=14, pady=(0, 6))

        # Lowercase extensions
        self.renamer_lower_ext_var = tk.BooleanVar(value=self.settings.get("renamer_lower_ext", False))
        ctk.CTkCheckBox(
            self.side_renamer_frame, text="Lowercase file extensions",
            variable=self.renamer_lower_ext_var, font=_font(12), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
            command=self._on_renamer_rule_change,
        ).pack(anchor="w", padx=14, pady=3)

        # Numbering
        self.renamer_num_var = tk.BooleanVar(value=self.settings.get("renamer_numbering", False))
        ctk.CTkCheckBox(
            self.side_renamer_frame, text="Add numbering sequence",
            variable=self.renamer_num_var, font=_font(12), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
            command=self._on_renamer_rule_change,
        ).pack(anchor="w", padx=14, pady=3)

        num_sub_frame = ctk.CTkFrame(self.side_renamer_frame, fg_color=T["card_alt"], corner_radius=6)
        num_sub_frame.pack(fill="x", padx=14, pady=4)

        self.renamer_num_pos_var = tk.StringVar(value=self.settings.get("renamer_num_pos", "suffix"))
        num_pos_seg = ctk.CTkSegmentedButton(
            num_sub_frame, values=["suffix", "prefix"],
            variable=self.renamer_num_pos_var, height=28, font=_font(11, "bold"),
            selected_color=T["btn_primary"], selected_hover_color=T["btn_primary_hover"],
            command=lambda _: self._on_renamer_rule_change(),
        )
        num_pos_seg.pack(fill="x", padx=6, pady=(6, 4))

        num_inputs = ctk.CTkFrame(num_sub_frame, fg_color="transparent")
        num_inputs.pack(fill="x", padx=6, pady=(0, 6))

        ctk.CTkLabel(num_inputs, text="Start:", font=_font(11), text_color=T["text_dim"]).pack(side="left", padx=(2, 2))
        self.renamer_start_entry = ctk.CTkEntry(
            num_inputs, width=42, height=26, font=_font(11),
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
        )
        self.renamer_start_entry.insert(0, str(self.settings.get("renamer_num_start", 1)))
        self.renamer_start_entry.pack(side="left", padx=(0, 8))
        self.renamer_start_entry.bind("<KeyRelease>", lambda _: self._on_renamer_rule_change())

        ctk.CTkLabel(num_inputs, text="Padding:", font=_font(11), text_color=T["text_dim"]).pack(side="left", padx=(2, 2))
        self.renamer_pad_entry = ctk.CTkEntry(
            num_inputs, width=42, height=26, font=_font(11),
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
        )
        self.renamer_pad_entry.insert(0, str(self.settings.get("renamer_num_pad", 2)))
        self.renamer_pad_entry.pack(side="left")
        self.renamer_pad_entry.bind("<KeyRelease>", lambda _: self._on_renamer_rule_change())

        # Recursive check
        self.renamer_rec_var = tk.BooleanVar(value=self.settings.get("renamer_recursive", False))
        ctk.CTkCheckBox(
            self.side_renamer_frame, text="Scan subfolders (recursive)",
            variable=self.renamer_rec_var, font=_font(12), text_color=T["text"],
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            border_color=T["border"], checkmark_color="#ffffff",
        ).pack(anchor="w", padx=14, pady=3)

        ctk.CTkFrame(self.side_renamer_frame, height=1, fg_color=T["border"]).pack(
            fill="x", padx=14, pady=8)

        # Quick Actions in Sidebar
        ctk.CTkLabel(
            self.side_renamer_frame, text="QUICK ACTIONS",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", padx=14, pady=(0, 4))

        ctk.CTkButton(
            self.side_renamer_frame, text="Clean Spaces & Symbols", height=32,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text"], border_width=1, border_color=T["border"],
            command=self._clean_filenames_preset,
        ).pack(fill="x", padx=12, pady=2)

        ctk.CTkButton(
            self.side_renamer_frame, text="Reset Renamer Rules", height=32,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text_muted"], border_width=1, border_color=T["border"],
            command=self._reset_renamer_rules,
        ).pack(fill="x", padx=12, pady=2)

        # Bottom Tools in Sidebar
        bottom_tools = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_tools.pack(fill="x", side="bottom", padx=12, pady=12)

        self.edit_cat_btn = ctk.CTkButton(
            bottom_tools, text="Edit Categories", height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text"], border_width=1, border_color=T["border"],
            command=self._open_category_editor,
        )
        self.edit_cat_btn.pack(fill="x", pady=2)

        self.export_report_btn = ctk.CTkButton(
            bottom_tools, text="Export CSV Report", height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text"], border_width=1, border_color=T["border"],
            command=self._export_report,
        )
        self.export_report_btn.pack(fill="x", pady=2)

        # ════════════════════════════════════════════════════════════════
        #  RIGHT CONTENT CONTAINERS (TABS)
        # ════════════════════════════════════════════════════════════════
        content_box = ctk.CTkFrame(main, fg_color="transparent")
        content_box.grid(row=0, column=1, sticky="nsew")
        content_box.grid_rowconfigure(0, weight=1)
        content_box.grid_columnconfigure(0, weight=1)

        # Container 1: General File Sorter
        self.files_content = ctk.CTkFrame(content_box, fg_color="transparent")
        self.files_content.grid(row=0, column=0, sticky="nsew")
        self.files_content.grid_rowconfigure(3, weight=1)
        self.files_content.grid_columnconfigure(0, weight=1)
        self._build_general_files_view(self.files_content)

        # Container 2: Media Sorter
        self.media_content = ctk.CTkFrame(content_box, fg_color="transparent")
        self.media_content.grid(row=0, column=0, sticky="nsew")
        self.media_content.grid_rowconfigure(3, weight=1)
        self.media_content.grid_columnconfigure(0, weight=1)
        self._build_media_view(self.media_content)

        # Container 3: Bulk Renamer
        self.renamer_content = ctk.CTkFrame(content_box, fg_color="transparent")
        self.renamer_content.grid(row=0, column=0, sticky="nsew")
        self.renamer_content.grid_rowconfigure(4, weight=1)
        self.renamer_content.grid_columnconfigure(0, weight=1)
        self._build_renamer_view(self.renamer_content)

        # Initialize view
        self._switch_tab(self.active_tab)

    # ── Tab Switching ───────────────────────────────────────────────────────
    def _switch_tab(self, tab_name: str):
        self.active_tab = tab_name
        self.settings["active_tab"] = tab_name
        T = self.T

        # Reset all tab button styles
        for btn in (self.tab_files_btn, self.tab_media_btn, self.tab_renamer_btn):
            btn.configure(
                fg_color=T["card_alt"], text_color=T["text_dim"],
                border_width=1, border_color=T["border"]
            )

        self.side_files_frame.pack_forget()
        self.side_media_frame.pack_forget()
        self.side_renamer_frame.pack_forget()
        self.files_content.grid_remove()
        self.media_content.grid_remove()
        self.renamer_content.grid_remove()

        if tab_name == "files":
            self.tab_files_btn.configure(fg_color=T["btn_primary"], text_color="#ffffff", border_width=0)
            self.side_files_frame.pack(fill="both", expand=True)
            self.files_content.grid()
            self.edit_cat_btn.pack(fill="x", pady=2)
        elif tab_name == "media":
            self.tab_media_btn.configure(fg_color=T["btn_primary"], text_color="#ffffff", border_width=0)
            self.side_media_frame.pack(fill="both", expand=True)
            self.media_content.grid()
            self.edit_cat_btn.pack_forget()
        elif tab_name == "renamer":
            self.tab_renamer_btn.configure(fg_color=T["btn_primary"], text_color="#ffffff", border_width=0)
            self.side_renamer_frame.pack(fill="both", expand=True)
            self.renamer_content.grid()
            self.edit_cat_btn.pack_forget()

    # ═══════════════════════════════════════════════════════════════════════
    #  VIEW 1: GENERAL FILE SORTER
    # ═══════════════════════════════════════════════════════════════════════
    def _build_general_files_view(self, parent: ctk.CTkFrame):
        T = self.T

        # Folder selection card
        folder_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        folder_card.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        inner = ctk.CTkFrame(folder_card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text="Target Folder", font=_font(12, "bold"), text_color=T["text_dim"]
        ).pack(anchor="w", pady=(0, 5))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        self.folder_entry = ctk.CTkEntry(
            row, placeholder_text="Select or drop a folder to organize...",
            placeholder_text_color=T["text_muted"],
            font=_font(13), height=40, corner_radius=6, border_width=1,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ctk.CTkButton(
            row, text="Browse...", width=110, height=40,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            text_color="#ffffff", command=self._browse_folder,
        )
        self.browse_btn.pack(side="left")

        # Action Toolbar card
        action_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        action_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", padx=12, pady=10)

        self.scan_btn = ctk.CTkButton(
            action_inner, text="Scan Files", width=105, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._scan_general, state="disabled",
        )
        self.scan_btn.pack(side="left", padx=(0, 8))

        self.sort_btn = ctk.CTkButton(
            action_inner, text="Sort Files", width=105, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._sort_general, state="disabled",
        )
        self.sort_btn.pack(side="left", padx=(0, 8))

        self.undo_btn = ctk.CTkButton(
            action_inner, text="Undo Last", width=95, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._undo_general, state="disabled",
        )
        self.undo_btn.pack(side="left", padx=(0, 10))

        ctk.CTkFrame(action_inner, width=1, height=24, fg_color=T["border"]).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            action_inner, text="All", width=48, height=36,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text_dim"], border_width=1, border_color=T["border"],
            command=lambda: self._toggle_all_general(True),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            action_inner, text="None", width=52, height=36,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text_dim"], border_width=1, border_color=T["border"],
            command=lambda: self._toggle_all_general(False),
        ).pack(side="left", padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_general_table())
        self.search_entry = ctk.CTkEntry(
            action_inner, textvariable=self.search_var,
            placeholder_text="Filter files...", placeholder_text_color=T["text_muted"],
            font=_font(12), height=36, width=180,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
            corner_radius=6, border_width=1,
        )
        self.search_entry.pack(side="right")

        self.count_label = ctk.CTkLabel(
            action_inner, text="", font=_font(12, "bold"), text_color=T["accent"],
        )
        self.count_label.pack(side="right", padx=10)

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            parent, fg_color=T["card"], progress_color=T["accent"],
            height=3, corner_radius=2,
        )
        self.progress.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))
        self.progress.set(0)

        # File Table Card
        table_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                  border_width=1, border_color=T["border"])
        table_card.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 6))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(table_card, fg_color=T["card_alt"], corner_radius=6, height=36)
        hdr.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        hdr.pack_propagate(False)

        for text, w in FILE_TABLE_COLS:
            ctk.CTkLabel(
                hdr, text=text, width=w, font=_font(12, "bold"),
                text_color=T["text"], anchor="w",
            ).pack(side="left", padx=4)

        self.table_body = ctk.CTkScrollableFrame(
            table_card, fg_color=T["chart_bg"],
            scrollbar_button_color=T["scrollbar"],
            scrollbar_button_hover_color=T["scrollbar_hover"],
        )
        self.table_body.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))

        ctk.CTkLabel(
            self.table_body,
            text='Select a folder above and click "Scan Files" to preview.',
            font=_font(14), text_color=T["text_dim"],
        ).pack(pady=80)

        # General Pagination Bar (Row 2 in table_card)
        self.gen_pag_bar = ctk.CTkFrame(table_card, fg_color=T["card_alt"], corner_radius=6, height=36)
        self.gen_pag_bar.grid(row=2, column=0, sticky="ew", padx=2, pady=2)
        self.gen_pag_bar.pack_propagate(False)

        self.gen_btn_first = ctk.CTkButton(
            self.gen_pag_bar, text="⏮ First", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._gen_page_first,
        )
        self.gen_btn_first.pack(side="left", padx=(6, 2), pady=5)

        self.gen_btn_prev = ctk.CTkButton(
            self.gen_pag_bar, text="◀ Prev", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._gen_page_prev,
        )
        self.gen_btn_prev.pack(side="left", padx=2, pady=5)

        self.gen_page_label = ctk.CTkLabel(
            self.gen_pag_bar, text="Page 1 of 1 (0 files)", font=_font(11, "bold"), text_color=T["text"],
        )
        self.gen_page_label.pack(side="left", padx=10, pady=5)

        self.gen_size_menu = ctk.CTkOptionMenu(
            self.gen_pag_bar, values=["50", "100", "250", "500"], width=72, height=26, font=_font(11),
            fg_color=T["card"], button_color=T["btn_primary"], button_hover_color=T["btn_primary_hover"],
            dropdown_fg_color=T["card"], command=self._gen_change_page_size,
        )
        self.gen_size_menu.set(str(self.general_page_size))
        self.gen_size_menu.pack(side="right", padx=(2, 6), pady=5)

        ctk.CTkLabel(self.gen_pag_bar, text="Per page:", font=_font(11), text_color=T["text_dim"]).pack(side="right", padx=2, pady=5)

        self.gen_btn_last = ctk.CTkButton(
            self.gen_pag_bar, text="Last ⏭", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._gen_page_last,
        )
        self.gen_btn_last.pack(side="right", padx=2, pady=5)

        self.gen_btn_next = ctk.CTkButton(
            self.gen_pag_bar, text="Next ▶", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._gen_page_next,
        )
        self.gen_btn_next.pack(side="right", padx=2, pady=5)

        self.gen_btn_go = ctk.CTkButton(
            self.gen_pag_bar, text="Go", width=34, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._gen_page_jump,
        )
        self.gen_btn_go.pack(side="right", padx=(2, 6), pady=5)

        self.gen_page_entry = ctk.CTkEntry(self.gen_pag_bar, width=42, height=26, font=_font(11), justify="center")
        self.gen_page_entry.insert(0, "1")
        self.gen_page_entry.pack(side="right", padx=2, pady=5)
        self.gen_page_entry.bind("<Return>", lambda _: self._gen_page_jump())

        ctk.CTkLabel(self.gen_pag_bar, text="Go:", font=_font(11), text_color=T["text_dim"]).pack(side="right", padx=2, pady=5)

        # Status Bar
        status_bar = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=6,
                                  height=28, border_width=1, border_color=T["border"])
        status_bar.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 10))
        status_bar.pack_propagate(False)

        self.status = ctk.CTkLabel(
            status_bar, text="Ready", font=_font(12), text_color=T["text_dim"], anchor="w",
        )
        self.status.pack(side="left", padx=12)

        self.dup_label = ctk.CTkLabel(
            status_bar, text="", font=_font(12, "bold"), text_color=T["warning"], anchor="e",
        )
        self.dup_label.pack(side="right", padx=12)

    # ═══════════════════════════════════════════════════════════════════════
    #  VIEW 2: MEDIA SORTER (TV & MOVIES)
    # ═══════════════════════════════════════════════════════════════════════
    def _build_media_view(self, parent: ctk.CTkFrame):
        T = self.T

        # Folder selection card
        folder_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        folder_card.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        inner = ctk.CTkFrame(folder_card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text="Target Media Folder (Movies / TV Downloads)",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", pady=(0, 5))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        self.media_folder_entry = ctk.CTkEntry(
            row, placeholder_text="Select folder containing movies or TV episodes...",
            placeholder_text_color=T["text_muted"],
            font=_font(13), height=40, corner_radius=6, border_width=1,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
        )
        self.media_folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.media_browse_btn = ctk.CTkButton(
            row, text="Browse...", width=110, height=40,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            text_color="#ffffff", command=self._browse_media_folder,
        )
        self.media_browse_btn.pack(side="left")

        # Media Action Toolbar Card
        action_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        action_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", padx=12, pady=10)

        self.media_scan_btn = ctk.CTkButton(
            action_inner, text="Scan Media", width=105, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._scan_media, state="disabled",
        )
        self.media_scan_btn.pack(side="left", padx=(0, 8))

        self.media_sort_btn = ctk.CTkButton(
            action_inner, text="Organize & Rename", width=145, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._sort_media, state="disabled",
        )
        self.media_sort_btn.pack(side="left", padx=(0, 8))

        self.media_undo_btn = ctk.CTkButton(
            action_inner, text="Undo Last", width=95, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._undo_media, state="disabled",
        )
        self.media_undo_btn.pack(side="left", padx=(0, 10))

        ctk.CTkFrame(action_inner, width=1, height=24, fg_color=T["border"]).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            action_inner, text="All", width=48, height=36,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text_dim"], border_width=1, border_color=T["border"],
            command=lambda: self._toggle_all_media(True),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            action_inner, text="None", width=52, height=36,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text_dim"], border_width=1, border_color=T["border"],
            command=lambda: self._toggle_all_media(False),
        ).pack(side="left", padx=(0, 10))

        self.media_search_var = tk.StringVar()
        self.media_search_var.trace_add("write", lambda *_: self._filter_media_table())
        self.media_search_entry = ctk.CTkEntry(
            action_inner, textvariable=self.media_search_var,
            placeholder_text="Filter media...", placeholder_text_color=T["text_muted"],
            font=_font(12), height=36, width=180,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
            corner_radius=6, border_width=1,
        )
        self.media_search_entry.pack(side="right")

        self.media_count_label = ctk.CTkLabel(
            action_inner, text="", font=_font(12, "bold"), text_color=T["accent"],
        )
        self.media_count_label.pack(side="right", padx=10)

        # Progress bar
        self.media_progress = ctk.CTkProgressBar(
            parent, fg_color=T["card"], progress_color=T["accent"],
            height=3, corner_radius=2,
        )
        self.media_progress.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))
        self.media_progress.set(0)

        # Media Table Card
        media_table_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                        border_width=1, border_color=T["border"])
        media_table_card.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 6))
        media_table_card.grid_rowconfigure(1, weight=1)
        media_table_card.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(media_table_card, fg_color=T["card_alt"], corner_radius=6, height=36)
        hdr.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        hdr.pack_propagate(False)

        for text, w in MEDIA_TABLE_COLS:
            ctk.CTkLabel(
                hdr, text=text, width=w, font=_font(12, "bold"),
                text_color=T["text"], anchor="w",
            ).pack(side="left", padx=4)

        self.media_table_body = ctk.CTkScrollableFrame(
            media_table_card, fg_color=T["chart_bg"],
            scrollbar_button_color=T["scrollbar"],
            scrollbar_button_hover_color=T["scrollbar_hover"],
        )
        self.media_table_body.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))

        ctk.CTkLabel(
            self.media_table_body,
            text='Select a media folder above and click "Scan Media" to preview TV shows & movies.',
            font=_font(14), text_color=T["text_dim"],
        ).pack(pady=80)

        # Media Pagination Bar (Row 2 in media_table_card)
        self.media_pag_bar = ctk.CTkFrame(media_table_card, fg_color=T["card_alt"], corner_radius=6, height=36)
        self.media_pag_bar.grid(row=2, column=0, sticky="ew", padx=2, pady=2)
        self.media_pag_bar.pack_propagate(False)

        self.med_btn_first = ctk.CTkButton(
            self.media_pag_bar, text="⏮ First", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._med_page_first,
        )
        self.med_btn_first.pack(side="left", padx=(6, 2), pady=5)

        self.med_btn_prev = ctk.CTkButton(
            self.media_pag_bar, text="◀ Prev", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._med_page_prev,
        )
        self.med_btn_prev.pack(side="left", padx=2, pady=5)

        self.med_page_label = ctk.CTkLabel(
            self.media_pag_bar, text="Page 1 of 1 (0 files)", font=_font(11, "bold"), text_color=T["text"],
        )
        self.med_page_label.pack(side="left", padx=10, pady=5)

        self.med_size_menu = ctk.CTkOptionMenu(
            self.media_pag_bar, values=["50", "100", "250", "500"], width=72, height=26, font=_font(11),
            fg_color=T["card"], button_color=T["btn_primary"], button_hover_color=T["btn_primary_hover"],
            dropdown_fg_color=T["card"], command=self._med_change_page_size,
        )
        self.med_size_menu.set(str(self.media_page_size))
        self.med_size_menu.pack(side="right", padx=(2, 6), pady=5)

        ctk.CTkLabel(self.media_pag_bar, text="Per page:", font=_font(11), text_color=T["text_dim"]).pack(side="right", padx=2, pady=5)

        self.med_btn_last = ctk.CTkButton(
            self.media_pag_bar, text="Last ⏭", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._med_page_last,
        )
        self.med_btn_last.pack(side="right", padx=2, pady=5)

        self.med_btn_next = ctk.CTkButton(
            self.media_pag_bar, text="Next ▶", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._med_page_next,
        )
        self.med_btn_next.pack(side="right", padx=2, pady=5)

        self.med_btn_go = ctk.CTkButton(
            self.media_pag_bar, text="Go", width=34, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._med_page_jump,
        )
        self.med_btn_go.pack(side="right", padx=(2, 6), pady=5)

        self.med_page_entry = ctk.CTkEntry(self.media_pag_bar, width=42, height=26, font=_font(11), justify="center")
        self.med_page_entry.insert(0, "1")
        self.med_page_entry.pack(side="right", padx=2, pady=5)
        self.med_page_entry.bind("<Return>", lambda _: self._med_page_jump())

        ctk.CTkLabel(self.media_pag_bar, text="Go:", font=_font(11), text_color=T["text_dim"]).pack(side="right", padx=2, pady=5)

        # Media Status Bar
        media_status_bar = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=6,
                                        height=28, border_width=1, border_color=T["border"])
        media_status_bar.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 10))
        media_status_bar.pack_propagate(False)

        self.media_status = ctk.CTkLabel(
            media_status_bar, text="Ready", font=_font(12), text_color=T["text_dim"], anchor="w",
        )
        self.media_status.pack(side="left", padx=12)

        self.media_info_label = ctk.CTkLabel(
            media_status_bar, text="", font=_font(12, "bold"), text_color=T["accent"], anchor="e",
        )
        self.media_info_label.pack(side="right", padx=12)

    # ═══════════════════════════════════════════════════════════════════════
    #  VIEW 3: BULK FILE RENAMER
    # ═══════════════════════════════════════════════════════════════════════
    def _build_renamer_view(self, parent: ctk.CTkFrame):
        T = self.T

        # Folder selection card (Row 0)
        folder_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        folder_card.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        inner = ctk.CTkFrame(folder_card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text="Target Folder to Rename Files",
            font=_font(12, "bold"), text_color=T["text_dim"],
        ).pack(anchor="w", pady=(0, 5))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        self.renamer_folder_entry = ctk.CTkEntry(
            row, placeholder_text="Select folder containing files to rename...",
            placeholder_text_color=T["text_muted"],
            font=_font(13), height=40, corner_radius=6, border_width=1,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
        )
        self.renamer_folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.renamer_browse_btn = ctk.CTkButton(
            row, text="Browse...", width=110, height=40,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            text_color="#ffffff", command=self._browse_renamer_folder,
        )
        self.renamer_browse_btn.pack(side="left")

        # Renaming Rules Configuration Card (Row 1)
        rules_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                  border_width=1, border_color=T["border"])
        rules_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        r_inner = ctk.CTkFrame(rules_card, fg_color="transparent")
        r_inner.pack(fill="x", padx=12, pady=10)

        # Line 1: Find & Replace + Options
        line1 = ctk.CTkFrame(r_inner, fg_color="transparent")
        line1.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(line1, text="Find:", font=_font(12, "bold"), text_color=T["text_dim"]).pack(side="left", padx=(0, 4))
        self.renamer_find_entry = ctk.CTkEntry(
            line1, placeholder_text="Text to find...", font=_font(12), height=32, width=170,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"], corner_radius=6,
        )
        self.renamer_find_entry.pack(side="left", padx=(0, 10))
        self.renamer_find_entry.bind("<KeyRelease>", lambda _: self._on_renamer_rule_change())

        ctk.CTkLabel(line1, text="Replace:", font=_font(12, "bold"), text_color=T["text_dim"]).pack(side="left", padx=(0, 4))
        self.renamer_replace_entry = ctk.CTkEntry(
            line1, placeholder_text="Replace with...", font=_font(12), height=32, width=170,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"], corner_radius=6,
        )
        self.renamer_replace_entry.pack(side="left", padx=(0, 12))
        self.renamer_replace_entry.bind("<KeyRelease>", lambda _: self._on_renamer_rule_change())

        self.renamer_match_case_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            line1, text="Match Case", variable=self.renamer_match_case_var,
            font=_font(12), text_color=T["text"], fg_color=T["btn_primary"],
            hover_color=T["btn_primary_hover"], border_color=T["border"],
            checkmark_color="#ffffff", command=self._on_renamer_rule_change,
        ).pack(side="left", padx=(0, 8))

        self.renamer_regex_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            line1, text="Regex", variable=self.renamer_regex_var,
            font=_font(12), text_color=T["text"], fg_color=T["btn_primary"],
            hover_color=T["btn_primary_hover"], border_color=T["border"],
            checkmark_color="#ffffff", command=self._on_renamer_rule_change,
        ).pack(side="left")

        # Line 2: Prefix & Suffix
        line2 = ctk.CTkFrame(r_inner, fg_color="transparent")
        line2.pack(fill="x")

        ctk.CTkLabel(line2, text="Prefix:", font=_font(12, "bold"), text_color=T["text_dim"]).pack(side="left", padx=(0, 4))
        self.renamer_prefix_entry = ctk.CTkEntry(
            line2, placeholder_text="Add prefix (e.g. 2024_)...", font=_font(12), height=32, width=220,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"], corner_radius=6,
        )
        self.renamer_prefix_entry.pack(side="left", padx=(0, 16))
        self.renamer_prefix_entry.bind("<KeyRelease>", lambda _: self._on_renamer_rule_change())

        ctk.CTkLabel(line2, text="Suffix:", font=_font(12, "bold"), text_color=T["text_dim"]).pack(side="left", padx=(0, 4))
        self.renamer_suffix_entry = ctk.CTkEntry(
            line2, placeholder_text="Add suffix (e.g. _draft)...", font=_font(12), height=32, width=220,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"], corner_radius=6,
        )
        self.renamer_suffix_entry.pack(side="left", padx=(0, 10))
        self.renamer_suffix_entry.bind("<KeyRelease>", lambda _: self._on_renamer_rule_change())

        # Action Toolbar Card (Row 2)
        action_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        action_card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 6))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", padx=12, pady=10)

        self.renamer_scan_btn = ctk.CTkButton(
            action_inner, text="Scan Files", width=105, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._scan_renamer, state="disabled",
        )
        self.renamer_scan_btn.pack(side="left", padx=(0, 8))

        self.renamer_rename_btn = ctk.CTkButton(
            action_inner, text="Rename Files", width=130, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._execute_rename, state="disabled",
        )
        self.renamer_rename_btn.pack(side="left", padx=(0, 8))

        self.renamer_undo_btn = ctk.CTkButton(
            action_inner, text="Undo Last", width=95, height=36,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            border_width=1, border_color=T["border"], text_color=T["text_muted"],
            command=self._undo_renamer, state="disabled",
        )
        self.renamer_undo_btn.pack(side="left", padx=(0, 10))

        ctk.CTkFrame(action_inner, width=1, height=24, fg_color=T["border"]).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            action_inner, text="All", width=48, height=36,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text_dim"], border_width=1, border_color=T["border"],
            command=lambda: self._toggle_all_renamer(True),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            action_inner, text="None", width=52, height=36,
            font=_font(12, "bold"), corner_radius=6,
            fg_color=T["card_alt"], hover_color=T["border"],
            text_color=T["text_dim"], border_width=1, border_color=T["border"],
            command=lambda: self._toggle_all_renamer(False),
        ).pack(side="left", padx=(0, 10))

        self.renamer_search_var = tk.StringVar()
        self.renamer_search_var.trace_add("write", lambda *_: self._filter_renamer_table())
        self.renamer_search_entry = ctk.CTkEntry(
            action_inner, textvariable=self.renamer_search_var,
            placeholder_text="Filter files...", placeholder_text_color=T["text_muted"],
            font=_font(12), height=36, width=180,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
            corner_radius=6, border_width=1,
        )
        self.renamer_search_entry.pack(side="right")

        self.renamer_count_label = ctk.CTkLabel(
            action_inner, text="", font=_font(12, "bold"), text_color=T["accent"],
        )
        self.renamer_count_label.pack(side="right", padx=10)

        # Progress bar (Row 3)
        self.renamer_progress = ctk.CTkProgressBar(
            parent, fg_color=T["card"], progress_color=T["accent"],
            height=3, corner_radius=2,
        )
        self.renamer_progress.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 6))
        self.renamer_progress.set(0)

        # Renamer Table Card (Row 4)
        renamer_table_card = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=8,
                                          border_width=1, border_color=T["border"])
        renamer_table_card.grid(row=4, column=0, sticky="nsew", padx=16, pady=(0, 6))
        renamer_table_card.grid_rowconfigure(1, weight=1)
        renamer_table_card.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(renamer_table_card, fg_color=T["card_alt"], corner_radius=6, height=36)
        hdr.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        hdr.pack_propagate(False)

        for text, w in RENAME_TABLE_COLS:
            ctk.CTkLabel(
                hdr, text=text, width=w, font=_font(12, "bold"),
                text_color=T["text"], anchor="w",
            ).pack(side="left", padx=4)

        self.renamer_table_body = ctk.CTkScrollableFrame(
            renamer_table_card, fg_color=T["chart_bg"],
            scrollbar_button_color=T["scrollbar"],
            scrollbar_button_hover_color=T["scrollbar_hover"],
        )
        self.renamer_table_body.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))

        ctk.CTkLabel(
            self.renamer_table_body,
            text='Select a folder above and click "Scan Files" to preview.',
            font=_font(14), text_color=T["text_dim"],
        ).pack(pady=80)

        # Renamer Pagination Bar (Row 2 in renamer_table_card)
        self.renamer_pag_bar = ctk.CTkFrame(renamer_table_card, fg_color=T["card_alt"], corner_radius=6, height=36)
        self.renamer_pag_bar.grid(row=2, column=0, sticky="ew", padx=2, pady=2)
        self.renamer_pag_bar.pack_propagate(False)

        self.ren_btn_first = ctk.CTkButton(
            self.renamer_pag_bar, text="⏮ First", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._ren_page_first,
        )
        self.ren_btn_first.pack(side="left", padx=(6, 2), pady=5)

        self.ren_btn_prev = ctk.CTkButton(
            self.renamer_pag_bar, text="◀ Prev", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._ren_page_prev,
        )
        self.ren_btn_prev.pack(side="left", padx=2, pady=5)

        self.ren_page_label = ctk.CTkLabel(
            self.renamer_pag_bar, text="Page 1 of 1 (0 files)", font=_font(11, "bold"), text_color=T["text"],
        )
        self.ren_page_label.pack(side="left", padx=10, pady=5)

        self.ren_size_menu = ctk.CTkOptionMenu(
            self.renamer_pag_bar, values=["50", "100", "250", "500"], width=72, height=26, font=_font(11),
            fg_color=T["card"], button_color=T["btn_primary"], button_hover_color=T["btn_primary_hover"],
            dropdown_fg_color=T["card"], command=self._ren_change_page_size,
        )
        self.ren_size_menu.set(str(self.renamer_page_size))
        self.ren_size_menu.pack(side="right", padx=(2, 6), pady=5)

        ctk.CTkLabel(self.renamer_pag_bar, text="Per page:", font=_font(11), text_color=T["text_dim"]).pack(side="right", padx=2, pady=5)

        self.ren_btn_last = ctk.CTkButton(
            self.renamer_pag_bar, text="Last ⏭", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._ren_page_last,
        )
        self.ren_btn_last.pack(side="right", padx=2, pady=5)

        self.ren_btn_next = ctk.CTkButton(
            self.renamer_pag_bar, text="Next ▶", width=55, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._ren_page_next,
        )
        self.ren_btn_next.pack(side="right", padx=2, pady=5)

        self.ren_btn_go = ctk.CTkButton(
            self.renamer_pag_bar, text="Go", width=34, height=26, font=_font(11),
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"], command=self._ren_page_jump,
        )
        self.ren_btn_go.pack(side="right", padx=(2, 6), pady=5)

        self.ren_page_entry = ctk.CTkEntry(self.renamer_pag_bar, width=42, height=26, font=_font(11), justify="center")
        self.ren_page_entry.insert(0, "1")
        self.ren_page_entry.pack(side="right", padx=2, pady=5)
        self.ren_page_entry.bind("<Return>", lambda _: self._ren_page_jump())

        ctk.CTkLabel(self.renamer_pag_bar, text="Go:", font=_font(11), text_color=T["text_dim"]).pack(side="right", padx=2, pady=5)

        # Renamer Status Bar (Row 5)
        renamer_status_bar = ctk.CTkFrame(parent, fg_color=T["card"], corner_radius=6,
                                          height=28, border_width=1, border_color=T["border"])
        renamer_status_bar.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 10))
        renamer_status_bar.pack_propagate(False)

        self.renamer_status = ctk.CTkLabel(
            renamer_status_bar, text="Ready", font=_font(12), text_color=T["text_dim"], anchor="w",
        )
        self.renamer_status.pack(side="left", padx=12)

        self.renamer_info_label = ctk.CTkLabel(
            renamer_status_bar, text="", font=_font(12, "bold"), text_color=T["accent"], anchor="e",
        )
        self.renamer_info_label.pack(side="right", padx=12)

    # ═══════════════════════════════════════════════════════════════════════
    #  MEDIA SORTER HANDLERS
    # ═══════════════════════════════════════════════════════════════════════
    def _browse_media_folder(self):
        folder = filedialog.askdirectory(title="Select Media Folder (Movies / TV Shows)")
        if folder:
            self.media_folder_entry.delete(0, "end")
            self.media_folder_entry.insert(0, folder)
            self.current_media_folder = folder
            self.settings["last_media_folder"] = folder
            self._set_btn_state(self.media_scan_btn, True, self.T["btn_primary"])
            self._update_media_undo_state()
            self._scan_media()

    def _scan_media(self):
        if hasattr(self, "_media_scanning") and self._media_scanning:
            self.media_status.configure(text="Cancelling scan...")
            self._media_scan_cancel.set()
            return

        if not self.current_media_folder or self._is_busy:
            return

        self._is_busy = True
        self._media_scanning = True
        self._media_scan_cancel.clear()
        self.media_scan_btn.configure(text="✕ Cancel", fg_color=self.T["danger"], hover_color=self.T["danger_hover"], state="normal")
        self._set_btn_state(self.media_sort_btn, False, self.T["card_alt"])
        self.media_status.configure(text="Scanning video files and querying TV & Anime Databases...")
        self.media_progress.set(0)

        def _worker():
            try:
                plan = scan_media_folder(
                    self.current_media_folder,
                    recursive=self.media_rec_var.get(),
                    fetch_tvdb=self.media_tvdb_var.get(),
                    fetch_anime=self.media_anime_var.get(),
                    create_season_folders=self.media_season_var.get(),
                    structure_by_type=self.media_struct_var.get(),
                    progress_cb=lambda c, t: self.after(0, lambda curr=c, tot=t: self._update_media_progress(curr, tot)),
                    cancel_event=self._media_scan_cancel,
                )
                self.after(0, self._scan_media_done, plan, None)
            except Exception as exc:
                self.after(0, self._scan_media_done, [], str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_media_progress(self, current: int, total: int):
        self.media_progress.set(current / max(total, 1))
        self.media_status.configure(text=f"Scanning media ({current:,}/{total:,})...")

    def _scan_media_done(self, plan: list[dict], error: str | None):
        self._is_busy = False
        self._media_scanning = False
        self.media_scan_btn.configure(text="Scan Media", fg_color=self.T["btn_primary"], hover_color=self.T["accent_hover"], state="normal")
        self.media_progress.set(0)

        if error:
            self.media_status.configure(text=f"Scan Error: {error}")
            messagebox.showerror("Scan Failed", error)
            return

        self.current_media_plan = plan
        self.media_filtered_plan = list(plan)
        self.media_page = 1
        self._populate_media_table()
        self._update_media_count()

        anime_count = sum(1 for e in plan if e["type"] == "Anime")
        tv_count = sum(1 for e in plan if e["type"] == "TV Show")
        movie_count = sum(1 for e in plan if e["type"] == "Movie")
        other_count = len(plan) - anime_count - tv_count - movie_count

        summary_parts = []
        if anime_count:
            summary_parts.append(f"{anime_count:,} Anime Episode{'s' if anime_count != 1 else ''}")
        if tv_count:
            summary_parts.append(f"{tv_count:,} TV Episode{'s' if tv_count != 1 else ''}")
        if movie_count:
            summary_parts.append(f"{movie_count:,} Movie{'s' if movie_count != 1 else ''}")
        if other_count:
            summary_parts.append(f"{other_count:,} Video{'s' if other_count != 1 else ''}")

        summary_text = " • ".join(summary_parts) if summary_parts else "No video files found"
        self.media_info_label.configure(text=summary_text)
        self.media_status.configure(text=f"Scan complete — {len(plan):,} files identified")

    def _populate_media_table(self, plan: list[dict] | None = None):
        if plan is not None:
            self.media_filtered_plan = plan

        active = self.media_filtered_plan
        total_items = len(active)
        page_size = self.media_page_size
        total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1

        if self.media_page > total_pages:
            self.media_page = total_pages
        if self.media_page < 1:
            self.media_page = 1

        start_idx = (self.media_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        page_items = active[start_idx:end_idx]

        self._update_med_pag_controls(total_items, total_pages, start_idx, end_idx)

        T = self.T
        for w in self.media_table_body.winfo_children():
            w.destroy()
        self._media_check_vars.clear()

        if not page_items:
            msg = "No video files found." if total_items == 0 else "No items on this page."
            ctk.CTkLabel(
                self.media_table_body,
                text=msg, font=_font(14), text_color=T["text_dim"],
            ).pack(pady=80)
            return

        col_w = {col[0]: col[1] for col in MEDIA_TABLE_COLS}

        for idx, entry in enumerate(page_items):
            bg = T["row_even"] if idx % 2 == 0 else T["row_odd"]
            row = ctk.CTkFrame(self.media_table_body, fg_color=bg, corner_radius=0, height=32)
            row.pack(fill="x")
            row.pack_propagate(False)

            # Checkbox
            var = tk.BooleanVar(value=entry.get("selected", True))
            self._media_check_vars.append(var)
            var.trace_add("write", lambda *_, e=entry, v=var: self._on_media_entry_check(e, v))
            ctk.CTkCheckBox(
                row, text="", variable=var, width=col_w[""],
                fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
                border_color=T["border"], checkmark_color="#ffffff", corner_radius=4,
            ).pack(side="left", padx=4)

            # Original Filename
            ctk.CTkLabel(
                row, text=entry["name"], width=col_w["Original File"],
                font=_font(12), text_color=T["text"], anchor="w",
            ).pack(side="left", padx=4)

            # Type badge
            type_frame = ctk.CTkFrame(row, fg_color="transparent", width=col_w["Type"])
            type_frame.pack(side="left", padx=4)
            type_frame.pack_propagate(False)
            if entry["type"] == "TV Show":
                badge_color = T["badge_tv"]
            elif entry["type"] == "Anime":
                badge_color = T["badge_anime"]
            elif entry["type"] == "Movie":
                badge_color = T["badge_movie"]
            else:
                badge_color = T.get("badge_video", T["card_alt"])
            ctk.CTkLabel(
                type_frame, text=f" {entry['type']} ", font=_font(10, "bold"),
                fg_color=badge_color, corner_radius=4, text_color="#ffffff", height=20,
            ).pack(anchor="w", pady=5)

            # Detected Title
            ctk.CTkLabel(
                row, text=entry["title"], width=col_w["Detected Title"],
                font=_font(12, "bold"), text_color=T["text"], anchor="w",
            ).pack(side="left", padx=4)

            # S / Ep
            ctk.CTkLabel(
                row, text=entry["se_tag"], width=col_w["S / Ep"],
                font=_font(12, "bold"), text_color=T["accent"], anchor="w",
            ).pack(side="left", padx=4)

            # Episode Title (DB)
            ctk.CTkLabel(
                row, text=entry["ep_title"], width=col_w["Episode Title (DB)"],
                font=_font(12), text_color=T["text_dim"], anchor="w",
            ).pack(side="left", padx=4)

            # Destination Path preview
            ctk.CTkLabel(
                row, text=entry["rel_dest"], width=col_w["New Destination Path"],
                font=_font(11), text_color=T["text_dim"], anchor="w",
            ).pack(side="left", padx=4)

            # Status
            ctk.CTkLabel(
                row, text="Pending", width=col_w["Status"],
                font=_font(12), text_color=T["text_dim"], anchor="w",
            ).pack(side="left", padx=4)

    def _update_med_pag_controls(self, total_items: int, total_pages: int, start_idx: int, end_idx: int):
        T = self.T
        can_prev = self.media_page > 1
        can_next = self.media_page < total_pages

        self._set_btn_state(self.med_btn_first, can_prev, T["btn_primary"])
        self._set_btn_state(self.med_btn_prev, can_prev, T["btn_primary"])
        self._set_btn_state(self.med_btn_next, can_next, T["btn_primary"])
        self._set_btn_state(self.med_btn_last, can_next, T["btn_primary"])

        if total_items == 0:
            self.med_page_label.configure(text="Page 0 of 0 (0 files)")
        else:
            self.med_page_label.configure(
                text=f"Page {self.media_page} of {total_pages} (Showing {start_idx+1:,}–{end_idx:,} of {total_items:,} files)"
            )
        self.med_page_entry.delete(0, "end")
        self.med_page_entry.insert(0, str(self.media_page))

    def _med_page_first(self):
        self.media_page = 1
        self._populate_media_table()

    def _med_page_prev(self):
        if self.media_page > 1:
            self.media_page -= 1
            self._populate_media_table()

    def _med_page_next(self):
        total_pages = max(1, math.ceil(len(self.media_filtered_plan) / self.media_page_size))
        if self.media_page < total_pages:
            self.media_page += 1
            self._populate_media_table()

    def _med_page_last(self):
        total_pages = max(1, math.ceil(len(self.media_filtered_plan) / self.media_page_size))
        self.media_page = total_pages
        self._populate_media_table()

    def _med_page_jump(self):
        val = self.med_page_entry.get().strip()
        if not val.isdigit():
            return
        page = int(val)
        total_pages = max(1, math.ceil(len(self.media_filtered_plan) / self.media_page_size))
        self.media_page = max(1, min(page, total_pages))
        self._populate_media_table()

    def _med_change_page_size(self, val: str):
        try:
            self.media_page_size = int(val)
        except ValueError:
            self.media_page_size = 100
        self.media_page = 1
        self._populate_media_table()

    def _filter_media_table(self):
        query = self.media_search_var.get().lower().strip()
        if not query:
            self.media_filtered_plan = list(self.current_media_plan)
        else:
            self.media_filtered_plan = [
                e for e in self.current_media_plan
                if query in e["name"].lower() or query in e["title"].lower() or query in e["ep_title"].lower() or query in e["type"].lower()
            ]
        self.media_page = 1
        self._populate_media_table()

    def _on_media_entry_check(self, entry: dict, var: tk.BooleanVar):
        entry["selected"] = var.get()
        self._update_media_count()

    def _toggle_all_media(self, state: bool):
        target_list = self.media_filtered_plan if self.media_filtered_plan else self.current_media_plan
        for e in target_list:
            e["selected"] = state
        for var in self._media_check_vars:
            var.set(state)
        self._update_media_count()

    def _update_media_count(self):
        sel = sum(1 for e in self.current_media_plan if e.get("selected", True))
        total = len(self.current_media_plan)
        self.media_count_label.configure(text=f"{sel:,}/{total:,} media selected")
        self._set_btn_state(self.media_sort_btn, sel > 0, self.T["success"])

    def _sort_media(self):
        if self._is_busy or not self.current_media_plan:
            return
        sel = [e for e in self.current_media_plan if e.get("selected", True)]
        n = len(sel)
        if n == 0:
            return

        if not messagebox.askyesno(
            "Confirm Media Organization",
            f"Organize and rename {n} media file{'s' if n != 1 else ''} into structured folders?\n\n"
            f"You can undo this operation at any time.",
        ):
            return

        self._is_busy = True
        self._set_btn_state(self.media_scan_btn, False, self.T["card_alt"])
        self._set_btn_state(self.media_sort_btn, False, self.T["card_alt"])
        self.media_status.configure(text="Organizing and renaming media files...")

        def _worker():
            try:
                execute_media_sort(
                    self.current_media_plan, self.current_media_folder,
                    progress_cb=lambda c, t: self.after(0, self.media_progress.set, c / max(t, 1)),
                )
                self.after(0, self._sort_media_done, None)
            except Exception as exc:
                self.after(0, self._sort_media_done, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _sort_media_done(self, error: str | None):
        self._is_busy = False
        self._media_scanning = False
        self.media_scan_btn.configure(text="Scan Media", fg_color=self.T["btn_primary"], hover_color=self.T["accent_hover"], state="normal")
        self.media_progress.set(0)

        if error:
            self.media_status.configure(text=f"Error: {error}")
            messagebox.showerror("Organization Failed", error)
        else:
            sel = sum(1 for e in self.current_media_plan if e.get("selected", True))
            self.media_status.configure(text=f"Successfully organized {sel} media files!")
            messagebox.showinfo("Done", f"Successfully organized and renamed {sel} media files!")
            self._update_media_undo_state()
            self._scan_media()

    def _undo_media(self):
        if self._is_busy or not self.current_media_folder:
            return
        if not messagebox.askyesno("Confirm Undo", "Reverse the last media sort and restore files?"):
            return

        self._is_busy = True
        self.media_status.configure(text="Restoring media files...")

        def _worker():
            try:
                count = undo_media_sort(
                    self.current_media_folder,
                    progress_cb=lambda c, t: self.after(0, self.media_progress.set, c / max(t, 1)),
                )
                self.after(0, self._undo_media_done, count, None)
            except Exception as exc:
                self.after(0, self._undo_media_done, 0, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _undo_media_done(self, count: int, error: str | None):
        self._is_busy = False

        # Pagination & Large Drive Virtualization State
        self.general_page = 1
        self.general_page_size = 100
        self.general_filtered_plan: list[dict] = []
        self._general_scanning = False
        self._general_scan_cancel = threading.Event()

        self.media_page = 1
        self.media_page_size = 100
        self.media_filtered_plan: list[dict] = []
        self._media_scanning = False
        self._media_scan_cancel = threading.Event()

        self.renamer_page = 1
        self.renamer_page_size = 100
        self.renamer_filtered_plan: list[dict] = []
        self._renamer_scanning = False
        self._renamer_scan_cancel = threading.Event()
        self._renamer_debounce_id = None
        self.media_progress.set(0)
        self._update_media_undo_state()

        if error:
            self.media_status.configure(text=f"Undo error: {error}")
            messagebox.showerror("Undo Failed", error)
        else:
            self.media_status.configure(text=f"Restored {count} media files to original paths")
            messagebox.showinfo("Undo Complete", f"Restored {count} media files.")
            self._scan_media()

    def _update_media_undo_state(self):
        has_history = False
        if self.current_media_folder:
            hp = Path(self.current_media_folder) / MEDIA_HISTORY_FILENAME
            has_history = hp.exists()
        self._set_btn_state(self.media_undo_btn, has_history, self.T["card_alt"])
        if has_history:
            self.media_undo_btn.configure(
                border_width=1, border_color=self.T["accent"], text_color=self.T["text"]
            )

    # ═══════════════════════════════════════════════════════════════════════
    #  BULK RENAMER HANDLERS
    # ═══════════════════════════════════════════════════════════════════════
    def _browse_renamer_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Rename Files")
        if folder:
            self.renamer_folder_entry.delete(0, "end")
            self.renamer_folder_entry.insert(0, folder)
            self.current_renamer_folder = folder
            self.settings["last_renamer_folder"] = folder
            self._set_btn_state(self.renamer_scan_btn, True, self.T["btn_primary"])
            self._update_renamer_undo_state()
            self._scan_renamer()

    def _get_active_renamer_rules(self) -> dict:
        try:
            num_start = int(self.renamer_start_entry.get() or "1")
        except ValueError:
            num_start = 1
        try:
            num_pad = int(self.renamer_pad_entry.get() or "2")
        except ValueError:
            num_pad = 2

        return {
            "find": self.renamer_find_entry.get(),
            "replace": self.renamer_replace_entry.get(),
            "match_case": self.renamer_match_case_var.get(),
            "use_regex": self.renamer_regex_var.get(),
            "prefix": self.renamer_prefix_entry.get(),
            "suffix": self.renamer_suffix_entry.get(),
            "case_mode": self.renamer_case_var.get(),
            "space_mode": self.renamer_space_var.get(),
            "lowercase_ext": self.renamer_lower_ext_var.get(),
            "add_numbering": self.renamer_num_var.get(),
            "num_pos": self.renamer_num_pos_var.get(),
            "num_start": num_start,
            "num_pad": num_pad,
        }

    def _scan_renamer(self):
        if hasattr(self, "_renamer_scanning") and self._renamer_scanning:
            self.renamer_status.configure(text="Cancelling scan...")
            self._renamer_scan_cancel.set()
            return

        if not self.current_renamer_folder or self._is_busy:
            return

        self._is_busy = True
        self._renamer_scanning = True
        self._renamer_scan_cancel.clear()
        self.renamer_scan_btn.configure(text="✕ Cancel", fg_color=self.T["danger"], hover_color=self.T["danger_hover"], state="normal")
        self._set_btn_state(self.renamer_apply_btn, False, self.T["card_alt"])
        self.renamer_status.configure(text="Scanning folder for files...")
        self.renamer_progress.set(0)

        rules = self._get_active_renamer_rules()

        def _worker():
            try:
                plan = scan_renamer_folder(
                    self.current_renamer_folder,
                    recursive=self.renamer_rec_var.get(),
                    rules=rules,
                    progress_cb=lambda count: self.after(0, lambda c=count: self.renamer_status.configure(text=f"Scanning... {c:,} files found")),
                    cancel_event=self._renamer_scan_cancel,
                )
                self.after(0, self._scan_renamer_done, plan, None)
            except Exception as exc:
                self.after(0, self._scan_renamer_done, [], str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _scan_renamer_done(self, plan: list[dict], error: str | None):
        self._is_busy = False
        self._renamer_scanning = False
        self.renamer_scan_btn.configure(text="Scan Files", fg_color=self.T["btn_primary"], hover_color=self.T["accent_hover"], state="normal")
        self.renamer_progress.set(0)

        if error:
            self.renamer_status.configure(text=f"Scan error: {error}")
            messagebox.showerror("Scan Failed", error)
            return

        self.current_renamer_plan = plan
        self.renamer_filtered_plan = list(plan)
        self.renamer_page = 1
        self._populate_renamer_table()
        self._update_renamer_count()
        self._update_renamer_undo_state()
        n = len(self.current_renamer_plan)
        self.renamer_status.configure(text=f"Scan complete — {n:,} files identified")

    def _on_renamer_rule_change(self, *args):
        if not self.current_renamer_plan:
            return
        if getattr(self, "_renamer_debounce_id", None):
            self.after_cancel(self._renamer_debounce_id)
        self._renamer_debounce_id = self.after(100, self._apply_renamer_rules_deferred)

    def _apply_renamer_rules_deferred(self):
        self._renamer_debounce_id = None
        if not self.current_renamer_plan:
            return
        rules = self._get_active_renamer_rules()
        seen_new_names: dict[str, int] = defaultdict(int)

        for idx, entry in enumerate(self.current_renamer_plan):
            orig_name = entry["name"]
            new_name = apply_rename_rules(orig_name, idx, rules)
            entry["new_name"] = new_name
            entry["changed"] = (new_name != orig_name)

            dest_path = Path(entry["src"]).parent / new_name
            entry["dest"] = str(dest_path)

            seen_new_names[str(dest_path).lower()] += 1
            if seen_new_names[str(dest_path).lower()] > 1:
                entry["status"] = "Duplicate Name"
            elif dest_path.exists() and str(dest_path) != entry["src"]:
                entry["status"] = "Target Exists"
            else:
                entry["status"] = "Pending"

        self._filter_renamer_table()
        self._update_renamer_count()

    def _populate_renamer_table(self, plan: list[dict] | None = None):
        if plan is not None:
            self.renamer_filtered_plan = plan

        active = self.renamer_filtered_plan
        total_items = len(active)
        page_size = self.renamer_page_size
        total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1

        if self.renamer_page > total_pages:
            self.renamer_page = total_pages
        if self.renamer_page < 1:
            self.renamer_page = 1

        start_idx = (self.renamer_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        page_items = active[start_idx:end_idx]

        self._update_ren_pag_controls(total_items, total_pages, start_idx, end_idx)

        T = self.T
        for w in self.renamer_table_body.winfo_children():
            w.destroy()
        self._renamer_check_vars.clear()

        if not page_items:
            msg = "Select a folder above and click 'Scan Files' to preview." if total_items == 0 else "No items on this page."
            ctk.CTkLabel(
                self.renamer_table_body,
                text=msg, font=_font(14), text_color=T["text_dim"],
            ).pack(pady=80)
            return

        col_w = {col[0]: col[1] for col in RENAME_TABLE_COLS}

        for idx, entry in enumerate(page_items):
            bg = T["row_even"] if idx % 2 == 0 else T["row_odd"]
            row = ctk.CTkFrame(self.renamer_table_body, fg_color=bg, corner_radius=0, height=32)
            row.pack(fill="x")
            row.pack_propagate(False)

            # Checkbox
            var = tk.BooleanVar(value=entry.get("selected", True))
            self._renamer_check_vars.append(var)
            var.trace_add("write", lambda *_, e=entry, v=var: self._on_renamer_entry_check(e, v))
            ctk.CTkCheckBox(
                row, text="", variable=var, width=col_w[""],
                fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
                border_color=T["border"], checkmark_color="#ffffff", corner_radius=4,
            ).pack(side="left", padx=4)

            # Original Filename
            ctk.CTkLabel(
                row, text=entry["name"], width=col_w["Original File"],
                font=_font(12), text_color=T["text"], anchor="w",
            ).pack(side="left", padx=4)

            # Size
            ctk.CTkLabel(
                row, text=human_size(entry.get("size", 0)), width=col_w["Size"],
                font=_font(12), text_color=T["text_dim"], anchor="w",
            ).pack(side="left", padx=4)

            # New Filename Preview
            preview_color = T["accent"] if entry["changed"] else T["text_muted"]
            ctk.CTkLabel(
                row, text=entry["new_name"], width=col_w["New Filename Preview"],
                font=_font(12, "bold" if entry["changed"] else "normal"), text_color=preview_color, anchor="w",
            ).pack(side="left", padx=4)

            # Change badge
            badge_text = "MODIFIED" if entry["changed"] else "SAME"
            badge_color = T["badge_changed"] if entry["changed"] else T["badge_same"]
            change_frame = ctk.CTkFrame(row, fg_color="transparent", width=col_w["Change"])
            change_frame.pack(side="left", padx=4)
            change_frame.pack_propagate(False)
            ctk.CTkLabel(
                change_frame, text=f" {badge_text} ", font=_font(10, "bold"),
                fg_color=badge_color, corner_radius=4, text_color="#ffffff", height=20,
            ).pack(anchor="w", pady=5)

            # Status
            stat_color = T["warning"] if entry["status"] in ("Duplicate Name", "Target Exists") else T["text_dim"]
            ctk.CTkLabel(
                row, text=entry["status"], width=col_w["Status"],
                font=_font(11, "bold" if entry["status"] != "Pending" else "normal"),
                text_color=stat_color, anchor="w",
            ).pack(side="left", padx=4)

    def _update_ren_pag_controls(self, total_items: int, total_pages: int, start_idx: int, end_idx: int):
        T = self.T
        can_prev = self.renamer_page > 1
        can_next = self.renamer_page < total_pages

        self._set_btn_state(self.ren_btn_first, can_prev, T["btn_primary"])
        self._set_btn_state(self.ren_btn_prev, can_prev, T["btn_primary"])
        self._set_btn_state(self.ren_btn_next, can_next, T["btn_primary"])
        self._set_btn_state(self.ren_btn_last, can_next, T["btn_primary"])

        if total_items == 0:
            self.ren_page_label.configure(text="Page 0 of 0 (0 files)")
        else:
            self.ren_page_label.configure(
                text=f"Page {self.renamer_page} of {total_pages} (Showing {start_idx+1:,}–{end_idx:,} of {total_items:,} files)"
            )
        self.ren_page_entry.delete(0, "end")
        self.ren_page_entry.insert(0, str(self.renamer_page))

    def _ren_page_first(self):
        self.renamer_page = 1
        self._populate_renamer_table()

    def _ren_page_prev(self):
        if self.renamer_page > 1:
            self.renamer_page -= 1
            self._populate_renamer_table()

    def _ren_page_next(self):
        total_pages = max(1, math.ceil(len(self.renamer_filtered_plan) / self.renamer_page_size))
        if self.renamer_page < total_pages:
            self.renamer_page += 1
            self._populate_renamer_table()

    def _ren_page_last(self):
        total_pages = max(1, math.ceil(len(self.renamer_filtered_plan) / self.renamer_page_size))
        self.renamer_page = total_pages
        self._populate_renamer_table()

    def _ren_page_jump(self):
        val = self.ren_page_entry.get().strip()
        if not val.isdigit():
            return
        page = int(val)
        total_pages = max(1, math.ceil(len(self.renamer_filtered_plan) / self.renamer_page_size))
        self.renamer_page = max(1, min(page, total_pages))
        self._populate_renamer_table()

    def _ren_change_page_size(self, val: str):
        try:
            self.renamer_page_size = int(val)
        except ValueError:
            self.renamer_page_size = 100
        self.renamer_page = 1
        self._populate_renamer_table()

    def _filter_renamer_table(self):
        query = self.renamer_search_var.get().lower().strip()
        if not query:
            self.renamer_filtered_plan = list(self.current_renamer_plan)
        else:
            self.renamer_filtered_plan = [
                e for e in self.current_renamer_plan
                if query in e["name"].lower() or query in e["new_name"].lower()
            ]
        self.renamer_page = 1
        self._populate_renamer_table()

    def _on_renamer_entry_check(self, entry: dict, var: tk.BooleanVar):
        entry["selected"] = var.get()
        self._update_renamer_count()

    def _toggle_all_renamer(self, state: bool):
        target_list = self.renamer_filtered_plan if self.renamer_filtered_plan else self.current_renamer_plan
        for e in target_list:
            e["selected"] = state
        for var in self._renamer_check_vars:
            var.set(state)
        self._update_renamer_count()

    def _update_renamer_count(self):
        sel = sum(1 for e in self.current_renamer_plan if e.get("selected", True) and e.get("changed", False))
        total = len(self.current_renamer_plan)
        changed_total = sum(1 for e in self.current_renamer_plan if e.get("changed", False))
        self.renamer_count_label.configure(text=f"{sel:,} selected to rename (out of {changed_total:,} changed, {total:,} total)")
        self._set_btn_state(self.renamer_apply_btn, sel > 0, self.T["btn_primary"])

    def _execute_rename(self):
        if self._is_busy or not self.current_renamer_plan or not self.current_renamer_folder:
            return
        to_rename = [e for e in self.current_renamer_plan if e.get("selected", True) and e.get("changed", False)]
        n = len(to_rename)
        if n == 0:
            messagebox.showinfo("Nothing to Rename", "No filenames differ from their current names.")
            return

        conflicts = [e for e in to_rename if e.get("status") in ("Duplicate Name", "Target Exists")]
        if conflicts:
            msg = f"Warning: {len(conflicts)} files have name conflicts or target files already exist.\nProceed anyway? Conflicting files will receive a numbered suffix."
            if not messagebox.askyesno("Conflicts Detected", msg, icon="warning"):
                return
        else:
            if not messagebox.askyesno("Confirm Bulk Rename", f"Rename {n} file{'s' if n != 1 else ''}?"):
                return

        self._is_busy = True
        self._set_btn_state(self.renamer_scan_btn, False, self.T["card_alt"])
        self._set_btn_state(self.renamer_rename_btn, False, self.T["card_alt"])
        self.renamer_status.configure(text=f"Renaming {n} files...")

        def _worker():
            try:
                history = execute_bulk_rename(
                    self.current_renamer_plan,
                    self.current_renamer_folder,
                    progress_cb=lambda c, t: self.after(0, self.renamer_progress.set, c / max(t, 1)),
                )
                self.after(0, self._rename_done, len(history), None)
            except Exception as exc:
                self.after(0, self._rename_done, 0, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _rename_done(self, count: int, error: str | None):
        self._is_busy = False

        # Pagination & Large Drive Virtualization State
        self.general_page = 1
        self.general_page_size = 100
        self.general_filtered_plan: list[dict] = []
        self._general_scanning = False
        self._general_scan_cancel = threading.Event()

        self.media_page = 1
        self.media_page_size = 100
        self.media_filtered_plan: list[dict] = []
        self._media_scanning = False
        self._media_scan_cancel = threading.Event()

        self.renamer_page = 1
        self.renamer_page_size = 100
        self.renamer_filtered_plan: list[dict] = []
        self._renamer_scanning = False
        self._renamer_scan_cancel = threading.Event()
        self._renamer_debounce_id = None
        self._set_btn_state(self.renamer_scan_btn, True, self.T["btn_primary"])
        self.renamer_progress.set(0)

        if error:
            self.renamer_status.configure(text=f"Rename error: {error}")
            messagebox.showerror("Rename Failed", error)
        else:
            self.renamer_status.configure(text=f"Successfully renamed {count} files")
            messagebox.showinfo("Rename Complete", f"Successfully renamed {count} file{'s' if count != 1 else ''}.")
            self._update_renamer_undo_state()
            self._scan_renamer()

    def _undo_renamer(self):
        if self._is_busy or not self.current_renamer_folder:
            return
        if not messagebox.askyesno("Confirm Undo", "Undo the last bulk rename operation?"):
            return

        self._is_busy = True
        self._set_btn_state(self.renamer_undo_btn, False, self.T["card_alt"])
        self.renamer_status.configure(text="Undoing last rename operation...")

        def _worker():
            try:
                restored = undo_bulk_rename(
                    self.current_renamer_folder,
                    progress_cb=lambda c, t: self.after(0, self.renamer_progress.set, c / max(t, 1)),
                )
                self.after(0, self._undo_renamer_done, restored, None)
            except Exception as exc:
                self.after(0, self._undo_renamer_done, 0, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _undo_renamer_done(self, count: int, error: str | None):
        self._is_busy = False

        # Pagination & Large Drive Virtualization State
        self.general_page = 1
        self.general_page_size = 100
        self.general_filtered_plan: list[dict] = []
        self._general_scanning = False
        self._general_scan_cancel = threading.Event()

        self.media_page = 1
        self.media_page_size = 100
        self.media_filtered_plan: list[dict] = []
        self._media_scanning = False
        self._media_scan_cancel = threading.Event()

        self.renamer_page = 1
        self.renamer_page_size = 100
        self.renamer_filtered_plan: list[dict] = []
        self._renamer_scanning = False
        self._renamer_scan_cancel = threading.Event()
        self._renamer_debounce_id = None
        self.renamer_progress.set(0)
        self._update_renamer_undo_state()

        if error:
            self.renamer_status.configure(text=f"Undo error: {error}")
            messagebox.showerror("Undo Failed", error)
        else:
            self.renamer_status.configure(text=f"Restored {count} files to original names")
            messagebox.showinfo("Undo Complete", f"Restored {count} file{'s' if count != 1 else ''}.")
            self._scan_renamer()

    def _update_renamer_undo_state(self):
        has_history = False
        if self.current_renamer_folder:
            hp = Path(self.current_renamer_folder) / RENAMER_HISTORY_FILENAME
            has_history = hp.exists()
        self._set_btn_state(self.renamer_undo_btn, has_history, self.T["card_alt"])
        if has_history:
            self.renamer_undo_btn.configure(
                border_width=1, border_color=self.T["accent"], text_color=self.T["text"]
            )

    def _clean_filenames_preset(self):
        self.renamer_space_var.set("Replace with _ (underscore)")
        self.renamer_case_var.set("Title Case")
        self.renamer_lower_ext_var.set(True)
        self._on_renamer_rule_change()

    def _reset_renamer_rules(self):
        self.renamer_find_entry.delete(0, "end")
        self.renamer_replace_entry.delete(0, "end")
        self.renamer_prefix_entry.delete(0, "end")
        self.renamer_suffix_entry.delete(0, "end")
        self.renamer_match_case_var.set(False)
        self.renamer_regex_var.set(False)
        self.renamer_case_var.set("No Change")
        self.renamer_space_var.set("Keep spaces")
        self.renamer_lower_ext_var.set(False)
        self.renamer_num_var.set(False)
        self.renamer_num_pos_var.set("suffix")
        self.renamer_start_entry.delete(0, "end")
        self.renamer_start_entry.insert(0, "1")
        self.renamer_pad_entry.delete(0, "end")
        self.renamer_pad_entry.insert(0, "2")
        self._on_renamer_rule_change()

    # ── TV Database Browser Dialog ──────────────────────────────────────────
    def _open_tvdb_browser(self):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("TV Database Search & Inspector")
        win.geometry("740x600")
        win.configure(fg_color=T["bg"])
        win.transient(self)

        # Header
        hdr = ctk.CTkFrame(win, fg_color=T["header"], corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="TV Database (TVMaze Search)",
            font=_font(16, "bold"), text_color="#ffffff",
        ).pack(side="left", padx=16)

        # Search Card
        search_card = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        search_card.pack(fill="x", padx=16, pady=12)

        s_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        s_inner.pack(fill="x", padx=12, pady=10)

        q_entry = ctk.CTkEntry(
            s_inner, placeholder_text="Enter show title (e.g. Breaking Bad, Stranger Things)...",
            font=_font(13), height=38, corner_radius=6, border_width=1,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
        )
        q_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Result display container
        res_card = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=8,
                                border_width=1, border_color=T["border"])
        res_card.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        title_lbl = ctk.CTkLabel(res_card, text="", font=_font(18, "bold"), text_color=T["text"], anchor="w")
        meta_lbl = ctk.CTkLabel(res_card, text="", font=_font(12), text_color=T["accent"], anchor="w")
        desc_lbl = ctk.CTkLabel(res_card, text="", font=_font(12), text_color=T["text_dim"], justify="left", wraplength=680, anchor="w")

        ep_frame = ctk.CTkScrollableFrame(
            res_card, fg_color=T["chart_bg"], corner_radius=6,
            scrollbar_button_color=T["scrollbar"], scrollbar_button_hover_color=T["scrollbar_hover"],
        )

        def _do_search():
            q = q_entry.get().strip()
            if not q:
                return
            s_btn.configure(state="disabled", text="Searching...")
            win.update()

            def _search_thread():
                data = fetch_show_data(q)
                def _update_ui():
                    s_btn.configure(state="normal", text="Search")
                    if not data or not data.get("name") or not data.get("episodes"):
                        title_lbl.configure(text=f'No results found for "{q}"')
                        meta_lbl.configure(text="")
                        desc_lbl.configure(text="")
                        return

                    title_lbl.configure(text=f'{data["name"]} ({data.get("premiered", "")[:4]})')
                    meta_lbl.configure(
                        text=f'Rating: {data.get("rating")}  •  Network: {data.get("network")}  •  Status: {data.get("status")}  •  Genres: {data.get("genres")}'
                    )
                    desc_lbl.configure(text=data.get("summary") or "No overview available.")

                    title_lbl.pack(anchor="w", padx=14, pady=(12, 2))
                    meta_lbl.pack(anchor="w", padx=14, pady=(0, 6))
                    desc_lbl.pack(anchor="w", padx=14, pady=(0, 10))

                    # Episodes
                    for w in ep_frame.winfo_children():
                        w.destroy()
                    ep_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

                    episodes = data.get("episodes", {})
                    sorted_eps = sorted(episodes.keys())
                    for s, e in sorted_eps:
                        ep_title = episodes[(s, e)]
                        r_frame = ctk.CTkFrame(ep_frame, fg_color="transparent")
                        r_frame.pack(fill="x", pady=1)
                        ctk.CTkLabel(
                            r_frame, text=f"S{s:02d}E{e:02d}", width=70,
                            font=_font(12, "bold"), text_color=T["accent"], anchor="w",
                        ).pack(side="left", padx=4)
                        ctk.CTkLabel(
                            r_frame, text=ep_title, font=_font(12),
                            text_color=T["text"], anchor="w",
                        ).pack(side="left", padx=4)

                self.after(0, _update_ui)

            threading.Thread(target=_search_thread, daemon=True).start()

        s_btn = ctk.CTkButton(
            s_inner, text="Search", width=95, height=38,
            font=_font(13, "bold"), corner_radius=6,
            fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
            command=_do_search,
        )
        s_btn.pack(side="left")
        q_entry.bind("<Return>", lambda _: _do_search())

    # ── Anime Database Browser Dialog (Kitsu) ──────────────────────────────
    def _open_animedb_browser(self):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Anime Database Search & Inspector (Kitsu)")
        win.geometry("740x600")
        win.configure(fg_color=T["bg"])
        win.transient(self)

        # Header
        hdr = ctk.CTkFrame(win, fg_color="#be185d", corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="Anime Database (Kitsu Search)",
            font=_font(16, "bold"), text_color="#ffffff",
        ).pack(side="left", padx=16)

        # Search Card
        search_card = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=8,
                                   border_width=1, border_color=T["border"])
        search_card.pack(fill="x", padx=16, pady=12)

        s_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        s_inner.pack(fill="x", padx=12, pady=10)

        q_entry = ctk.CTkEntry(
            s_inner, placeholder_text="Enter anime title (e.g. Attack on Titan, Jujutsu Kaisen, One Piece)...",
            font=_font(13), height=38, corner_radius=6, border_width=1,
            fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"],
        )
        q_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Result display container
        res_card = ctk.CTkFrame(win, fg_color=T["card"], corner_radius=8,
                                border_width=1, border_color=T["border"])
        res_card.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        title_lbl = ctk.CTkLabel(res_card, text="", font=_font(18, "bold"), text_color=T["text"], anchor="w")
        meta_lbl = ctk.CTkLabel(res_card, text="", font=_font(12), text_color="#ec4899", anchor="w")
        desc_lbl = ctk.CTkLabel(res_card, text="", font=_font(12), text_color=T["text_dim"], justify="left", wraplength=680, anchor="w")

        ep_frame = ctk.CTkScrollableFrame(
            res_card, fg_color=T["chart_bg"], corner_radius=6,
            scrollbar_button_color=T["scrollbar"], scrollbar_button_hover_color=T["scrollbar_hover"],
        )

        def _do_search():
            q = q_entry.get().strip()
            if not q:
                return
            s_btn.configure(state="disabled", text="Searching...")
            win.update()

            def _search_thread():
                data = fetch_anime_data(q)
                # If we have an ID, pre-fetch up to 40-60 episodes for full listing
                if data and data.get("id"):
                    anime_id = data["id"]
                    for offset in (20, 40):
                        if len(data.get("episodes", {})) >= int(data.get("total_episodes") or 0):
                            break
                        ep_url = f"https://kitsu.io/api/edge/anime/{anime_id}/episodes?page[limit]=20&page[offset]={offset}"
                        ep_req = urllib.request.Request(
                            ep_url,
                            headers={"User-Agent": "FileSorter/3.1", "Accept": "application/vnd.api+json"},
                        )
                        try:
                            with urllib.request.urlopen(ep_req, timeout=5) as ep_resp:
                                ep_data = json.loads(ep_resp.read().decode("utf-8"))
                                items = ep_data.get("data", [])
                                if not items:
                                    break
                                for item in items:
                                    ep_attr = item.get("attributes", {})
                                    num = ep_attr.get("number")
                                    t = ep_attr.get("canonicalTitle")
                                    if num is not None and t:
                                        data["episodes"][int(num)] = sanitize_filename(t)
                                if len(items) < 20:
                                    break
                        except Exception:
                            break

                def _update_ui():
                    s_btn.configure(state="normal", text="Search")
                    if not data or not data.get("name") or not data.get("id"):
                        title_lbl.configure(text=f'No anime found for "{q}"')
                        meta_lbl.configure(text="")
                        desc_lbl.configure(text="")
                        return

                    year_str = f" ({data['year']})" if data.get("year") else ""
                    title_lbl.configure(text=f"{data['name']}{year_str}")
                    meta_lbl.configure(
                        text=f"Rating: {data.get('rating')}  •  Status: {data.get('status')}  •  Episodes: {data.get('total_episodes')}"
                    )
                    desc_lbl.configure(text=data.get("summary") or "No synopsis available.")

                    title_lbl.pack(anchor="w", padx=14, pady=(12, 2))
                    meta_lbl.pack(anchor="w", padx=14, pady=(0, 6))
                    desc_lbl.pack(anchor="w", padx=14, pady=(0, 10))

                    # Episodes
                    for w in ep_frame.winfo_children():
                        w.destroy()
                    ep_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

                    episodes = data.get("episodes", {})
                    sorted_eps = sorted(episodes.keys())
                    if not sorted_eps:
                        r_frame = ctk.CTkFrame(ep_frame, fg_color="transparent")
                        r_frame.pack(fill="x", pady=4)
                        ctk.CTkLabel(
                            r_frame, text="No individual episode titles listed for this entry.",
                            font=_font(12), text_color=T["text_dim"],
                        ).pack(side="left", padx=4)
                    else:
                        for ep_num in sorted_eps:
                            ep_t = episodes[ep_num]
                            r_frame = ctk.CTkFrame(ep_frame, fg_color="transparent")
                            r_frame.pack(fill="x", pady=1)
                            ctk.CTkLabel(
                                r_frame, text=f"Ep {ep_num:02d}" if ep_num < 100 else f"Ep {ep_num}",
                                width=70, font=_font(12, "bold"), text_color="#ec4899", anchor="w",
                            ).pack(side="left", padx=4)
                            ctk.CTkLabel(
                                r_frame, text=ep_t, font=_font(12),
                                text_color=T["text"], anchor="w",
                            ).pack(side="left", padx=4)

                self.after(0, _update_ui)

            threading.Thread(target=_search_thread, daemon=True).start()

        s_btn = ctk.CTkButton(
            s_inner, text="Search", width=95, height=38,
            font=_font(13, "bold"), corner_radius=6,
            fg_color="#ec4899", hover_color="#db2777",
            command=_do_search,
        )
        s_btn.pack(side="left")
        q_entry.bind("<Return>", lambda _: _do_search())

    # ═══════════════════════════════════════════════════════════════════════
    #  GENERAL FILE SORTER HANDLERS
    # ═══════════════════════════════════════════════════════════════════════
    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.current_folder = folder
            self.settings["last_folder"] = folder
            self._set_btn_state(self.scan_btn, True, self.T["btn_primary"])
            self._update_general_undo_state()
            self._scan_general()

    def _scan_general(self):
        if hasattr(self, "_general_scanning") and self._general_scanning:
            self.status.configure(text="Cancelling scan...")
            self._general_scan_cancel.set()
            return

        if not self.current_folder or self._is_busy:
            return

        self._is_busy = True
        self._general_scanning = True
        self._general_scan_cancel.clear()
        self.scan_btn.configure(text="✕ Cancel", fg_color=self.T["danger"], hover_color=self.T["danger_hover"], state="normal")
        self._set_btn_state(self.sort_btn, False, self.T["card_alt"])
        self.status.configure(text="Scanning folder for files...")
        self.progress.set(0)

        def _worker():
            try:
                plan = scan_general_folder(
                    self.current_folder, self.ext_map,
                    recursive=self.recursive_var.get(),
                    sort_uncategorised_to_misc=self.misc_var.get(),
                    progress_cb=lambda count: self.after(0, lambda c=count: self.status.configure(text=f"Scanning... {c:,} files found")),
                    cancel_event=self._general_scan_cancel,
                )
                self.after(0, self._scan_general_done, plan, None)
            except Exception as exc:
                self.after(0, self._scan_general_done, [], str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _scan_general_done(self, plan: list[dict], error: str | None):
        self._is_busy = False
        self._general_scanning = False
        self.scan_btn.configure(text="Scan Files", fg_color=self.T["btn_primary"], hover_color=self.T["accent_hover"], state="normal")
        self.progress.set(0)

        if error:
            self.status.configure(text=f"Scan error: {error}")
            messagebox.showerror("Scan Failed", error)
            return

        self.current_plan = plan
        self.general_filtered_plan = list(plan)
        self.general_page = 1
        self._populate_file_table()
        self._update_general_stats(self.current_plan)
        self._update_general_count()
        self._update_general_undo_state()

        dups = sum(1 for e in self.current_plan if e.get("duplicate"))
        if dups:
            self.dup_label.configure(text=f"{dups:,} duplicate{'s' if dups != 1 else ''} found")
        else:
            self.dup_label.configure(text="")

        n = len(self.current_plan)
        if n > 0:
            self.status.configure(text=f"Scan complete — {n:,} files identified")
        else:
            self.status.configure(text="No sortable files in this folder")

    def _populate_file_table(self, plan: list[dict] | None = None):
        if plan is not None:
            self.general_filtered_plan = plan

        active = self.general_filtered_plan
        total_items = len(active)
        page_size = self.general_page_size
        total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1

        if self.general_page > total_pages:
            self.general_page = total_pages
        if self.general_page < 1:
            self.general_page = 1

        start_idx = (self.general_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        page_items = active[start_idx:end_idx]

        self._update_gen_pag_controls(total_items, total_pages, start_idx, end_idx)

        T = self.T
        for w in self.table_body.winfo_children():
            w.destroy()
        self._check_vars.clear()

        if not page_items:
            msg = "No sortable files found in this folder." if total_items == 0 else "No items on this page."
            ctk.CTkLabel(
                self.table_body,
                text=msg, font=_font(14), text_color=T["text_dim"],
            ).pack(pady=80)
            return

        col_w = {col[0]: col[1] for col in FILE_TABLE_COLS}

        for idx, entry in enumerate(page_items):
            bg = T["row_even"] if idx % 2 == 0 else T["row_odd"]
            row = ctk.CTkFrame(self.table_body, fg_color=bg, corner_radius=0, height=32)
            row.pack(fill="x")
            row.pack_propagate(False)

            # Checkbox
            var = tk.BooleanVar(value=entry.get("selected", True))
            self._check_vars.append(var)
            var.trace_add("write", lambda *_, e=entry, v=var: self._on_general_entry_check(e, v))
            ctk.CTkCheckBox(
                row, text="", variable=var, width=col_w[""],
                fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
                border_color=T["border"], checkmark_color="#ffffff", corner_radius=4,
            ).pack(side="left", padx=4)

            # File name
            ctk.CTkLabel(
                row, text=entry["name"], width=col_w["File Name"],
                font=_font(12), text_color=T["text"], anchor="w",
            ).pack(side="left", padx=4)

            # Size
            ctk.CTkLabel(
                row, text=human_size(entry.get("size", 0)), width=col_w["Size"],
                font=_font(12), text_color=T["text_dim"], anchor="w",
            ).pack(side="left", padx=4)

            # Extension
            ext = Path(entry["name"]).suffix.lower()
            ctk.CTkLabel(
                row, text=ext, width=col_w["Ext"],
                font=_font(12, "bold"), text_color=T["accent"], anchor="w",
            ).pack(side="left", padx=4)

            # Category badge
            cat_frame = ctk.CTkFrame(row, fg_color="transparent", width=col_w["Target Category"])
            cat_frame.pack(side="left", padx=4)
            cat_frame.pack_propagate(False)
            cat_color = self._get_cat_color(entry["category"])
            ctk.CTkLabel(
                cat_frame, text=f"  {entry['category']}  ", font=_font(11, "bold"),
                fg_color=cat_color, corner_radius=5, text_color="#ffffff", height=22,
            ).pack(anchor="w", pady=4)

            # Duplicate
            dup_text = "Yes" if entry.get("duplicate") else ""
            dup_color = T["warning"] if entry.get("duplicate") else T["text_muted"]
            ctk.CTkLabel(
                row, text=dup_text, width=col_w["Dup"],
                font=_font(11, "bold"), text_color=dup_color, anchor="w",
            ).pack(side="left", padx=4)

            # Status
            ctk.CTkLabel(
                row, text="Pending", width=col_w["Status"],
                font=_font(12), text_color=T["text_dim"], anchor="w",
            ).pack(side="left", padx=4)

    def _update_gen_pag_controls(self, total_items: int, total_pages: int, start_idx: int, end_idx: int):
        T = self.T
        can_prev = self.general_page > 1
        can_next = self.general_page < total_pages

        self._set_btn_state(self.gen_btn_first, can_prev, T["btn_primary"])
        self._set_btn_state(self.gen_btn_prev, can_prev, T["btn_primary"])
        self._set_btn_state(self.gen_btn_next, can_next, T["btn_primary"])
        self._set_btn_state(self.gen_btn_last, can_next, T["btn_primary"])

        if total_items == 0:
            self.gen_page_label.configure(text="Page 0 of 0 (0 files)")
        else:
            self.gen_page_label.configure(
                text=f"Page {self.general_page} of {total_pages} (Showing {start_idx+1:,}–{end_idx:,} of {total_items:,} files)"
            )
        self.gen_page_entry.delete(0, "end")
        self.gen_page_entry.insert(0, str(self.general_page))

    def _gen_page_first(self):
        self.general_page = 1
        self._populate_file_table()

    def _gen_page_prev(self):
        if self.general_page > 1:
            self.general_page -= 1
            self._populate_file_table()

    def _gen_page_next(self):
        total_pages = max(1, math.ceil(len(self.general_filtered_plan) / self.general_page_size))
        if self.general_page < total_pages:
            self.general_page += 1
            self._populate_file_table()

    def _gen_page_last(self):
        total_pages = max(1, math.ceil(len(self.general_filtered_plan) / self.general_page_size))
        self.general_page = total_pages
        self._populate_file_table()

    def _gen_page_jump(self):
        val = self.gen_page_entry.get().strip()
        if not val.isdigit():
            return
        page = int(val)
        total_pages = max(1, math.ceil(len(self.general_filtered_plan) / self.general_page_size))
        self.general_page = max(1, min(page, total_pages))
        self._populate_file_table()

    def _gen_change_page_size(self, val: str):
        try:
            self.general_page_size = int(val)
        except ValueError:
            self.general_page_size = 100
        self.general_page = 1
        self._populate_file_table()

    def _filter_general_table(self):
        query = self.search_var.get().lower().strip()
        if not query:
            self.general_filtered_plan = list(self.current_plan)
        else:
            self.general_filtered_plan = [
                e for e in self.current_plan
                if query in e["name"].lower() or query in e["category"].lower()
            ]
        self.general_page = 1
        self._populate_file_table()

    def _on_general_entry_check(self, entry: dict, var: tk.BooleanVar):
        entry["selected"] = var.get()
        self._update_general_count()

    def _toggle_all_general(self, state: bool):
        target_list = self.general_filtered_plan if self.general_filtered_plan else self.current_plan
        for e in target_list:
            e["selected"] = state
        for var in self._check_vars:
            var.set(state)
        self._update_general_count()

    def _update_general_count(self):
        sel = sum(1 for e in self.current_plan if e.get("selected", True))
        total = len(self.current_plan)
        cats = len({e["category"] for e in self.current_plan if e.get("selected", True)})
        self.count_label.configure(
            text=f"{sel:,}/{total:,} selected  •  {cats} categor{'ies' if cats != 1 else 'y'}"
        )
        self._set_btn_state(self.sort_btn, sel > 0, self.T["success"])

    def _update_general_stats(self, plan: list[dict]):
        T = self.T
        for w in self.stats_frame.winfo_children():
            w.destroy()

        if not plan:
            ctk.CTkLabel(
                self.stats_frame, text="No scan data yet",
                font=_font(13), text_color=T["text_muted"],
            ).pack(pady=20)
            return

        cat_counts: dict[str, int] = defaultdict(int)
        cat_sizes: dict[str, int] = defaultdict(int)
        for e in plan:
            cat_counts[e["category"]] += 1
            cat_sizes[e["category"]] += e.get("size", 0)
        total = sum(cat_counts.values())
        sorted_cats = sorted(cat_counts.items(), key=lambda x: -x[1])

        for i, (cat, count) in enumerate(sorted_cats):
            pct = count / total * 100 if total else 0
            color = self._get_cat_color(cat)

            row_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            label_row = ctk.CTkFrame(row_frame, fg_color="transparent")
            label_row.pack(fill="x")

            ctk.CTkLabel(
                label_row, text=f"●  {cat}", font=_font(12, "bold"),
                text_color=color, anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                label_row, text=f"{count:,} ({pct:.0f}%) | {human_size(cat_sizes[cat])}",
                font=_font(11), text_color=T["text_dim"], anchor="e",
            ).pack(side="right")

            bar_bg = ctk.CTkFrame(row_frame, height=6, fg_color=T["chart_bg"], corner_radius=3)
            bar_bg.pack(fill="x", pady=(2, 4))

            ctk.CTkFrame(
                bar_bg, height=6, fg_color=color, corner_radius=3,
            ).place(relx=0, rely=0, relwidth=max(pct / 100, 0.02), relheight=1)

    def _sort_general(self):
        if self._is_busy or not self.current_plan:
            return
        sel = [e for e in self.current_plan if e.get("selected", True)]
        n = len(sel)
        if n == 0:
            return

        if not messagebox.askyesno(
            "Confirm Sort",
            f"Move {n} file{'s' if n != 1 else ''} into category folders?\n\n"
            f"You can undo this operation at any time.",
        ):
            return

        self._is_busy = True
        self._set_btn_state(self.scan_btn, False, self.T["card_alt"])
        self._set_btn_state(self.sort_btn, False, self.T["card_alt"])
        self.status.configure(text="Sorting files into categories...")

        def _worker():
            try:
                execute_general_sort(
                    self.current_plan, self.current_folder,
                    progress_cb=lambda c, t: self.after(0, self.progress.set, c / max(t, 1)),
                )
                self.after(0, self._sort_general_done, None)
            except Exception as exc:
                self.after(0, self._sort_general_done, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _sort_general_done(self, error: str | None):
        self._is_busy = False

        # Pagination & Large Drive Virtualization State
        self.general_page = 1
        self.general_page_size = 100
        self.general_filtered_plan: list[dict] = []
        self._general_scanning = False
        self._general_scan_cancel = threading.Event()

        self.media_page = 1
        self.media_page_size = 100
        self.media_filtered_plan: list[dict] = []
        self._media_scanning = False
        self._media_scan_cancel = threading.Event()

        self.renamer_page = 1
        self.renamer_page_size = 100
        self.renamer_filtered_plan: list[dict] = []
        self._renamer_scanning = False
        self._renamer_scan_cancel = threading.Event()
        self._renamer_debounce_id = None
        self._set_btn_state(self.scan_btn, True, self.T["btn_primary"])
        self.progress.set(0)

        if error:
            self.status.configure(text=f"Error: {error}")
            messagebox.showerror("Sort Failed", error)
        else:
            sel = sum(1 for e in self.current_plan if e.get("selected", True))
            self.status.configure(text=f"Sorted {sel} files successfully!")
            messagebox.showinfo("Done", f"Sorted {sel} files into category folders!")
            self._update_general_undo_state()
            self._scan_general()

    def _undo_general(self):
        if self._is_busy or not self.current_folder:
            return
        if not messagebox.askyesno("Confirm Undo", "Reverse the last sort operation?"):
            return

        self._is_busy = True
        self.status.configure(text="Undoing last sort...")

        def _worker():
            try:
                count = undo_general_sort(
                    self.current_folder,
                    progress_cb=lambda c, t: self.after(0, self.progress.set, c / max(t, 1)),
                )
                self.after(0, self._undo_general_done, count, None)
            except Exception as exc:
                self.after(0, self._undo_general_done, 0, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _undo_general_done(self, count: int, error: str | None):
        self._is_busy = False

        # Pagination & Large Drive Virtualization State
        self.general_page = 1
        self.general_page_size = 100
        self.general_filtered_plan: list[dict] = []
        self._general_scanning = False
        self._general_scan_cancel = threading.Event()

        self.media_page = 1
        self.media_page_size = 100
        self.media_filtered_plan: list[dict] = []
        self._media_scanning = False
        self._media_scan_cancel = threading.Event()

        self.renamer_page = 1
        self.renamer_page_size = 100
        self.renamer_filtered_plan: list[dict] = []
        self._renamer_scanning = False
        self._renamer_scan_cancel = threading.Event()
        self._renamer_debounce_id = None
        self.progress.set(0)
        self._update_general_undo_state()

        if error:
            self.status.configure(text=f"Undo error: {error}")
            messagebox.showerror("Undo Failed", error)
        else:
            self.status.configure(text=f"Restored {count} files")
            messagebox.showinfo("Undo Complete", f"Restored {count} files.")
            self._scan_general()

    def _update_general_undo_state(self):
        has_history = False
        if self.current_folder:
            hp = Path(self.current_folder) / HISTORY_FILENAME
            has_history = hp.exists()
        self._set_btn_state(self.undo_btn, has_history, self.T["card_alt"])
        if has_history:
            self.undo_btn.configure(
                border_width=1, border_color=self.T["accent"], text_color=self.T["text"]
            )

    # ── Category Editor & Export ────────────────────────────────────────────
    def _open_category_editor(self):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Edit Categories")
        win.geometry("620x520")
        win.configure(fg_color=T["bg"])
        win.transient(self)

        ctk.CTkLabel(win, text="Category Editor", font=_font(18, "bold"), text_color=T["text"]).pack(pady=(16, 4))
        ctk.CTkLabel(win, text="Modify categories and their associated file extensions.", font=_font(13), text_color=T["text_dim"]).pack(pady=(0, 12))

        editor_frame = ctk.CTkScrollableFrame(win, fg_color=T["card"], corner_radius=8,
                                              scrollbar_button_color=T["scrollbar"], scrollbar_button_hover_color=T["scrollbar_hover"])
        editor_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        entries: dict[str, ctk.CTkEntry] = {}
        for cat in sorted(self.categories.keys()):
            row = ctk.CTkFrame(editor_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=cat, width=130, font=_font(13, "bold"), text_color=T["text"], anchor="w").pack(side="left", padx=(8, 4))
            ent = ctk.CTkEntry(row, font=_font(12), fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"])
            ent.pack(side="left", fill="x", expand=True, padx=4)
            ent.insert(0, "  ".join(self.categories[cat]))
            entries[cat] = ent

            def _del(c=cat):
                if messagebox.askyesno("Delete", f"Remove category '{c}'?"):
                    del self.categories[c]
                    self.ext_map = build_ext_map(self.categories)
                    win.destroy()
                    self._open_category_editor()

            ctk.CTkButton(row, text="Remove", width=65, height=28, fg_color=T["danger"],
                          hover_color=T["danger_hover"], text_color="#ffffff", corner_radius=6,
                          font=_font(12, "bold"), command=_del).pack(side="right", padx=4)

        ctk.CTkFrame(editor_frame, height=1, fg_color=T["border"]).pack(fill="x", padx=8, pady=8)
        add_row = ctk.CTkFrame(editor_frame, fg_color="transparent")
        add_row.pack(fill="x", pady=4)
        new_name = ctk.CTkEntry(add_row, placeholder_text="Category name...", width=140, font=_font(12),
                                fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"])
        new_name.pack(side="left", padx=8)
        new_exts = ctk.CTkEntry(add_row, placeholder_text="Extensions (e.g. .abc .def)...", font=_font(12),
                                fg_color=T["input_bg"], border_color=T["border"], text_color=T["text"])
        new_exts.pack(side="left", fill="x", expand=True, padx=4)

        def _add():
            name = new_name.get().strip()
            exts = [e.strip() for e in new_exts.get().split() if e.strip().startswith(".")]
            if name and exts:
                self.categories[name] = exts
                self.ext_map = build_ext_map(self.categories)
                win.destroy()
                self._open_category_editor()

        ctk.CTkButton(add_row, text="+ Add", width=70, height=30, fg_color=T["success"],
                      hover_color=T["success_hover"], text_color="#ffffff", corner_radius=6,
                      font=_font(12, "bold"), command=_add).pack(side="right", padx=8)

        def _save():
            for cat, ent in entries.items():
                exts = [e.strip() for e in ent.get().split() if e.strip().startswith(".")]
                if exts:
                    self.categories[cat] = exts
            self.ext_map = build_ext_map(self.categories)
            self.settings["custom_categories"] = {
                k: v for k, v in self.categories.items()
                if k not in DEFAULT_CATEGORIES or v != DEFAULT_CATEGORIES.get(k)
            }
            save_settings(self.settings)
            win.destroy()
            self.status.configure(text="Categories updated")
            if self.current_folder:
                self._scan_general()

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(btn_row, text="Save & Close", height=36, font=_font(13, "bold"),
                      fg_color=T["btn_primary"], hover_color=T["btn_primary_hover"],
                      corner_radius=6, command=_save).pack(side="right")
        ctk.CTkButton(btn_row, text="Cancel", height=36, font=_font(13), fg_color=T["card"],
                      hover_color=T["border"], text_color=T["text"], corner_radius=6,
                      border_width=1, border_color=T["border"], command=win.destroy).pack(side="right", padx=8)

    def _export_report(self):
        if self.active_tab == "files":
            plan_to_export = self.current_plan
        elif self.active_tab == "media":
            plan_to_export = self.current_media_plan
        else:
            plan_to_export = self.current_renamer_plan

        if not plan_to_export:
            messagebox.showinfo("No Data", "Scan a folder first to generate a report.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Sort / Rename Report", defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if self.active_tab == "files":
                    writer.writerow(["File Name", "Extension", "Category", "Size (bytes)", "Size (human)", "Duplicate", "Selected"])
                    for e in plan_to_export:
                        writer.writerow([
                            e["name"], Path(e["name"]).suffix.lower(), e["category"],
                            e.get("size", 0), human_size(e.get("size", 0)),
                            "Yes" if e.get("duplicate") else "No",
                            "Yes" if e.get("selected", True) else "No",
                        ])
                elif self.active_tab == "media":
                    writer.writerow(["Original File", "Type", "Title", "Season/Ep", "Episode Title", "Destination Path", "Selected"])
                    for e in plan_to_export:
                        writer.writerow([
                            e["name"], e.get("type"), e.get("title"), e.get("se_tag"),
                            e.get("ep_title"), e.get("dest"),
                            "Yes" if e.get("selected", True) else "No",
                        ])
                else:
                    writer.writerow(["Original File", "New Filename", "Size (bytes)", "Size (human)", "Changed", "Status", "Selected"])
                    for e in plan_to_export:
                        writer.writerow([
                            e["name"], e.get("new_name"),
                            e.get("size", 0), human_size(e.get("size", 0)),
                            "Yes" if e.get("changed") else "No",
                            e.get("status"),
                            "Yes" if e.get("selected", True) else "No",
                        ])
            messagebox.showinfo("Export Complete", f"Report saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _on_close(self):
        self.settings["window_geometry"] = self.geometry()
        self.settings["recursive"] = self.recursive_var.get()
        self.settings["sort_misc"] = self.misc_var.get()
        self.settings["media_recursive"] = self.media_rec_var.get()
        self.settings["media_fetch_tvdb"] = self.media_tvdb_var.get()
        self.settings["media_fetch_anime"] = self.media_anime_var.get()
        self.settings["media_season_folders"] = self.media_season_var.get()
        self.settings["media_structure_by_type"] = self.media_struct_var.get()
        self.settings["renamer_recursive"] = self.renamer_rec_var.get()
        self.settings["renamer_case"] = self.renamer_case_var.get()
        self.settings["renamer_spaces"] = self.renamer_space_var.get()
        self.settings["renamer_lower_ext"] = self.renamer_lower_ext_var.get()
        self.settings["renamer_numbering"] = self.renamer_num_var.get()
        self.settings["renamer_num_pos"] = self.renamer_num_pos_var.get()
        try:
            self.settings["renamer_num_start"] = int(self.renamer_start_entry.get() or "1")
        except (ValueError, AttributeError):
            pass
        try:
            self.settings["renamer_num_pad"] = int(self.renamer_pad_entry.get() or "2")
        except (ValueError, AttributeError):
            pass
        save_settings(self.settings)
        self.destroy()


# ═════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = FileSorterApp()
    app.mainloop()
