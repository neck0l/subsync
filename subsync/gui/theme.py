import wx

# #165(c): best-effort dark theme. wxWidgets 3.2 has no native dark-mode switch
# (that arrived in 3.3), so we apply a dark palette recursively. This is opt-in
# (Settings -> darkMode), default 'light', because manual theming on Windows is
# imperfect for some native controls.

DARK_BG   = wx.Colour(45, 45, 48)
DARK_PANEL= wx.Colour(37, 37, 38)
DARK_FG   = wx.Colour(220, 220, 220)


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


def apply(window):
    """Apply the dark palette to a top-level window and its children, if enabled."""
    if not isDarkEnabled():
        return
    _applyDark(window)
    try:
        window.Refresh()
    except Exception:
        pass


def _applyDark(win):
    try:
        win.SetBackgroundColour(DARK_BG)
        win.SetForegroundColour(DARK_FG)
    except Exception:
        pass
    for child in win.GetChildren():
        _applyDark(child)
