from __future__ import annotations

import io
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gdk, Gio, GLib, Graphene, Gtk
from PIL import Image

from . import __version__
from .capture import CaptureCancelled, PortalCapture
from .editor import EditorModel
from .paths import copy_portal_capture


APP_ID = "io.github.snipr.SnipR"
CAPTURE_CHOICES = (
    ("Rectangular region", True),
    ("Full screen", True),
    ("Active window", True),
)


def fit_geometry(image_size: tuple[int, int], canvas_size: tuple[int, int]):
    image_width, image_height = image_size
    canvas_width, canvas_height = canvas_size
    scale = min(canvas_width / image_width, canvas_height / image_height)
    draw_width, draw_height = image_width * scale, image_height * scale
    offset = ((canvas_width - draw_width) / 2, (canvas_height - draw_height) / 2)
    return scale, offset, (draw_width, draw_height)


def image_texture(image: Image.Image) -> Gdk.Texture:
    output = io.BytesIO()
    image.save(output, format="PNG")
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(output.getvalue()))


class ImageCanvas(Gtk.Widget):
    """One snapshot surface for both the fitted image and pointer overlay."""

    def __init__(self, editor: "EditorWindow") -> None:
        super().__init__(hexpand=True, vexpand=True)
        self.editor = editor

    def do_measure(self, _orientation, _for_size):
        return 0, 0, -1, -1

    def do_snapshot(self, snapshot: Gtk.Snapshot) -> None:
        self.editor._snapshot_canvas(snapshot, self.get_width(), self.get_height())


