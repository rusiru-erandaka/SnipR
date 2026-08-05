from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageDraw


Point = tuple[float, float]


class EditorModel:
    """Image editing state kept independent of GTK for simple, reliable tests."""

    def __init__(self, image: Image.Image) -> None:
        self.original = image.convert("RGBA")
        self.background = self.original.copy()
        self.image = self.original.copy()
        self.undo_stack: list[tuple[Image.Image, Image.Image]] = []
        self.redo_stack: list[tuple[Image.Image, Image.Image]] = []
        self.dirty = False

    def _commit(self, image: Image.Image, background: Image.Image | None = None) -> None:
        if image.size == self.image.size and image.tobytes() == self.image.tobytes():
            return
        self.undo_stack.append((self.image.copy(), self.background.copy()))
        self.image = image.convert("RGBA")
        if background is not None:
            self.background = background.convert("RGBA")
        self.redo_stack.clear()
        self.dirty = True

    def stroke(
        self,
        points: Iterable[Point],
        color: tuple[int, int, int, int],
        width: int,
        tool: str,
    ) -> None:
        points = list(points)
        if not points:
            return
        before = self.image.copy()
        if tool == "eraser":
            mask = Image.new("L", before.size, 0)
            draw = ImageDraw.Draw(mask)
            if len(points) == 1:
                x, y = points[0]
                draw.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=255)
            else:
                draw.line(points, fill=255, width=width, joint="curve")
            before.paste(self.background, (0, 0), mask)
            self._commit(before)
            return

        overlay = Image.new("RGBA", before.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        rgba = color
        if tool == "highlighter":
            rgba = (*color[:3], 90)
        if len(points) == 1:
            x, y = points[0]
            draw.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=rgba)
        else:
            draw.line(points, fill=rgba, width=width, joint="curve")
        self._commit(Image.alpha_composite(before, overlay))

    def crop(self, box: tuple[int, int, int, int]) -> None:
        left, top, right, bottom = box
        left = max(0, min(left, self.image.width - 1))
        top = max(0, min(top, self.image.height - 1))
        right = max(left + 1, min(right, self.image.width))
        bottom = max(top + 1, min(bottom, self.image.height))
        if right - left > 2 and bottom - top > 2:
            box = (left, top, right, bottom)
            self._commit(self.image.crop(box), self.background.crop(box))

    def undo(self) -> None:
        if not self.undo_stack:
            return
        self.redo_stack.append((self.image.copy(), self.background.copy()))
        self.image, self.background = self.undo_stack.pop()
        self.dirty = self.image.size != self.original.size or self.image.tobytes() != self.original.tobytes()

    def redo(self) -> None:
        if not self.redo_stack:
            return
        self.undo_stack.append((self.image.copy(), self.background.copy()))
        self.image, self.background = self.redo_stack.pop()
        self.dirty = True

    def save(self, path: Path) -> None:
        self.image.convert("RGB").save(path, "PNG")
        self.dirty = False
