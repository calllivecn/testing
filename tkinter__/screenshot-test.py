#!/usr/bin/env python3
# coding=utf-8
# date 2023-06-18 15:03:19
# author calllivecn <calllivecn@outlook.com>

import dbus
from gi.repository import GLib
import dbus.mainloop.glib


def response_handler(response, result):
    if response == 0:
        print(f'Screenshot file: {result.get("uri")}')
    else:
        print("Failed to get screenshot")


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    my_name = bus.get_connection().get_unique_name()[1:].replace(".", "_")
    response_path = f"/org/freedesktop/portal/desktop/request/{my_name}/my_token"
    bus.add_signal_receiver(
        response_handler,
        dbus_interface="org.freedesktop.portal.Request",
        path=response_path,
    )

    desktop = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    desktop.Screenshot("Screenshot", {"handle_token": "my_token"}, dbus_interface="org.freedesktop.portal.Screenshot")
    loop = GLib.MainLoop()
    loop.run()


if __name__ == "__main__":
    main()
