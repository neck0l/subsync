"""App translations using a simple dict loaded from .po files.
No gettext, no .mo files, no install/uninstall — just a plain Python dict
assigned to builtins._ for fast, predictable, debuggable lookups.
"""

import os, re, builtins, importlib, logging
from subsync import config

logger = logging.getLogger(__name__)

_TRANSLATIONS = {}  # msgid -> msgstr (English -> translated)
_DEFAULT_LANG = 'en'
initialized = False


def init():
    """Called once at module import. Installs the English _() into builtins."""
    global initialized
    _install(loadDict('en'))
    initialized = True


def loadDict(lang):
    """Parse a .po file and return {msgid: msgstr} dict."""
    if lang == 'en':
        return {}
    path = os.path.join(config.localedir, lang, 'LC_MESSAGES', 'messages.po')
    if not os.path.isfile(path):
        logger.warning('no .po file for language %s: %s', lang, path)
        return {}
    d = {}
    with open(path, 'r', encoding='utf-8') as fp:
        text = fp.read()
    # Parse simple msgid / msgstr pairs
    for block in text.split('\n\n'):
        m_id = re.search(r'msgid\s*"(.+?)"\s*\nmsgstr\s*"(.+?)"', block, re.DOTALL)
        if m_id and m_id.group(1) and m_id.group(2) and m_id.group(2) != m_id.group(1):
            # Unescape the msgstr
            s = m_id.group(2)
            s = s.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            d[m_id.group(1)] = s
    return d


def _install(d):
    """Replace builtins._ with a dict-based lookup that falls back to msgid."""
    global _TRANSLATIONS
    _TRANSLATIONS = d
    builtins.__dict__['_'] = lambda msg: _TRANSLATIONS.get(msg, msg)


def setLanguage(language):
    """Switch all app text to the given language (2-letter code)."""
    import locale
    try:
        lang = language or _DEFAULT_LANG
        if lang is None:
            lang = locale.getdefaultlocale()[0].split('_', 1)[0]
        if lang == 'en':
            _install({})
        else:
            d = loadDict(lang)
            _install(d)

        global initialized
        initialized = True

        # Reload language-dependent data modules
        import subsync.data.languages
        importlib.reload(subsync.data.languages)
        import subsync.data.descriptions
        importlib.reload(subsync.data.descriptions)

    except Exception as e:
        logger.warning('translation language setup failed, %r', e, exc_info=False)


def listLanguages():
    try:
        langs = os.listdir(config.localedir)
    except:
        langs = []
    langs = [l for l in langs if os.path.isdir(os.path.join(config.localedir, l))]
    if 'en' not in langs:
        langs.append('en')
    return langs


def _(msg):
    try:
        gettext = builtins.__dict__.get('_', None)
        if gettext is not None:
            return gettext(msg)
    except Exception:
        pass
    return msg
