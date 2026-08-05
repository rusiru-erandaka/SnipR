import unittest

from snipr.capture import portal_options
from snipr.ui import CAPTURE_CHOICES


class CaptureRoutingTests(unittest.TestCase):
    def test_every_button_opens_the_interactive_wayland_picker(self):
        self.assertEqual([label for label, _interactive in CAPTURE_CHOICES], [
            "Rectangular region",
            "Full screen",
            "Active window",
        ])
        self.assertTrue(all(interactive for _label, interactive in CAPTURE_CHOICES))

    def test_portal_options_preserve_interactive_request(self):
        options = portal_options(True, "snipr_test")
        self.assertTrue(options["interactive"].unpack())
        self.assertEqual(options["handle_token"].unpack(), "snipr_test")


if __name__ == "__main__":
    unittest.main()
