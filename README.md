<div align="center">

# 📁 File Sorter & Media Organizer v3.2

**A modern, desktop powerhouse for Windows to organize files, TV series, anime, movies with database metadata, and perform bulk file renaming.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-2563eb.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v3.2.0-purple.svg)](https://github.com/Zeusx212/File-Sorter/releases)

</div>

---

## 🌟 Highlights & Features

### 1. 🗂️ Files & Folders Sorter
- **Category Sorting**: Instantly sort mixed folders into clean categories (Images, Documents, Videos, Music, Code, Archives, Executables, 3D Models, and more).
- **Duplicate Detection**: Identifies exact duplicates using checksum hashing.
- **Custom Categories**: Add, remove, or customize file extensions and category names with the built-in Category Editor.
- **Multi-Level Undo**: Safely reverts sorting operations in reverse order, restoring files and cleaning up empty directories.
- **CSV Export**: Export detailed sorting and duplicate reports with a single click.

### 2. 🎬 Media Sorter (TV Shows & Movies)
- **Automatic Classification**: Intelligently classifies files as TV Episodes, Movies, or standalone Videos.
- **TV Database Integration (TVMaze API)**: Free, keyless API integration to retrieve canonical series titles and exact episode names.
- **Smart Directory Structure**:
  - `TV Shows / <Show Name> / Season <XX> / <Show Name> - S01E02 - <Episode Title>.<ext>`
  - `Movies / <Movie Name> (<Year>) / <Movie Name> (<Year>).<ext>`
- **Database Inspector**: Search and inspect full TV show guides, ratings, networks, genres, and complete episode guides.

### 3. 🎌 Anime Database (Kitsu API)
- **Release Group Parsing**: Automatically detects anime release groups (e.g. `[SubsPlease]`, `[HorribleSubs]`, `[Erai-raws]`, `[Judas]`, `[DKB]`).
- **Absolute Episode Numbering**: Handles absolute episode numbers (e.g., `One Piece - 1085 [1080p].mkv`, `Naruto Shippuden Episode 250.mp4`, `Bleach - 001.mkv`).
- **Kitsu API Integration**: Free, keyless anime database integration fetching canonical titles, ratings, status, and episode titles.
- **Anime Database Inspector**: Search anime titles (supporting English, Romaji, and Japanese search queries), browse synopses, ratings, and full episode guides.
- **Clean Structure**: Organizes anime into clean directories and filenames, stripping noisy CRC32 hashes and quality tags.

### 4. 🏷️ Bulk File Renamer
- **Real-Time Live Preview**: See exact before-and-after filenames highlighted in real time as you configure rules.
- **Find & Replace**: Case-sensitive and case-insensitive string replacements.
- **Regex Support**: Full regular expression matching and capture groups (`\1`, `\2`).
- **Prefix & Suffix**: Easily prepend or append tags.
- **Case Transformation**: Transform file stems to `lowercase`, `UPPERCASE`, `Title Case`, or `Capitalize Words`.
- **Space Handling**: Keep spaces, replace with underscores (`_`), hyphens (`-`), or remove spaces completely.
- **Sequential Numbering**: Prefix or suffix numbering with customizable start index and zero-padding (e.g., `01`, `001`).
- **Extension Controls**: Standardize and lowercase file extensions (`.JPG` → `.jpg`).
- **Two-Pass Collision Protection**: Avoids Windows case-collision issues (`file.txt` → `FILE.TXT`) and circular rename overlaps (`A` → `B`, `B` → `C`).
- **Undo Support**: Every rename operation is recorded for full multi-level rollback.

### 5. 🎨 Design & Accessibility
- **High-Contrast Slate Themes**: Slate Dark (`#0f172a`) and Crisp Light (`#f8fafc`) themes designed for readability.
- **Custom Antialiased Sun/Moon Toggle**: Pillow-rendered vector icons for seamless dark/light switching.
- **Status & Collision Warnings**: Color-coded badges for changed files, duplicates, and target conflicts.

---

## 🚀 Download & Installation

### Option 1: Standalone Windows Executable (No Python Required)
1. Head over to the **[Releases](https://github.com/Zeusx212/File-Sorter/releases)** page.
2. Download **`File Sorter.exe`**.
3. Run the application directly. No installation or setup required.

### Option 2: Run from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/Zeusx212/File-Sorter.git
   cd File-Sorter
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the app:
   ```bash
   python file_sorter.py
   ```

---

## 🛠️ Building Standalone Executable

To compile a single-file Windows `.exe` using PyInstaller:

```bash
pyinstaller --onefile --windowed --name "File Sorter" --collect-all customtkinter --noconfirm file_sorter.py
```
The compiled executable will be located in the `dist/` directory.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.
