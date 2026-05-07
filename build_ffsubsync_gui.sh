#!/usr/bin/env bash
# ----------------------------------------------------------------------
# build_ffsubsync_gui.sh
# Full‑proof pipeline that builds a one‑file PyInstaller binary and
# packages it into a portable AppImage.
#
# Run this script on the GitHub‑Actions runner (Ubuntu 22.04) or any
# recent Ubuntu/Debian host.
# ----------------------------------------------------------------------

set -euo pipefail

# ---------- 0.  Variables ----------
TARGET_ARCH=x86_64                     # use i386 for 32‑bit old Debian
APPIMAGE_NAME="ffsubsync-gui-$(date +%Y%m%d)-${TARGET_ARCH}.AppImage"

# ---------- 1.  Create a clean virtual environment ----------
python3 -m venv .venv
source .venv/bin/activate

# ---------- 2.  Install build‑time Python tools ----------
pip install -r requirements.txt

# ---------- 3.  Install system packages needed for building ----------
# (the runner already has most of these, but we install explicitly)
sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential git \
    libfreetype6-dev zlib1g-dev libgl1-mesa-dev libglu1-mesa-dev \
    libxcb1-dev libx11-dev libxext-dev libxrender-dev libxrandr-dev \
    libsm-dev libice-dev libxft-dev libxinerama-dev \
    squashfs-tools fuse liblzma-dev \
    # for the test container later
    xvfb

# ---------- 4.  Pull the original ffsubsync source ----------
# The script will live in the folder “ffsubsync/ffsubsync.py”.
SRC_DIR="ffsubsync"
if [[ ! -d "$SRC_DIR" ]]; then
    git clone https://github.com/smacke/ffsubsync "$SRC_DIR"
fi
# Keep only the main script (the rest is optional)
if [[ ! -f "$SRC_DIR/ffsubsync.py" ]]; then
    # The upstream repo may have renamed the file – adjust as needed.
    echo "⚠️ Expected $SRC_DIR/ffsubsync.py but it does not exist.  Cloning again..."
    rm -rf "$SRC_DIR"
    git clone https://github.com/smacke/ffsubsync "$SRC_DIR"
fi

# ---------- 5.  Freeze the GUI binary with PyInstaller ----------
# We add the original ffsubsync script as data so it becomes part of
# the AppImage.  The syntax is "<src>:<dest>" – the dest part is the
# path **inside the extracted data directory**.
pyinstaller \
    --onefile \
    --noconsole \
    --add-data "ffsubsync/ffsubsync.py:ffsubsync" \
    --arch ${TARGET_ARCH} \
    gui/ffsync_gui.py

BINARY_PATH="$(pwd)/dist/ffsubsync_gui"
if [[ ! -x "$BINARY_PATH" ]]; then
    echo "❌ PyInstaller failed – see errors above."
    exit 1
fi
echo "✅ PyInstaller binary created at $BINARY_PATH"

# ---------- 6.  Create the AppDir layout ----------
APPDIR="$(pwd)/AppDir"
mkdir -p "$APPDIR"/usr/bin "$APPDIR"/usr/share/applications

# Copy the frozen binary
cp "$BINARY_PATH" "$APPDIR"/usr/bin/ffsubsync-gui

# Minimal launcher – AppImage expects an executable called “AppRun” at the root
cat <<'EOF' > "$APPDIR"/AppRun
#!/usr/bin/env bash
# AppRun simply forwards to the bundled binary.
exec "$(dirname "$0")/usr/bin/ffsubsync-gui" "$@"
EOF
chmod +x "$APPDIR"/AppRun

# Optional desktop entry (makes the icon appear in menus)
cat <<'EOF' > "$APPDIR"/usr/share/applications/ffsubsync-gui.desktop
[Desktop Entry]
Name=FFSubSync GUI
Comment=Synchronise subtitles with a graphical front‑end
Exec=/AppRun
Icon=ffsubsync
Terminal=false
Type=Application
Categories=AudioVideo;
EOF

# Tiny config file for appimage‑builder – you can extend it later
cat <<'YAML' > "$APPDIR"/appimage-builder.yml
AppDir:
  Name: ffsync-gui
  Version: "0.1.0"
  Description: GUI wrapper for ffsubsync, packaged as a portable AppImage.
  Executable: ffsync-gui
  Files:
    - Path: usr/bin/ffsubsync-gui
    - Path: AppRun
    - Path: usr/share/applications/ffsubsync-gui.desktop
YAML

# ---------- 7.  Build the AppImage ----------
# appimage‑builder automatically pulls in all needed shared libraries
# (X11, GLibc, libSM, …) thanks to the “--runtime-libs” flag.
appimage-builder \
    --config "$APPDIR"/appimage-builder.yml \
    --out-path "$PWD" \
    --runtime-libs

# ---------- 8.  Locate the produced AppImage ----------
APPMAP=$(ls "${APPIMAGE_NAME}" 2>/dev/null || true)
if [[ -z "$APPMAP" ]]; then
    echo "❌ AppImage not produced – check the logs for missing libraries."
    exit 1
fi
echo "✅ AppImage built successfully:"
ls -lh "$APPMAP"

# (Optional) keep a copy with a stable name for downstream jobs:
echo "$APPMAP" > appimage_path.txt
