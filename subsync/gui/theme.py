# #165(c): dark theme for wxWidgets 3.2 on Windows.
#
# wxWidgets 3.2 has no native dark-mode switch (that arrived in 3.3), so we:
#   1. enable the Windows process dark app-mode (undocumented uxtheme ordinals),
#   2. darken each top-level window's title bar via DWM,
#   3. recolor controls recursively - setting BOTH background and foreground per
#      control type so text is light on dark (the previous version only set a dark
#      background, leaving dark text -> unreadable).

import wx
import sys

_WIN = sys.platform == 'win32'

# palette
FG       = wx.Colour(230, 230, 230)   # light text
BG       = wx.Colour(32, 32, 32)      # window / panel background
CTRL_BG  = wx.Colour(52, 52, 56)      # input controls
BORDERV  = wx.Colour(70, 70, 74)

_APP_DARK_INITED = False


def _initWindowsDarkApp():
    """Enable process-wide dark mode using the (undocumented) uxtheme ordinals.
    Best-effort: silently ignored if unavailable."""
    global _APP_DARK_INITED
    if not _WIN or _APP_DARK_INITED:
        return
    try:
        import ctypes
        uxtheme = ctypes.windll.uxtheme
        # SetPreferredAppMode is ordinal #135 (Win10 1903+); 1 = AllowDark, 2 = ForceDark
        try:
            SetPreferredAppMode = uxtheme[135]
            SetPreferredAppMode(2)
        except Exception:
            # older builds: AllowDarkModeForApp is ordinal #135 too / #133
            try:
                uxtheme[133](True)
            except Exception:
                pass
        try:
            uxtheme[136]()  # FlushMenuThemes
        except Exception:
            pass
        _APP_DARK_INITED = True
    except Exception:
        pass


def _darkTitleBar(hwnd):
    if not _WIN or not hwnd:
        return
    try:
        import ctypes
        val = ctypes.c_int(1)
        for attr in (20, 19):  # 20 = Win10 1809+, 19 = older insider builds
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attr, ctypes.byref(val), ctypes.sizeof(val))
            except Exception:
                pass
    except Exception:
        pass


def isDarkEnabled():
    try:
        from subsync.settings import settings
        mode = settings().get('darkMode') or 'light'
    except Exception:
        mode = 'light'
    if mode == 'dark':
        return True
    if mode == 'system':
        try:
            return wx.SystemSettings.GetAppearance().IsDark()
        except Exception:
            return False
    return False


def enable():
    """One-time process setup (call once at app start)."""
    if isDarkEnabled():
        _initWindowsDarkApp()
        _installShowHooks()


_HOOKS_INSTALLED = False


def _installShowHooks():
    """Auto-apply the dark theme to every dialog/frame right before it is shown,
    so dynamically-built content is covered and no per-dialog edits are needed."""
    global _HOOKS_INSTALLED
    if _HOOKS_INSTALLED:
        return
    _HOOKS_INSTALLED = True

    _origDialogShowModal = wx.Dialog.ShowModal
    def _dialogShowModal(self):
        try:
            apply(self)
        except Exception:
            pass
        return _origDialogShowModal(self)
    wx.Dialog.ShowModal = _dialogShowModal

    _origDialogShow = wx.Dialog.Show
    def _dialogShow(self, show=True):
        if show:
            try:
                apply(self)
            except Exception:
                pass
        return _origDialogShow(self, show)
    wx.Dialog.Show = _dialogShow

    if hasattr(wx.Frame, 'ShowModal'):
        _origFrameShowModal = wx.Frame.ShowModal
        def _frameShowModal(self):
            try:
                apply(self)
            except Exception:
                pass
            return _origFrameShowModal(self)
        wx.Frame.ShowModal = _frameShowModal


def apply(top):
    """Apply dark appearance to a top-level window and all descendants."""
    if not isDarkEnabled():
        return
    try:
        _darkTitleBar(top.GetHandle())
    except Exception:
        pass
    _style(top)
    try:
        top.Refresh()
    except Exception:
        pass


def _style(win):
    try:
        # Input-like controls: dark field + light text.
        if isinstance(win, (wx.TextCtrl, wx.SpinCtrl, wx.Choice, wx.ComboBox,
                            wx.ListBox, wx.ListCtrl, wx.CheckListBox)):
            win.SetBackgroundColour(CTRL_BG)
            win.SetForegroundColour(FG)
        elif isinstance(win, wx.Button):
            win.SetBackgroundColour(CTRL_BG)
            win.SetForegroundColour(FG)
        # Labels / checkboxes / radios: keep parent bg, just lighten text.
        elif isinstance(win, (wx.StaticText, wx.CheckBox, wx.RadioButton,
                              wx.StaticBox, wx.RadioBox, wx.Gauge, wx.StaticLine,
                              wx.Slider)):
            win.SetForegroundColour(FG)
            _maybeBg(win, BG)
            # StaticBox draws a light etched border/label on Windows; dim it so it
            # blends into the dark instead of a bright frame.
            if isinstance(win, wx.StaticBox):
                try:
                    win.SetBackgroundColour(BG)
                    win.SetForegroundColour(wx.Colour(150, 150, 150))
                except Exception:
                    pass
        # Containers.
        elif isinstance(win, (wx.Frame, wx.Dialog, wx.Panel, wx.ScrolledWindow,
                              wx.Notebook, wx.Choicebook)):
            win.SetBackgroundColour(BG)
            win.SetForegroundColour(FG)
        else:
            win.SetForegroundColour(FG)
            _maybeBg(win, BG)
    except Exception:
        pass

    for child in win.GetChildren():
        _style(child)


def _maybeBg(win, colour):
    # StaticText etc. render better with the container colour behind them.
    try:
        win.SetBackgroundColour(colour)
    except Exception:
        pass