class EditorWindow(Gtk.ApplicationWindow):
    COLORS = ["#000000", "#ffffff", "#ef2929", "#ff7800", "#f6d32d", "#33d17a", "#1c71d8", "#813d9c"]
    CURSORS = {"pen": "pencil", "highlighter": "cell", "eraser": "not-allowed", "crop": "crosshair"}

    def __init__(self, app: Gtk.Application, raw_path: Path) -> None:
        super().__init__(application=app, title=f"SnipR {__version__} — {raw_path.name}")
        self.set_default_size(1000, 720)
        self.raw_path = raw_path
        self.model = EditorModel(Image.open(raw_path))
        self.tool = "pen"
        self.color = (239, 41, 41, 255)
        self.width = 5
        self.points: list[tuple[float, float]] = []
        self.crop_start: tuple[float, float] | None = None
        self.crop_end: tuple[float, float] | None = None
        self.scale = 1.0
        self.offset = (0.0, 0.0)
        self._closing_after_choice = False
        self.texture = image_texture(self.model.image)
        self._build_ui()
        self.connect("close-request", self._on_close_request)

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        toolbar = Gtk.Box(spacing=6)
        toolbar.set_margin_top(8)
        toolbar.set_margin_bottom(8)
        toolbar.set_margin_start(8)
        toolbar.set_margin_end(8)

        for label, tool in (("Pen", "pen"), ("Highlighter", "highlighter"), ("Eraser", "eraser"), ("Crop", "crop")):
            button = Gtk.ToggleButton(label=label)
            button.connect("toggled", self._tool_toggled, tool)
            if tool == "pen":
                button.set_active(True)
            toolbar.append(button)

        color_button = Gtk.ColorButton()
        color_button.set_rgba(Gdk.RGBA(0.94, 0.16, 0.16, 1.0))
        color_button.connect("color-set", self._color_changed)
        toolbar.append(color_button)

        size = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 40, 1)
        size.set_value(self.width)
        size.set_size_request(130, -1)
        size.connect("value-changed", lambda widget: setattr(self, "width", int(widget.get_value())))
        toolbar.append(size)

        for label, callback in (("Undo", self._undo), ("Redo", self._redo), ("Copy", self._copy), ("Save As…", self._save_as)):
            button = Gtk.Button(label=label)
            button.connect("clicked", callback)
            toolbar.append(button)

        root.append(toolbar)
        self.canvas = ImageCanvas(self)
        drag = Gtk.GestureDrag()
        drag.set_button(Gdk.BUTTON_PRIMARY)
        drag.connect("drag-begin", self._drag_begin)
        drag.connect("drag-update", self._drag_update)
        drag.connect("drag-end", self._drag_end)
        self.canvas.add_controller(drag)
        self._update_cursor()
        root.append(self.canvas)

        status = Gtk.Label(label=f"Raw capture saved automatically to {self.raw_path}", xalign=0)
        status.set_margin_start(10)
        status.set_margin_end(10)
        status.set_margin_top(5)
        status.set_margin_bottom(8)
        status.set_ellipsize(3)
        root.append(status)
        self.set_child(root)

    def _tool_toggled(self, button: Gtk.ToggleButton, tool: str) -> None:
        if button.get_active():
            self.tool = tool
            parent = button.get_parent()
            child = parent.get_first_child()
            while child:
                if isinstance(child, Gtk.ToggleButton) and child is not button:
                    child.set_active(False)
                child = child.get_next_sibling()
            self._update_cursor()

    def _update_cursor(self) -> None:
        if hasattr(self, "canvas"):
            self.canvas.set_cursor_from_name(self.CURSORS.get(self.tool, "default"))

    def _color_changed(self, button: Gtk.ColorButton) -> None:
        rgba = button.get_rgba()
        self.color = tuple(round(channel * 255) for channel in (rgba.red, rgba.green, rgba.blue, rgba.alpha))

    def _image_point(self, x: float, y: float) -> tuple[float, float]:
        return ((x - self.offset[0]) / self.scale, (y - self.offset[1]) / self.scale)

    def _drag_begin(self, _gesture: Gtk.GestureDrag, x: float, y: float) -> None:
        point = self._image_point(x, y)
        self.points = [point]
        self.crop_start = point if self.tool == "crop" else None
        self.crop_end = self.crop_start

    def _drag_update(self, gesture: Gtk.GestureDrag, dx: float, dy: float) -> None:
        start = gesture.get_start_point()
        if not start[0]:
            return
        point = self._image_point(start[1] + dx, start[2] + dy)
        if self.tool == "crop":
            self.crop_end = point
        else:
            self.points.append(point)
        self.canvas.queue_draw()

    def _drag_end(self, _gesture: Gtk.GestureDrag, _dx: float, _dy: float) -> None:
        if self.tool == "crop" and self.crop_start and self.crop_end:
            x1, y1 = self.crop_start
            x2, y2 = self.crop_end
            self.model.crop((round(min(x1, x2)), round(min(y1, y2)), round(max(x1, x2)), round(max(y1, y2))))
        elif self.points:
            width = self.width * (3 if self.tool == "highlighter" else 1)
            self.model.stroke(self.points, self.color, width, self.tool)
        self._refresh_canvas()
        self.points = []
        self.crop_start = self.crop_end = None
        self.canvas.queue_draw()

    def _snapshot_canvas(self, snapshot: Gtk.Snapshot, width: int, height: int) -> None:
        image = self.model.image
        if width <= 0 or height <= 0:
            return
        self.scale, self.offset, draw_size = fit_geometry(image.size, (width, height))
        draw_width, draw_height = draw_size
        image_rect = Graphene.Rect()
        image_rect.init(self.offset[0], self.offset[1], draw_width, draw_height)
        snapshot.append_texture(self.texture, image_rect)

        canvas_rect = Graphene.Rect()
        canvas_rect.init(0, 0, width, height)
        cr = snapshot.append_cairo(canvas_rect)
        cr.translate(*self.offset)
        cr.scale(self.scale, self.scale)
        if self.points and self.tool != "crop":
            cr.set_source_rgba(*(channel / 255 for channel in self.color))
            cr.set_line_width(self.width)
            cr.move_to(*self.points[0])
            for point in self.points[1:]:
                cr.line_to(*point)
            cr.stroke()
        if self.crop_start and self.crop_end:
            x1, y1 = self.crop_start
            x2, y2 = self.crop_end
            cr.set_source_rgba(1, 1, 1, 0.9)
            cr.set_line_width(2 / self.scale)
            cr.rectangle(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            cr.stroke()

    def _refresh_canvas(self) -> None:
        self.texture = image_texture(self.model.image)
        self.canvas.queue_draw()

    def _undo(self, _button=None) -> None:
        self.model.undo()
        self._refresh_canvas()
        self.canvas.queue_draw()

    def _redo(self, _button=None) -> None:
        self.model.redo()
        self._refresh_canvas()
        self.canvas.queue_draw()

    def _copy(self, _button=None) -> None:
        self.get_clipboard().set_texture(image_texture(self.model.image))

    def _save_as(self, _button=None, close_after: bool = False) -> None:
        chooser = Gtk.FileChooserNative.new("Save edited screenshot", self, Gtk.FileChooserAction.SAVE, "Save", "Cancel")
        chooser.set_current_name(self.raw_path.stem + "_edited.png")
        image_filter = Gtk.FileFilter()
        image_filter.set_name("PNG images")
        image_filter.add_mime_type("image/png")
        chooser.add_filter(image_filter)

        def response(dialog: Gtk.FileChooserNative, result: int) -> None:
            if result == Gtk.ResponseType.ACCEPT:
                file = dialog.get_file()
                path = Path(file.get_path())
                if path.suffix.lower() != ".png":
                    path = path.with_suffix(".png")
                self.model.save(path)
                self.set_title(f"SnipR {__version__} — {path.name}")
                if close_after:
                    self._closing_after_choice = True
                    self.close()
            dialog.destroy()

        chooser.connect("response", response)
        chooser.show()

    def _on_close_request(self, _window) -> bool:
        if self._closing_after_choice or not self.model.dirty:
            return False
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Save your edited screenshot?",
        )
        dialog.format_secondary_text("The unedited capture is already safe. Unsaved edits will be lost if you discard them.")
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Discard edits", Gtk.ResponseType.REJECT, "Save As…", Gtk.ResponseType.ACCEPT)

        def response(message: Gtk.MessageDialog, result: int) -> None:
            message.destroy()
            if result == Gtk.ResponseType.ACCEPT:
                self._save_as(close_after=True)
            elif result == Gtk.ResponseType.REJECT:
                self._closing_after_choice = True
                self.close()

        dialog.connect("response", response)
        dialog.present()
        return True


class CaptureWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application) -> None:
        super().__init__(application=app, title=f"SnipR {__version__}")
        self.set_default_size(460, 280)
        self.portal = PortalCapture()
        self._build_ui()

    def _build_ui(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Take a screenshot</span>")
        box.append(title)
        help_text = Gtk.Label(label="All modes use Ubuntu’s secure Wayland screenshot picker.")
        help_text.add_css_class("dim-label")
        box.append(help_text)
        grid = Gtk.Grid(column_spacing=10, row_spacing=10, column_homogeneous=True)
        for index, (label, interactive) in enumerate(CAPTURE_CHOICES):
            button = Gtk.Button(label=label)
            button.set_size_request(-1, 50)
            button.connect("clicked", self._capture_clicked, interactive)
            grid.attach(button, index % 2, index // 2, 1, 1)
        box.append(grid)
        delay_box = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        delay_box.append(Gtk.Label(label="Delay:"))
        self.delay = Gtk.SpinButton.new_with_range(0, 10, 1)
        self.delay.set_value(0)
        delay_box.append(self.delay)
        delay_box.append(Gtk.Label(label="seconds"))
        box.append(delay_box)
        self.status = Gtk.Label(label="Raw captures are saved automatically.")
        self.status.set_wrap(True)
        box.append(self.status)
        self.set_child(box)

    def _capture_clicked(self, _button: Gtk.Button, interactive: bool) -> None:
        delay_ms = int(self.delay.get_value()) * 1000
        self.status.set_text("Waiting…" if delay_ms else "Opening screenshot portal…")
        self.set_visible(False)
        GLib.timeout_add(delay_ms or 150, self._begin_capture, interactive)

    def _begin_capture(self, interactive: bool) -> bool:
        self.portal.capture(interactive, self._capture_finished)
        return GLib.SOURCE_REMOVE

    def _capture_finished(self, uri: str | None, error: Exception | None) -> None:
        if error:
            self.set_visible(True)
            if isinstance(error, CaptureCancelled):
                self.status.set_text("Capture cancelled. Choose a mode to try again.")
            else:
                self.status.set_text(f"Screenshot portal error: {error}")
            return
        try:
            raw_path = copy_portal_capture(uri or "")
            editor = EditorWindow(self.get_application(), raw_path)
            editor.present()
            self.destroy()
        except Exception as exc:
            self.set_visible(True)
            self.status.set_text(f"Could not save screenshot: {exc}")


class SnipRApplication(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self) -> None:
        window = self.get_active_window()
        if window is None:
            window = CaptureWindow(self)
        window.present()


def main() -> int:
    return SnipRApplication().run(None)
