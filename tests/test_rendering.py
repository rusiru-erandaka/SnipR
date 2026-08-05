import unittest

from PIL import Image

from snipr.ui import fit_geometry, image_texture


class GtkTextureTests(unittest.TestCase):
    def test_pillow_image_becomes_sized_gtk_texture(self):
        texture = image_texture(Image.new("RGBA", (23, 17), "red"))
        self.assertEqual(texture.get_width(), 23)
        self.assertEqual(texture.get_height(), 17)

    def test_fitted_geometry_round_trip_preserves_pointer_position(self):
        scale, offset, draw_size = fit_geometry((941, 877), (1000, 610))
        image_point = (350, 344)
        canvas_point = (
            offset[0] + image_point[0] * scale,
            offset[1] + image_point[1] * scale,
        )
        mapped_back = (
            (canvas_point[0] - offset[0]) / scale,
            (canvas_point[1] - offset[1]) / scale,
        )
        self.assertAlmostEqual(mapped_back[0], image_point[0])
        self.assertAlmostEqual(mapped_back[1], image_point[1])
        self.assertAlmostEqual(draw_size[1], 610)
