import tempfile
import unittest
from pathlib import Path

from PIL import Image

from sniplite.editor import EditorModel
from sniplite.paths import unique_capture_path


class EditorModelTests(unittest.TestCase):
    def setUp(self):
        self.model = EditorModel(Image.new("RGB", (100, 80), "white"))

    def test_pen_undo_and_redo(self):
        self.model.stroke([(10, 10), (90, 70)], (255, 0, 0, 255), 5, "pen")
        changed = self.model.image.tobytes()
        self.assertTrue(self.model.dirty)
        self.model.undo()
        self.assertEqual(self.model.image.getpixel((50, 40)), (255, 255, 255, 255))
        self.model.redo()
        self.assertEqual(self.model.image.tobytes(), changed)

    def test_crop(self):
        self.model.crop((10, 10, 60, 50))
        self.assertEqual(self.model.image.size, (50, 40))

    def test_eraser_restores_pixels_under_annotation(self):
        self.model.stroke([(10, 10), (90, 70)], (255, 0, 0, 255), 9, "pen")
        self.assertNotEqual(self.model.image.getpixel((50, 40)), (255, 255, 255, 255))
        self.model.stroke([(40, 30), (60, 50)], (0, 0, 0, 255), 12, "eraser")
        self.assertEqual(self.model.image.getpixel((50, 40)), (255, 255, 255, 255))

    def test_save_marks_clean(self):
        self.model.stroke([(10, 10)], (0, 0, 0, 255), 3, "pen")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "edited.png"
            self.model.save(target)
            self.assertTrue(target.exists())
            self.assertFalse(self.model.dirty)

    def test_unique_capture_path(self):
        with tempfile.TemporaryDirectory() as directory:
            first = unique_capture_path(Path(directory))
            first.touch()
            second = unique_capture_path(Path(directory))
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
