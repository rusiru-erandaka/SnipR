from __future__ import annotations

import secrets
from collections.abc import Callable

from gi.repository import Gio, GLib


CaptureCallback = Callable[[str | None, Exception | None], None]


class PortalCapture:
    """Wayland-safe screenshot capture through xdg-desktop-portal."""

    BUS = "org.freedesktop.portal.Desktop"
    PATH = "/org/freedesktop/portal/desktop"
    SCREENSHOT_IFACE = "org.freedesktop.portal.Screenshot"
    REQUEST_IFACE = "org.freedesktop.portal.Request"

    def __init__(self) -> None:
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self._subscriptions: set[int] = set()

    def capture(self, interactive: bool, callback: CaptureCallback) -> None:
        token = "sniplite_" + secrets.token_hex(8)
        options = {
            "interactive": GLib.Variant("b", interactive),
            "handle_token": GLib.Variant("s", token),
        }
        parameters = GLib.Variant("(sa{sv})", ("", options))

        def request_ready(connection: Gio.DBusConnection, result: Gio.AsyncResult) -> None:
            try:
                reply = connection.call_finish(result)
                request_path = reply.unpack()[0]
            except Exception as exc:  # portal errors are surfaced in the UI
                callback(None, exc)
                return

            subscription_id = 0

            def response_received(
                _connection: Gio.DBusConnection,
                _sender: str,
                _path: str,
                _interface: str,
                _signal: str,
                parameters: GLib.Variant,
                _user_data=None,
            ) -> None:
                code, results = parameters.unpack()
                self.connection.signal_unsubscribe(subscription_id)
                self._subscriptions.discard(subscription_id)
                if code != 0:
                    callback(None, RuntimeError("Screenshot capture was cancelled"))
                    return
                uri = results.get("uri")
                if isinstance(uri, GLib.Variant):
                    uri = uri.unpack()
                if not uri:
                    callback(None, RuntimeError("The screenshot portal returned no image"))
                    return
                callback(str(uri), None)

            subscription_id = self.connection.signal_subscribe(
                self.BUS,
                self.REQUEST_IFACE,
                "Response",
                request_path,
                None,
                Gio.DBusSignalFlags.NONE,
                response_received,
            )
            self._subscriptions.add(subscription_id)

        self.connection.call(
            self.BUS,
            self.PATH,
            self.SCREENSHOT_IFACE,
            "Screenshot",
            parameters,
            GLib.VariantType("(o)"),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            request_ready,
        )
