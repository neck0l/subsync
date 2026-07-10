"""#102: Windows taskbar progress bar via the ITaskbarList3 COM interface.

wxPython 4.2 / wxWidgets 3.2 doesn't expose the taskbar button, so this uses
ctypes COM directly. Everything is wrapped defensively: on any failure (non
-Windows, COM error, etc.) it becomes a silent no-op and never affects the app.
"""
import sys

_WIN = sys.platform == 'win32'

# TBPFLAG
TBPF_NOPROGRESS    = 0
TBPF_INDETERMINATE = 1
TBPF_NORMAL        = 2
TBPF_ERROR         = 4
TBPF_PAUSED        = 8


class TaskbarProgress:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        self._itbl = None
        self._vtbl = None
        if not _WIN:
            return
        try:
            import ctypes
            from ctypes import byref, POINTER, c_void_p

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", ctypes.c_ulong),
                            ("Data2", ctypes.c_ushort),
                            ("Data3", ctypes.c_ushort),
                            ("Data4", ctypes.c_ubyte * 8)]

            def _guid(l, w1, w2, b):
                g = GUID()
                g.Data1 = l; g.Data2 = w1; g.Data3 = w2
                for i in range(8):
                    g.Data4[i] = b[i]
                return g

            CLSID_TaskbarList = _guid(0x56FDF344, 0xFD6D, 0x11d0,
                    (0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90))
            IID_ITaskbarList3 = _guid(0xEA1AFB91, 0x9E28, 0x4B86,
                    (0x90, 0xE9, 0x9E, 0x9F, 0x8A, 0x5E, 0xEF, 0xAF))

            ole32 = ctypes.oledll.ole32
            try:
                ole32.CoInitialize(None)
            except Exception:
                pass  # already initialised on this thread

            ptr = c_void_p()
            CLSCTX_INPROC_SERVER = 1
            ole32.CoCreateInstance(byref(CLSID_TaskbarList), None,
                    CLSCTX_INPROC_SERVER, byref(IID_ITaskbarList3), byref(ptr))
            self._itbl = ptr
            self._vtbl = ctypes.cast(ptr, POINTER(POINTER(c_void_p)))[0]
            self._call(3)  # HrInit()
        except Exception:
            self._itbl = None

    def _call(self, index, argtypes=(), args=()):
        from ctypes import c_void_p, HRESULT, WINFUNCTYPE
        func = self._vtbl[index]
        proto = WINFUNCTYPE(HRESULT, c_void_p, *argtypes)
        return proto(func)(self._itbl, *args)

    def set(self, fraction):
        if not self._itbl:
            return
        try:
            import ctypes
            from ctypes import wintypes, c_ulonglong
            frac = max(0.0, min(1.0, float(fraction)))
            self._call(10, (wintypes.HWND, ctypes.c_int),
                    (self.hwnd, TBPF_NORMAL))               # SetProgressState
            self._call(9, (wintypes.HWND, c_ulonglong, c_ulonglong),
                    (self.hwnd, int(frac * 1000), 1000))     # SetProgressValue
        except Exception:
            pass

    def clear(self):
        if not self._itbl:
            return
        try:
            from ctypes import wintypes
            self._call(10, (wintypes.HWND, __import__('ctypes').c_int),
                    (self.hwnd, TBPF_NOPROGRESS))
        except Exception:
            pass
