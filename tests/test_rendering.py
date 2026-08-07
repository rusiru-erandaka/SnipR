import unittest

from PIL import Image

from snipr.ui import (
    crop_handles,
    crop_hit_target,
    fit_geometry,
    image_texture,
    move_crop_box,
    normalize_crop_box,
    resize_crop_box,
)


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

    def test_crop_box_normalizes_reverse_drag(self):
        self.assertEqual(normalize_crop_box((90, 70), (10, 20)), (10, 20, 90, 70))

    def test_crop_has_four_corner_and_four_edge_handles(self):
        handles = crop_handles((10, 20, 90, 80))
        self.assertEqual(set(handles), {"nw", "n", "ne", "e", "se", "s", "sw", "w"})
        self.assertEqual(handles["e"], (90, 50))

    def test_crop_hit_detects_handle_before_inside_move(self):
        box = (10, 20, 90, 80)
        self.assertEqual(crop_hit_target(box, (11, 21), 4), "nw")
        self.assertEqual(crop_hit_target(box, (50, 50), 4), "move")
        self.assertIsNone(crop_hit_target(box, (100, 100), 4))

    def test_resize_and_move_stay_inside_image(self):
        resized = resize_crop_box((10, 20, 90, 80), "se", (150, 140), (120, 100))
        self.assertEqual(resized, (10, 20, 120, 100))
        moved = move_crop_box((10, 20, 90, 80), (100, 100), (120, 100))
        self.assertEqual(moved, (40, 40, 120, 100))
