# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Define the path to frontend dist
# We assume we are running pyinstaller from the 'Backend' directory,
# so Frontend is at ../Frontend
frontend_dist = os.path.join('..', 'Frontend', 'dist')
if not os.path.exists(frontend_dist):
    # Fallback/Check
    print(f"WARNING: Frontend dist not found at {frontend_dist}. Please run 'npm run build' in Frontend first.")

# Datas: (Source, Destination in bundle)
# We map ../Frontend/dist to 'static' inside the bundle (_MEIPASS/static)
datas = [
    (frontend_dist, 'static'),
    # Add other data files if needed (e.g. templates, db migrations, etc.)
    # ('atherops.db', '.') # Optionally bundle a default DB? Probably not.
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'engineio.async_drivers.asgi', # If using socketio/engineio
    # Add other hidden imports as discovered
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
    'tiktoken_ext.plugin',
]

a = Analysis(
    ['run_packaged.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AtherOps',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Set to False for windowed mode (no terminal), but True is better for debugging/server logs initially
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None # Add icon here later if available
)
