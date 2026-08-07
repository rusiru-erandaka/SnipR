# SnipR

SnipR is a lightweight native GTK 4 screenshot and annotation tool for Ubuntu
Wayland sessions. It automatically preserves the original capture and lets you
draw, highlight, erase, crop, undo, redo, copy, and manually save the edited image.

## Easy installation

1. Download or open the SnipR project folder.
2. Open a terminal inside that folder.
3. Install the included package:

```sh
sudo apt install ./dist/snipr_0.3.0-1_all.deb
```

Ubuntu installs any required GTK, Pillow, and desktop-portal dependencies
automatically. After installation, open **SnipR** from the application menu or run:

```sh
snipr
```

If an older SnipLite process is still open, close it before starting SnipR:

```sh
pkill -f '^python3 -m sniplite' || true
```

The SnipR package replaces the former `sniplite` package during installation.

## Uninstall

```sh
sudo apt remove snipr
```

Removing the application does not delete screenshots.

## Where captures are saved

Every unedited capture is automatically saved to the standard XDG screenshots
folder, normally:

```text
~/Pictures/Screenshots
```

Edited images are saved only when you select **Save As**. Closing with unsaved
edits shows Save, Discard, and Cancel choices.

## Cropping

Select **Crop**, then drag over the part of the screenshot you want to keep. The
outside area is dimmed and the selection remains active. Drag a corner or edge
handle to resize it, or drag inside the selection to move it. Choose **Apply Crop**
to finalize the crop or **Cancel Crop** to leave the image unchanged.

## Capture modes

- Rectangular region
- Full screen
- Active window through Ubuntu's secure picker
- Capture delay from 0 to 10 seconds

Wayland prevents applications from reading other windows directly. Region and
window capture therefore use Ubuntu's trusted desktop screenshot portal. All
three buttons open this picker for reliable behavior across Ubuntu versions. For
a full-screen capture, choose the display/full-screen option in the picker and
confirm the capture. The portal controls the exact UI displayed on each desktop.

## Run from source

Install the runtime dependencies:

```sh
sudo apt install python3 python3-gi gir1.2-gtk-4.0 python3-pil \
  xdg-desktop-portal xdg-desktop-portal-gnome
```

Then run:

```sh
python3 -m snipr
```

## Build a new Debian package

```sh
./build-deb.sh
```

The package is created in `dist/`.

## Run tests

```sh
python3 -m unittest discover -v
```
