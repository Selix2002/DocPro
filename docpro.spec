# -*- mode: python ; coding: utf-8 -*-
# DocPro — PyInstaller spec (onedir, Windows 11 x64)
#
# Build:
#   pip install pyinstaller>=6.11
#   pyinstaller docpro.spec
#
# Output: dist/DocPro/DocPro.exe  (+ support files in the same folder)
#
# BEFORE BUILDING:
#   - If you use Gmail: place credentials.json in ~/.docpro/credentials.json
#     (it will be bundled automatically; users can also drop it there post-install)
#   - Optionally place a docpro.ico icon at assets/docpro.ico
# ---------------------------------------------------------------------------

from pathlib import Path

ROOT     = Path(SPECPATH)                                   # project root (where this .spec lives)
BACK_SRC = ROOT / "backend"  / "src"
FRONT_SRC = ROOT / "frontend" / "src"

# ---------------------------------------------------------------------------
# 1. DATA FILES
# ---------------------------------------------------------------------------

datas = []

# -- Jinja2 PDF templates (WeasyPrint reads them at render time) -------------
datas += [
    (str(BACK_SRC / "docpro_backend" / "templates"), "docpro_backend/templates"),
]

# -- WeasyPrint internal CSS defaults + ICC color profile --------------------
#    weasyprint/css/*.css  and  weasyprint/pdf/sRGB2014.icc
#    These are non-Python files that WeasyPrint accesses with importlib.resources.
from PyInstaller.utils.hooks import collect_data_files
datas += collect_data_files("weasyprint", include_py_files=False)

# -- Alembic migration scripts (run at app startup via _run_migrations()) ----
#    Layout in bundle:
#      _MEIPASS/alembic.ini
#      _MEIPASS/alembic/env.py
#      _MEIPASS/alembic/versions/<revision>.py  (×5)
datas += [
    (str(ROOT / "backend" / "alembic.ini"),                 "."),
    (str(ROOT / "backend" / "alembic" / "env.py"),          "alembic"),
    (str(ROOT / "backend" / "alembic" / "versions"),        "alembic/versions"),
]

# -- Frontend SVG resources --------------------------------------------------
resources_dir = FRONT_SRC / "docpro_frontend" / "resources"
if resources_dir.exists():
    datas += [(str(resources_dir), "docpro_frontend/resources")]

# -- Gmail OAuth credentials (optional — bundled only if found) --------------
#    In frozen mode gmail_service.py looks for credentials.json at sys._MEIPASS.
#    Users who set up Gmail AFTER install should place credentials.json at:
#      %APPDATA%\DocPro\credentials.json  (the app will check ~/.docpro/ too)
_credentials_src = Path.home() / ".docpro" / "credentials.json"
if _credentials_src.exists():
    datas += [(str(_credentials_src), ".")]

# -- GTK3 DLLs (required by WeasyPrint for PDF rendering) -------------------
#    WeasyPrint uses GObject/GLib/Cairo/Pango via ctypes at runtime.
#    We bundle the DLLs from the GTK3 runtime installation so users don't
#    need to install GTK separately.
import shutil, os as _os

_GTK_CANDIDATES = [
    Path("C:/Program Files/GTK3-Runtime Win64/bin"),
    Path("C:/GTK/bin"),
    Path("C:/msys64/mingw64/bin"),
]

# Also search PATH
for _p in _os.environ.get("PATH", "").split(";"):
    _candidate = Path(_p.strip())
    if _candidate.exists() and any(_candidate.glob("libgobject*.dll")):
        _GTK_CANDIDATES.insert(0, _candidate)
        break

_GTK_BIN = None
for _c in _GTK_CANDIDATES:
    if _c.exists() and any(_c.glob("libgobject*.dll")):
        _GTK_BIN = _c
        break

if _GTK_BIN:
    print(f"[spec] Bundling GTK3 DLLs from: {_GTK_BIN}")
    _GTK_DLLS = [
        "libgobject-2.0-0.dll",
        "libglib-2.0-0.dll",
        "libgio-2.0-0.dll",
        "libgmodule-2.0-0.dll",
        "libgthread-2.0-0.dll",
        "libcairo-2.dll",
        "libcairo-gobject-2.dll",
        "libpango-1.0-0.dll",
        "libpangocairo-1.0-0.dll",
        "libpangoft2-1.0-0.dll",
        "libpangowin32-1.0-0.dll",
        "libgdk_pixbuf-2.0-0.dll",
        "libffi-8.dll",
        "libffi-7.dll",
        "libintl-8.dll",
        "libharfbuzz-0.dll",
        "libfontconfig-1.dll",
        "libfreetype-6.dll",
        "libpixman-1-0.dll",
        "libpng16-16.dll",
        "zlib1.dll",
        "libbrotlidec.dll",
        "libbrotlicommon.dll",
        "libexpat-1.dll",
        "libiconv-2.dll",
        "libpcre2-8-0.dll",
    ]
    _gtk_binaries = []
    for _dll in _GTK_DLLS:
        _dll_path = _GTK_BIN / _dll
        if _dll_path.exists():
            _gtk_binaries.append((str(_dll_path), "."))
