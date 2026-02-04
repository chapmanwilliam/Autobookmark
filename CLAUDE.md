# CLAUDE.md - Autobookmark Project Guide

## Project Overview

**Autobookmark** is a sophisticated PDF processing and management application that automatically creates bookmarks, tables of contents, and hyperlinks in PDF documents. It organizes, annotates, and enhances PDF documents with chronological information, structured bookmarks, and cross-references.

**Primary Technologies:**
- Python 3
- GUI Frameworks: wxPython (main), PyQt6, Tkinter
- PDF Processing: PyMuPDF (fitz), PyPDF2, pdfminer, pikepdf
- OCR: ocrmypdf, pytesseract
- Cross-platform: Windows, macOS, Linux

## Codebase Structure

```
/home/user/Autobookmark/
├── Core PDF Processing Modules
│   ├── wwc_AutoBookmarker.py    # Main bookmarking engine (2083 lines)
│   ├── wwc_parser.py            # Date/time string parser (1452 lines)
│   ├── wwc_TOC.py               # Table of Contents generation
│   ├── wwc_page_labels.py       # PDF page label handling
│   ├── wwc_parsebookmark.py     # Bookmark parsing and date extraction
│   ├── wwc_hyperlinkpagerefs.py # Page reference linking
│   ├── wwc_merge.py             # PDF merging utilities
│   └── wwc_paginatepdf.py       # PDF pagination utilities
│
├── GUI Components
│   ├── Display.py               # Main PDF viewer (Tkinter, 1890 lines)
│   ├── frame_main.py            # Main wxPython frame with drag-and-drop
│   ├── frame_main_gui.py        # wxFormBuilder generated GUI
│   ├── AutoBookmarker.py        # Application launcher
│   ├── CdropLabel.py            # Drag-and-drop label layout
│   ├── tree.py                  # Tree structure for bookmarks (1213 lines)
│   └── RubberBand.py            # Selection tool for PDF display
│
├── Dialogs
│   ├── tocDialog.py             # Table of Contents editing
│   ├── hyperlinkDialog.py       # Hyperlink configuration
│   ├── paginateDialog.py        # PDF pagination
│   ├── rotateDialog.py          # Page rotation
│   ├── searchtextDialog.py      # Text search
│   ├── searchtreeDialog.py      # Tree-based bookmark search
│   └── printing.py              # Print dialog
│
├── Utilities
│   ├── utilities.py             # Color handling, file operations
│   ├── wwc_gui_config.py        # GUI configuration and tooltips
│   ├── hyperlinks.py            # Hyperlink generation
│   ├── merge.py                 # PDF merging (wxPython-based)
│   └── OrderPages.py            # Page ordering
│
├── Entry Points & Configuration
│   ├── action.py                # Main action dispatcher
│   ├── main.py                  # PyCharm template entry point
│   ├── setupMac.py              # macOS setup
│   ├── setupPC.py               # Windows setup
│   └── requirements.txt         # Python dependencies
│
├── Build Configuration
│   ├── pyinstaller.spec         # PyInstaller build config
│   └── pyinstaller.sh           # Build shell script
│
├── Resources
│   ├── images/                  # Application icons and assets
│   ├── Resources/               # Configuration files
│   └── pyutilsettings.db        # Settings database (shelve)
│
└── Build Outputs (gitignored)
    ├── buildPCDisplay/          # Windows executable
    ├── buildMacDisplay/         # macOS application bundle
    ├── buildPCWidget/           # Windows widget build
    └── buildMacWidget/          # macOS widget build
```

## Key Modules

### Core Processing Engine

| Module | Purpose |
|--------|---------|
| `wwc_AutoBookmarker.py` | Primary PDF bookmarking engine with date parsing, bookmark extraction, and 12+ date pattern recognition (patterns A-N) |
| `wwc_parser.py` | Generic date/time parser supporting multiple formats |
| `wwc_TOC.py` | Table of Contents generation and chronology writing |
| `tree.py` | Tree data structure management for bookmarks and chronology display |

### GUI Layer

| Module | Purpose |
|--------|---------|
| `Display.py` | Main PDF viewer using Tkinter with page navigation, zoom, annotations |
| `frame_main.py` | wxPython main window with drag-and-drop functionality |
| `CdropLabel.py` | Drag-and-drop label layout for bookmarks, chronology, hyperlinks |

