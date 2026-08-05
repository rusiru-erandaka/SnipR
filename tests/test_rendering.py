import unittest

from PIL import Image

from sniplite.ui import image_texture


class GtkTextureTests(unittest.TestCase):
    def test_pillow_image_becomes_sized_gtk_texture(self):
        texture = image_texture(Image.new("RGBA", (23, 17), "red"))
        self.assertEqual(texture.get_width(), 23)
        self.assertEqual(texture.get_height(), 17)
