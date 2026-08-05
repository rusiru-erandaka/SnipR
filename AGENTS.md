# SnipR agent guide

## Purpose

SnipR is a lightweight Ubuntu Wayland screenshot editor. It captures through
`xdg-desktop-portal`, immediately copies the raw PNG into the user's XDG
`Pictures/Screenshots` directory, and opens a GTK 4 editor. Edited output is never
silently written over the raw capture.

Current application/package version: `0.2.0-1`.

## Technology and runtime requirements

- Python 3.10 or newer
- PyGObject with GTK 4 (`python3-gi`, `gir1.2-gtk-4.0`)
- Pillow (`python3-pil`)
- `xdg-desktop-portal` and an Ubuntu-compatible portal backend
- Wayland only; do not add X11 screen-scraping APIs
- No network access or service is required at runtime

Keep the dependency set small. Prefer GTK/GIO/Pillow functionality already
available from Ubuntu packages over new third-party libraries.

## Repository map

- `snipr/ui.py`: GTK application, capture window, editor, unified image canvas,
  pointer mapping, tool cursors, save dialog, and dirty-close prompt
- `snipr/capture.py`: asynchronous `org.freedesktop.portal.Screenshot` D-Bus client
- `snipr/editor.py`: Pillow-based editing model and undo/redo history
- `snipr/paths.py`: XDG Pictures lookup, unique filenames, and portal-file copying
- `snipr/__main__.py`: `python3 -m snipr` entry point
- `tests/`: model, texture, and coordinate-mapping tests
- `data/`: launcher, icon, executable wrapper, and direct `.deb` control metadata
- `debian/`: conventional Debian source-package metadata
- `build-deb.sh`: dependency-free local binary-package builder
- `SNIPR.md`: user installation and usage guide

## Capture and editing flow

1. `CaptureWindow` requests a full-screen or interactive portal screenshot after
   the selected delay.
2. The portal returns a file URI. `copy_portal_capture()` copies it to a unique
   `Screenshot_YYYY-MM-DD_HH-MM-SS.png` path.
3. `EditorWindow` loads that path into `EditorModel` and a GDK texture.
4. `ImageCanvas.do_snapshot()` draws the image and live annotation overlay using
   one shared fit rectangle. Pointer coordinates must use the same `scale` and
   `offset`; never introduce a separately scaled `Gtk.Picture` overlay.
5. Completed edits update the Pillow model and replace the canvas texture.
6. Save As writes a separate PNG. Closing a dirty editor must offer Save,
   Discard, and Cancel. Closing a clean editor exits normally.

## Important behavior and constraints

- The raw capture must be saved before opening the editor.
- Never overwrite or delete the raw capture during editing or uninstalling.
- Region and active-window buttons both use the interactive portal because the
  Wayland portal, not the application, owns secure window/region selection.
- Keep pen, highlighter, eraser, and crop pointer mapping exact at every aspect
  ratio and window size.
- Eraser restores pixels from the model's current uncensored background layer;
  it must not paint a solid color over annotations.
- Maintain tool-specific cursors and keep the canvas cursor synchronized with
  the selected tool.
- UI work belongs on the GTK main loop. Portal completion uses async GIO calls.
- User-visible branding is `SnipR`; package, command, and Python module are
  lowercase `snipr`; application ID is `io.github.snipr.SnipR`.

## Development commands

Run from source:

```sh
python3 -m snipr
```

Compile-check and test:

```sh
python3 -m compileall -q snipr tests
python3 -m unittest discover -v
```

Build and inspect the package:

```sh
./build-deb.sh
dpkg-deb --info dist/snipr_0.2.0-1_all.deb
dpkg-deb --contents dist/snipr_0.2.0-1_all.deb
desktop-file-validate data/io.github.snipr.SnipR.desktop
```

Install the local build:

```sh
sudo apt install ./dist/snipr_0.2.0-1_all.deb
```

## Release checklist

When changing the version, update all of these together:

1. `snipr/__init__.py`
2. `pyproject.toml`
3. `data/deb-control`
4. output filename in `build-deb.sh`
5. newest entry in `debian/changelog`
6. package filenames in `SNIPR.md` and this guide

Then run the full tests, rebuild the `.deb`, validate the desktop file, extract
the package into a temporary directory, and verify that `import snipr` succeeds
from its installed `dist-packages` path.

## Testing expectations

Add or update tests for pure editing behavior and coordinate calculations. The
tool environment may not have access to the user's Wayland display or session
D-Bus, so a successful headless test does not replace a real capture-and-draw
smoke test on Ubuntu. For visual bugs, inspect the exact raw PNG first to separate
portal/copy problems from rendering problems.