else:
    print("[spec] WARNING: GTK3 not found — PDF preview will fail at runtime.")
    print("[spec] Install GTK3: winget install tschoonj.GTK3RuntimeWin64")
    _gtk_binaries = []

# ---------------------------------------------------------------------------
# 2. HIDDEN IMPORTS
#    PyInstaller misses modules that are imported dynamically (via strings,
#    conditional imports, or plugin-discovery patterns).
# ---------------------------------------------------------------------------

hiddenimports = [
    # Standard library modules loaded dynamically or by external scripts
    "logging.config",
    "logging.handlers",

    # SQLAlchemy — dialect loaded by name at runtime
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "sqlalchemy.pool",

    # Alembic runtime
    "alembic",
    "alembic.config",
    "alembic.command",
    "alembic.runtime.migration",
    "alembic.runtime.environment",
    "alembic.operations",
    "alembic.operations.ops",
    "alembic.script",
    "alembic.script.revision",

    # Cryptography (Fernet + hazmat backend)
    "cryptography.fernet",
    "cryptography.hazmat.backends.openssl",
    "cryptography.hazmat.primitives.kdf.pbkdf2",
    "cryptography.hazmat.primitives.ciphers",

    # Google API + OAuth2
    "google.auth",
    "google.auth.transport.requests",
    "google.auth.credentials",
    "google_auth_oauthlib",
    "google_auth_oauthlib.flow",
    "googleapiclient",
    "googleapiclient.discovery",
    "googleapiclient.errors",
    "googleapiclient.http",

    # Groq AI SDK
    "groq",
    "groq._client",

    # WeasyPrint rendering stack
    "weasyprint",
    "weasyprint.css",
    "weasyprint.document",
    "weasyprint.html",
    "weasyprint.images",
    "pydyf",
    "tinycss2",
    "cssselect2",
    "zopfli",
    "brotli",

    # PDF extraction (future phases)
    "pdfplumber",
    "fitz",               # PyMuPDF

    # PySide6 Qt modules used at runtime
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtPrintSupport",

    # Jinja2 extensions (accessed by name)
    "jinja2",
    "jinja2.ext",
    "jinja2.loaders",

    # Backend workspace package (all submodules)
    "docpro_backend",
    "docpro_backend.db",
    "docpro_backend.db.engine",
    "docpro_backend.db.session",
    "docpro_backend.schema",
    "docpro_backend.schema.config",
    "docpro_backend.schema.config.clients",
    "docpro_backend.schema.config.company_profile",
    "docpro_backend.schema.config.settings",
    "docpro_backend.schema.documents",
    "docpro_backend.schema.documents.documents",
    "docpro_backend.schema.documents.document_versions",
    "docpro_backend.schema.documents.section_templates",
    "docpro_backend.schema.quotes",
    "docpro_backend.schema.quotes.quotes",
    "docpro_backend.schema.reports",
    "docpro_backend.schema.reports.reports",
    "docpro_backend.schema.mail",
    "docpro_backend.schema.mail.send_log",
    "docpro_backend.repositories",
    "docpro_backend.services",
    "docpro_backend.dtos",
]

# ---------------------------------------------------------------------------
# 3. EXCLUDES (reduce bundle size — ~200 MB saved)
# ---------------------------------------------------------------------------

excludes = [
    "hupper",           # dev-only auto-reloader
    "tkinter",
    "_tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "IPython",
    "notebook",
    "pytest",
    "setuptools",
    "wheel",
    "pip",
    "pygments",         # not used at runtime
]

# ---------------------------------------------------------------------------
# 4. ANALYSIS
# ---------------------------------------------------------------------------

a = Analysis(
    [str(FRONT_SRC / "docpro_frontend" / "main.py")],
    pathex=[
        str(BACK_SRC),    # makes  docpro_backend  importable
        str(FRONT_SRC),   # makes  docpro_frontend importable
    ],
    binaries=_gtk_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

# ---------------------------------------------------------------------------
# 5. EXE + COLLECT  (onedir — dist/DocPro/DocPro.exe)
# ---------------------------------------------------------------------------

_icon = str(ROOT / "assets" / "docpro.ico")

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DocPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon if Path(_icon).exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        # Don't UPX-compress Qt DLLs — they break on some Windows versions
        "Qt6*.dll",
        "PySide6*.pyd",
    ],
    name="DocPro",
)
