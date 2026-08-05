# SnipLite

SnipLite is a small native GTK 4 screenshot editor for Wayland desktops. It uses
the standard desktop screenshot portal, so it works without bypassing Wayland's
security model.

## Features

- Rectangular region, full-screen, active-window/system-picker, and delayed capture
- Automatic preservation of every raw capture in the XDG Pictures/Screenshots folder
- Pen, highlighter, eraser, crop, undo, redo, clipboard, and manual PNG saving
- Save/discard/cancel prompt when closing with unsaved edits

On Wayland, applications cannot inspect other windows directly. Region and window
capture therefore open Ubuntu's trusted system picker; the exact choices shown are
controlled by the installed desktop portal.

## Run from source

Install `python3`, `python3-gi`, `gir1.2-gtk-4.0`, `python3-pil`,
`xdg-desktop-portal`, and the portal backend for your desktop. Then run:

```sh
python3 -m sniplite
```

## Build the Debian package

The repository includes a dependency-free package builder (apart from the standard
`dpkg-deb` command):

```sh
./build-deb.sh
```

The resulting `.deb` is written to `dist/`. Install it with:

```sh
sudo apt install ./dist/sniplite_0.1.2-1_all.deb
```

## Tests

```sh
python3 -m unittest discover -v
```
