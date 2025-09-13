import locale
import os
import platform
import sys
from configparser import MissingSectionHeaderError, NoOptionError, NoSectionError
from pathlib import Path
from typing import Optional, Tuple

# Ensure Kivy Windows runtime dependencies are available before importing Kivy
if platform.system() == "Windows":  # pragma: no cover_linux
    try:
        # These wheels ship the necessary DLLs (SDL2, GLEW, ANGLE)
        from kivy_deps import sdl2, glew, angle  # type: ignore

        # Prefer ANGLE on Windows for broader driver compatibility
        os.environ.setdefault("KIVY_GL_BACKEND", "angle_sdl2")
        os.environ.setdefault("KIVY_WINDOW", "sdl2")

        dep_paths = []
        for m in (sdl2, glew, angle):
            bins = getattr(m, "dep_bins", []) or []
            dep_paths.extend(bins)
            # Fallback: add <pkg_dir>\bin if present
            pkg_dir = os.path.dirname(m.__file__)
            candidate = os.path.join(pkg_dir, "bin")
            if os.path.isdir(candidate):
                dep_paths.append(candidate)

        # Last-resort fallback: recursively search common DLLs inside Briefcase bundle
        # when dep_bins are empty or missing expected DLLs.
        try:
            base_dir = os.path.abspath(os.path.dirname(sys.executable))
        except Exception:
            base_dir = None
        dll_names = {"SDL2.dll", "libEGL.dll", "libGLESv2.dll", "glew32.dll", "glew32s.dll"}
        if base_dir and (not dep_paths or os.environ.get("MYDEVOIRS_FORCE_DLL_SCAN")):
            for root, dirs, files in os.walk(base_dir):
                # limit depth to avoid scanning user profile; Briefcase bundle paths are short
                rel = os.path.relpath(root, base_dir)
                if rel.count(os.sep) > 3:
                    continue
                if any(name in files for name in dll_names):
                    dep_paths.append(root)

        # Python 3.8+: add DLL directories explicitly
        add_dll_dir = getattr(os, "add_dll_directory", None)
        for p in dep_paths:
            try:
                if add_dll_dir:
                    add_dll_dir(p)
                else:
                    os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            except Exception:
                pass

        # Optional debug: verify presence of DLL folders
        if os.environ.get("MYDEVOIRS_DEBUG_WINDOWS_DEPS"):
            try:
                # Avoid buffering: write directly to stdout
                sys.stdout.write("[MyDevoirs] Kivy deps paths:\n")
                for p in dep_paths:
                    try:
                        exists = os.path.isdir(p)
                        sys.stdout.write(f"  - {p}  => {'OK' if exists else 'MISSING'}\n")
                    except Exception as e:
                        sys.stdout.write(f"  - {p}  => error: {e}\n")
                sys.stdout.flush()
            except Exception:
                pass

        # Ensure pywin32 runtime DLLs are discoverable (win32file, pywintypes, pythoncom)
        try:
            import win32api  # type: ignore
            import pywintypes  # type: ignore

            pywin_candidates = set()
            # From installed modules
            for mod in (win32api, pywintypes):
                mod_dir = os.path.dirname(getattr(mod, "__file__", ""))
                if mod_dir:
                    pywin_candidates.add(mod_dir)
                    pywin_candidates.add(os.path.join(mod_dir, "..", "pywin32_system32"))
            # From Briefcase bundle layout
            if base_dir:
                pywin_candidates.add(os.path.join(base_dir, "app_packages", "pywin32_system32"))
                pywin_candidates.add(os.path.join(base_dir, "app_packages", "win32"))
                pywin_candidates.add(os.path.join(base_dir, "app_packages"))

            for p in list(pywin_candidates):
                ap = os.path.abspath(p)
                if os.path.isdir(ap):
                    try:
                        if add_dll_dir:
                            add_dll_dir(ap)
                        else:
                            os.environ["PATH"] = ap + os.pathsep + os.environ.get("PATH", "")
                    except Exception:
                        pass

            # Try importing win32file now so Kivy's filechooser check succeeds
            try:  # type: ignore
                import win32file  # noqa: F401
            except Exception:
                pass

            if os.environ.get("MYDEVOIRS_DEBUG_WINDOWS_DEPS"):
                try:
                    sys.stdout.write("[MyDevoirs] pywin32 paths:\n")
                    for p in pywin_candidates:
                        sys.stdout.write(f"  - {os.path.abspath(p)}  => {'OK' if os.path.isdir(p) else 'MISSING'}\n")
                    sys.stdout.flush()
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        # If deps are missing, Kivy may still run in dev env; packaged app will fail early otherwise
        pass

from kivy.config import ConfigParser
from mydevoirs.app import MyDevoirsApp
from mydevoirs.avertissement import BackupAncienneDB


def set_locale_fr() -> None:
    if platform.system() == "Linux":
        locale.setlocale(locale.LC_ALL, "fr_FR.utf8")  # pragma: no cover_win
    else:
        locale.setlocale(locale.LC_ALL, "french")  # pragma: no cover_linux


def setup_kivy() -> bool:

    from kivy.config import Config

    Config.set("input", "mouse", "mouse,multitouch_on_demand")
    Config.set(
        "kivy", "window_icon", Path(__file__).parent / "data" / "icons" / "logo.png"
    )
    set_locale_fr()

    return True


def reapply_version(app: MyDevoirsApp) -> Tuple[int, str]:
    """
    Verifie les differents version précendentes
    :param app: L'instance en cours
    :return:
        0: le fichier n'existe pas
        1: la version a du être ajoutée
        2: la version existe == version en cours
        3: la version existe < version en cours
        4: la version existe > version en cours
    """
    cf_file = app.get_application_config()
    file = Path(cf_file)
    return_value = 0
    file_version = None
    if file.is_file():  # pragma: no branch
        config = ConfigParser()
        try:
            config.read(cf_file)
            file_version = config.get("aide", "version")
        except NoSectionError:
            return_value = 1
        except NoOptionError:
            return_value = 1
    from mydevoirs.constants import VERSION # not import constant to early because of theme 

    if file_version is not None:
        if file_version < VERSION:
            return_value = 3
        elif file_version > VERSION:
            return_value = 4
        else:
            return_value = 2

    return return_value, file_version


def get_backup_ddb_path(app: MyDevoirsApp, state: int) -> Tuple[Path, Optional[Path]]:
    path = Path(app.load_config()["ddb"]["path"])
    new_path = None
    if path.is_file() and state < 2:
        # on ne crée pas de nouvelle db  qui sera crée + tard dans load_config de app
        new_path = path.parent / "mydevoirs_sauvegarde_ancienne_version.ddb"
    return path, new_path


def main():  # pragma: no cover_all
    # covered in check_executable.py
    setup_kivy()
    app = MyDevoirsApp()
    state, file_version = reapply_version(app)
    old_path, backup_path = get_backup_ddb_path(app, state)
    if backup_path:
        app.avertissement = BackupAncienneDB(old_path, backup_path)
    else:
        app.init_database()

    app.run()
