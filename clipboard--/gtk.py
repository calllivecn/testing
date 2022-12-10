
import time

import gi

gi.require_version("Gtk", "3.0")
# gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk


clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

clipboard.set_text("测试粘贴板", -1)

# time.sleep(3)

print(clipboard)


