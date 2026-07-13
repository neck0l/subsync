"""Optional post-sync translation of the output subtitle.

After SubSync re-times the subtitle, this can additionally produce a translated
copy in another language (Google via deep-translator, or DeepL). It operates on
a pysubs2 SSAFile (our `Subtitles`), preserving every cue's timing and only
replacing the text. Duplicate lines are translated once; DeepL falls back to
Google on failure. A `translator` callable can be injected for offline tests.
"""

import os
import re
import sys
import copy
import logging

from subsync.data import languages

logger = logging.getLogger(__name__)


# Language names that our ISO tables don't resolve on their own.
_NAME_TO_CODE = {
    'auto': 'auto', 'auto detect': 'auto',
    'english': 'en', 'arabic': 'ar', 'croatian': 'hr', 'korean': 'ko',
    'japanese': 'ja', 'chinese': 'zh-CN', 'french': 'fr', 'german': 'de',
    'spanish': 'es', 'italian': 'it', 'portuguese': 'pt', 'russian': 'ru',
    'turkish': 'tr', 'polish': 'pl', 'dutch': 'nl',
}

_DEEPL_KEY_FILES = ('deepl_auth_key.txt', '.deepl_auth_key')


def googleCode(lang, default='en'):
    """Resolve a subsync language (2/3-letter code or name) to a Google code."""
    if not lang:
        return default
    value = str(lang).strip().lower()
    if value in ('auto', 'auto detect', ''):
        return 'auto'
    info = languages.get(value)
    if info and info.code2:
        return info.code2
    return _NAME_TO_CODE.get(value, value)


def deeplCode(lang, is_target, default='AR'):
    """Resolve a language to a DeepL code (target codes differ from Google)."""
    code = googleCode(lang, default.lower())
    upper = code.upper()
    if upper == 'AUTO':
        return default.upper() if is_target else None
    if upper == 'EN' and is_target:
        return 'EN-US'
    if upper == 'PT' and is_target:
        return 'PT-PT'
    if upper in ('ZH-CN', 'ZH-HANS'):
        return 'ZH-HANS' if is_target else 'ZH'
    if upper in ('ZH-TW', 'ZH-HANT'):
        return 'ZH-HANT' if is_target else 'ZH'
    return upper


# ---------------------------------------------------------------------------
# API-key reading (DeepL): env var first, then a private ignored file.
# ---------------------------------------------------------------------------

def _keyFileCandidates(explicit=None):
    if explicit:
        return [explicit]
    dirs = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    if getattr(sys, 'frozen', False):
        dirs.append(os.path.dirname(os.path.abspath(sys.executable)))
    paths = []
    for d in dirs:
        for name in _DEEPL_KEY_FILES:
            paths.append(os.path.join(d, name))
    return paths


def readDeeplKey(explicit_path=None):
    env = (os.environ.get('DEEPL_AUTH_KEY') or '').strip()
    if env:
        return env
    for path in _keyFileCandidates(explicit_path):
        if path and os.path.isfile(path):
            with open(path, 'r', encoding='utf-8-sig') as fp:
                key = fp.read().strip().lstrip('\ufeff').strip()
            if key:
                return key
    return None


# ---------------------------------------------------------------------------
# Text-batch translators
# ---------------------------------------------------------------------------

def _translateGoogle(texts, source, target, factory=None):
    """Translate unique texts with deep-translator's GoogleTranslator."""
    if not texts:
        return {}
    if factory is None:
        from deep_translator import GoogleTranslator
        factory = GoogleTranslator

    translator = factory(source=googleCode(source, 'auto'),
                         target=googleCode(target, 'en'))
    out = {}
    for i in range(0, len(texts), 40):
        batch = texts[i:i + 40]
        try:
            results = translator.translate_batch(batch)
            for src, res in zip(batch, results):
                out[src] = (res or src).strip()
        except Exception:
            for text in batch:
                try:
                    out[text] = (translator.translate(text) or text).strip()
                except Exception:
                    out[text] = text
    return out


def _translateDeepl(texts, source, target, key, client_factory=None):
    """Translate unique texts with DeepL; fall back to Google on any failure."""
    if not texts:
        return {}
    if client_factory is None:
        import deepl
        client_factory = deepl.DeepLClient if hasattr(deepl, 'DeepLClient') else deepl.Translator

    target_code = deeplCode(target, is_target=True)
    source_code = deeplCode(source, is_target=False)
    try:
        client = client_factory(key)
        out = {}
        for i in range(0, len(texts), 40):
            batch = texts[i:i + 40]
            kwargs = {'target_lang': target_code}
            if source_code:
                kwargs['source_lang'] = source_code
            results = client.translate_text(batch, **kwargs)
            if not isinstance(results, list):
                results = [results]
            for src, res in zip(batch, results):
                out[src] = getattr(res, 'text', str(res)).strip()
        return out
    except Exception as e:
        logger.warning('DeepL translation failed (%s); falling back to Google', e)
        return _translateGoogle(texts, source, target)


# ---------------------------------------------------------------------------
# Subtitle translation (operates on a pysubs2 SSAFile / our Subtitles)
# ---------------------------------------------------------------------------

def translateSubtitles(subtitles, target, source=None, engine='google',
                       translator=None, deepl_key_path=None):
    """Return a translated copy of `subtitles`, preserving all timings.

    Only the plain text of each event is replaced. A `translator` callable
    (str -> str) may be injected to avoid any network access (used by tests).
    """
    result = copy.deepcopy(subtitles)

    plains = []
    for event in result:
        if getattr(event, 'is_comment', False):
            continue
        text = event.plaintext.strip() if event.plaintext else ''
        if text:
            plains.append(text)

    unique = list(dict.fromkeys(plains))
    if not unique:
        return result

    if translator is not None:
        mapping = {}
        for text in unique:
            try:
                mapping[text] = (translator(text) or text).strip()
            except Exception:
                mapping[text] = text
    elif engine == 'deepl':
        key = readDeeplKey(deepl_key_path)
        if not key:
            logger.warning('DeepL key not found; using Google Translate')
            mapping = _translateGoogle(unique, source, target)
        else:
            mapping = _translateDeepl(unique, source, target, key)
    elif engine == 'google':
        mapping = _translateGoogle(unique, source, target)
    else:
        raise ValueError('unsupported translation engine: {}'.format(engine))

    for event in result:
        if getattr(event, 'is_comment', False):
            continue
        text = event.plaintext.strip() if event.plaintext else ''
        if text and text in mapping:
            event.plaintext = mapping[text]

    return result


def translatedOutputPath(path, target):
    """Insert the target language code before the extension: out.srt -> out.ar.srt."""
    root, ext = os.path.splitext(path)
    code = googleCode(target, 'x')
    return '{}.{}{}'.format(root, code, ext)