### Entry Point

| Module | Purpose |
|--------|---------|
| `action.py` | Main action dispatcher that processes PDF queue via `externalDrop()` |

## Development Workflow

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run main application (wxPython GUI)
python frame_main.py

# Or via the launcher
python AutoBookmarker.py
```

### Building Executables

```bash
# Windows build
python setupPC.py

# macOS build
python setupMac.py

# Or via PyInstaller directly
./pyinstaller.sh
```

### Primary Workflow
1. User drops PDF file onto wxPython/PyQt6 GUI
2. `action.py` dispatches to core processor via queue
3. `wwc_AutoBookmarker.py` analyzes PDF and extracts bookmarks/dates
4. Results displayed in `Display.py` Tkinter viewer
5. User can edit, merge, paginate, and save enhanced PDF

## Coding Conventions

### File Naming
- Core modules prefixed with `wwc_` (e.g., `wwc_AutoBookmarker.py`)
- Dialog classes suffixed with `Dialog` (e.g., `tocDialog.py`)
- GUI components use descriptive names (e.g., `Display.py`, `RubberBand.py`)

### Import Style
```python
from __future__ import absolute_import
from __future__ import print_function
import standard_library
from third_party import module
import local_module as alias
from local_module import specific_function
```

### Date Pattern Conventions
The codebase uses letter-prefixed patterns (A-N) for date recognition:
- `patA-patJ`: String patterns for various date formats
- `patK-patN`: Compiled regex patterns for complex date/time formats
- See comments in `wwc_AutoBookmarker.py:30-52` for pattern documentation

### Named Tuples
```python
Chunk = collections.namedtuple("chunk", ["txt", "a", "size_chunk", ...])
Bookmark = collections.namedtuple("bookmark", ["txt", "Dt", "pg", "chunk"])
```

### Global State
- `NO_PAGES`, `percentComplete`, `error_list` - Processing state
- `KEY_WORDS`, `WP`, `BOW`, `MONTHS` - Configuration dictionaries

### Class Patterns
- Context managers for PDF operations (`PdfMinerWrapper`)
- Tkinter widget subclasses for custom components
- Class-level ID tracking (`display.next_id`)

## Dependencies

### Primary Libraries
| Library | Purpose |
|---------|---------|
| `pymupdf` (fitz) | Primary PDF manipulation |
| `PyPDF2` | PDF reading and annotation building |
| `pdfminer` | PDF text extraction and parsing |
| `pikepdf` | Advanced PDF manipulation |
| `wxPython` | Main GUI framework |
| `tkinter` | PDF viewer and dialogs |
| `PyQt6` | Alternative GUI support |
| `ocrmypdf` | OCR text recognition |
| `dateparser` | Date parsing |
| `treelib` | Tree structure management |

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Common Development Tasks

### Adding a New Date Pattern
1. Add pattern in `wwc_AutoBookmarker.py` (after line 52)
2. Update pattern matching logic in parsing functions
3. Add test cases for new pattern format

### Adding a New Dialog
1. Create `newDialog.py` following existing dialog patterns
2. Import in `Display.py` or relevant GUI module
3. Add menu/button handler to invoke dialog

### Modifying PDF Processing
1. Core logic is in `wwc_AutoBookmarker.py`
2. Use `fitz` (PyMuPDF) for page manipulation
3. Use `PdfMinerWrapper` for text extraction
4. Bookmark data uses `Bookmark` namedtuple

### Adding UI Elements
1. For wxPython: modify `frame_main.py` or `frame_main_gui.py`
2. For Tkinter viewer: modify `Display.py`
3. Icon assets go in `images/` directory

## Known TODOs in Codebase

- `CdropLabel.py`: Check file download status
- `hyperlinks.py`: Duplicate reference detection, OPML conversion
- `tree.py`: Popup functionality
- `wwc_TOC.py`: Named destination alternatives
- `wwc_page_labels.py`: Alphabetical name sorting
- `wwc_parsebookmark.py`: Enhanced date conversion

## Testing

Run tests with:
```bash
python test.py
```

## Project Metrics

- **Total Python Files:** ~51
- **Total Lines of Code:** ~13,000
- **Largest Modules:** wwc_AutoBookmarker.py, Display.py, wwc_parser.py
- **GUI Frameworks:** 3 (wxPython, PyQt6, Tkinter)
