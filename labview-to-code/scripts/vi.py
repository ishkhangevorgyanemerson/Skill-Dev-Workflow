import importlib
import os
import shutil
import subprocess
import sys
import time
import win32com
import win32com.client
import win32com.client.dynamic
import win32com.client.gencache
from os.path import basename, join, abspath
from pathlib import Path

_LV_PATH_FILE = Path(__file__).parent.parent / "labview_path.txt"
_LABVIEW_EXECUTABLE = Path(_LV_PATH_FILE.read_text(encoding="utf-8").strip())


def _clear_win32com_gen_py_cache() -> None:
    """Clear pywin32 generated COM wrappers that may become corrupted."""
    cache_paths: set[Path] = set()

    # Common runtime cache location used by pywin32.
    temp_dir = os.environ.get("Temp")
    if temp_dir:
        cache_paths.add(Path(temp_dir) / "gen_py")

    # Per-interpreter/site-packages cache location used in some setups.
    win32com_pkg_dir = Path(win32com.client.__file__).resolve().parent.parent
    cache_paths.add(win32com_pkg_dir / "gen_py")

    # gencache runtime location (if available).
    gen_path = getattr(win32com, "__gen_path__", None)
    if gen_path:
        cache_paths.add(Path(gen_path))

    for cache_path in cache_paths:
        if cache_path.exists():
            shutil.rmtree(cache_path, ignore_errors=True)


def _reset_win32com_gencache() -> None:
    """Clear on-disk and in-process pywin32 caches so Dispatch can rebuild."""
    _clear_win32com_gen_py_cache()

    stale_modules = [
        module_name
        for module_name in sys.modules
        if module_name == "win32com.gen_py" or module_name.startswith("win32com.gen_py.")
    ]
    for module_name in stale_modules:
        sys.modules.pop(module_name, None)

    importlib.invalidate_caches()
    win32com.client.gencache.is_readonly = False
    win32com.client.gencache.Rebuild()


def _is_pywin32_cache_error(exc: Exception) -> bool:
    message = str(exc)
    return "CLSIDTo" in message or "gen_py" in message


def _dispatch_application(activex_server: str) -> tuple[object, bool]:
    prog_id = activex_server + ".Application"

    try:
        return win32com.client.Dispatch(prog_id), False
    except AttributeError as exc:
        if not _is_pywin32_cache_error(exc):
            raise

    _reset_win32com_gencache()

    try:
        return win32com.client.Dispatch(prog_id), False
    except AttributeError as exc:
        if not _is_pywin32_cache_error(exc):
            raise
        return win32com.client.dynamic.Dispatch(prog_id), True


class VI:
    def __init__(self, vi_path: Path, activex_server='LabVIEW'):
        for _ in range(5):
            if self.launched(_LABVIEW_EXECUTABLE):
                break
            subprocess.Popen(_LABVIEW_EXECUTABLE)
            time.sleep(3)

        # pywin32 can occasionally leave corrupted generated wrappers in
        # gen_py. Reset and rebuild the cache first, then fall back to dynamic
        # dispatch so LabVIEW automation can still proceed.
        LabVIEW, used_dynamic_dispatch = _dispatch_application(activex_server)

        if activex_server == 'LabVIEW':
            vi_path = abspath(vi_path)
            if not used_dynamic_dispatch:
                LabVIEW = win32com.client.CastTo(LabVIEW, '_Application')
        else:
            vi_path = join(LabVIEW.ApplicationDirectory,
                           basename(_LABVIEW_EXECUTABLE), vi_path)
        self.VI = LabVIEW.GetVIReference(vi_path)
        if hasattr(self.VI, '_FlagAsMethod'):
            self.VI._FlagAsMethod('Run')
            self.VI._FlagAsMethod('Abort')
            self.VI._FlagAsMethod('CenterFrontPanel')
            self.VI._FlagAsMethod('OpenFrontPanel')
            self.VI._FlagAsMethod('GetPanelImage')

        if activex_server == 'LabVIEW':
            # 1 - open the front panel visible
            # 3 - open the front panel hidden
            # refer to https://www.ni.com/docs/en-US/bundle/labview-api-ref/page/properties-and-methods/activex/enumerations/fp-state.html
            self.OpenFrontPanel(False, 3)

    def running(self):
        return self.VI.ExecState == 2

    def __getattr__(self, attr):
        return getattr(self.VI, attr)

    def __getitem__(self, control_or_indicater):
        return self.VI.GetControlValue(control_or_indicater)

    def __setitem__(self, control, value):
        return self.VI.SetControlValue(control, value)

    @staticmethod
    def launched(executable='LabVIEW.exe'):
        wmi = win32com.client.GetObject('winmgmts:')
        query = wmi.ExecQuery('select Name from Win32_Process'
                              ' where Name = "' + basename(executable) + '"')
        return len(query) > 0
