"""Пути GTK для собранной Windows-программы. Подключается PyInstaller до импорта окна."""

import os
import sys

if getattr(sys, "frozen", False) and sys.platform == "win32":
    base = os.path.dirname(sys.executable)
    os.environ["PATH"] = base + os.pathsep + os.environ.get("PATH", "")
    os.environ["GI_TYPELIB_PATH"] = os.path.join(base, "lib", "girepository-1.0")
    os.environ["XDG_DATA_DIRS"] = os.path.join(base, "share")
    os.environ["GTK_EXE_PREFIX"] = base
    os.environ["GTK_DATA_PREFIX"] = base
    loaders = os.path.join(base, "lib", "gdk-pixbuf-2.0", "2.10.0", "loaders.cache")
    if os.path.exists(loaders):
        os.environ["GDK_PIXBUF_MODULE_FILE"] = loaders
        os.environ["GDK_PIXBUF_MODULEDIR"] = os.path.dirname(loaders)
