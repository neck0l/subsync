"""Optional AI polish of translated subtitle output.

After translation, an LLM can review the source + translated subtitle pair,
cleaning up wording / removing junk / fixing OCR artifacts. Multiple
providers: OpenRouter, OpenAI, Anthropic, Groq. Keys are read from
git-ignored files or environment variables; unavailable providers are
skipped gracefully with a log warning.
"""

import os
import re
import json
import sys
import logging

logger = logging.getLogger(__name__)


# Provider detection from key prefix.
def _detectProvider(key):
    key = (key or '').strip()
    l = key.lower()
    if l.startswith('sk-ant-'): return 'anthropic'
    if l.startswith('sk-or-'):  return 'openrouter'
    if l.startswith('gsk_') or l.startswith('gsk-'): return 'groq'
    if l.startswith('sk-'):     return 'openai'
    return 'unknown'

# Key files: env var first, then a private file next to the app.
_KEY_FILES = ('ai_provider_keys.json', '.ai_provider_keys.json')
def _readKeys():
    """Return list of {provider, key} dicts from env or config files."""
    keys = []
    env = (os.environ.get('AI_PROVIDER_KEYS') or '').strip()
    if env:
        # comma / newline separated simple list
        for k in re.split(r'[,\n]+', env):
            k = k.strip()
            if k:
                keys.append({'provider': _detectProvider(k), 'key': k})
        if keys:
            return keys

    dirs = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    if getattr(sys, 'frozen', False):
        dirs.append(os.path.dirname(os.path.abspath(sys.executable)))
    seen = set()
    for d in dirs:
        d = os.path.abspath(d)
        if d in seen:
            continue
        seen.add(d)
        for name in _KEY_FILES:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                with open(p, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                for rec in data.get('keys', []):
                    prov = rec.get('provider') or _detectProvider(rec['key'])
                    keys.append({'provider': prov, 'key': rec['key']})
                return keys

    # legacy: openrouter key in env or file
    or_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if or_key:
        return [{'provider': 'openrouter', 'key': or_key}]
    for d in dirs:
        for name in ('openrouter_api_key.txt', '.openrouter_api_key'):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                try:
                    with open(p, 'r', encoding='utf-8-sig') as f:
                        k = f.read().strip().lstrip('\ufeff').strip()
                except Exception:
                    k = ''
                if k:
                    return [{'provider': 'openrouter', 'key': k}]
    return []


# ---------------------------------------------------------------------------
# Provider-specific chat-completions calls
# ---------------------------------------------------------------------------

_OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
_OPENAI_URL = 'https://api.openai.com/v1/chat/completions'
_ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
_GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'


SYSTEM_PROMPT = (
    'You are a professional subtitle editor. Compare the source and translated '
    'subtitle text. Clean up translation errors, improve natural wording, remove '
    'OCR junk, and for Arabic output remove leftover Latin letters unless they '
    'are a proper name. Preserve timing — only return corrected target-language '
    'text or a delete flag for pure garbage.'
)


def _callOpenAI(provider, key, model, payload, request_post=None):
    if request_post is None:
        import requests
        request_post = requests.post
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    if provider == 'anthropic':
        r = request_post(_ANTHROPIC_URL, headers={
            'x-api-key': key, 'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'}, json=payload, timeout=120)
        data = r.json()
        blocks = data.get('content', [])
        return '\n'.join(b.get('text', '') for b in blocks if isinstance(b, dict))
    if provider == 'groq':
        url = _GROQ_URL
    elif provider == 'openai':
        url = _OPENAI_URL
    else:
        url = _OPENROUTER_URL
    r = request_post(url, headers=headers, json=payload, timeout=120)
    if provider == 'openrouter' and r.status_code >= 400:
        # some models block response_format -> retry without it
        if 'response_format' in str(payload) and (
                'response_format' in r.text.lower() or 'guardrail' in r.text.lower()):
            payload2 = dict(payload)
            payload2.pop('response_format', None)
            r = request_post(url, headers=headers, json=payload2, timeout=120)
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']


def _cleanResponse(raw):
    """Strip code fences + extract JSON object from model output."""
    text = (raw or '').strip()
    if text.startswith('```'):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines).strip()
    s = text.find('{')
    e = text.rfind('}')
    if s != -1 and e != -1 and e > s:
        text = text[s:e + 1]
    return json.loads(text)


def polishCues(sourceCues, targetCues,
               provider='openrouter', model=None,
               request_post=None):
    """Return a polished list of cue texts (same length as targetCues).

    sourceCues / targetCues are lists of plain strings (the text of each subtitle
    line), in order.
    """
    if not targetCues:
        return list(targetCues)

    keys = [k for k in _readKeys() if k['provider'] == provider]
    if not keys:
        logger.warning('no AI key for provider=%s; skipping polish', provider)
        return list(targetCues)

    model = model or ('openai/gpt-oss-120b:free' if provider == 'openrouter'
                       else 'gpt-3.5-turbo')

    items = []
    for i, (src, tgt) in enumerate(zip(sourceCues, targetCues)):
        if not tgt.strip():
            items.append({'index': i, 'source': src or '', 'translation': ''})
        else:
            items.append({'index': i, 'source': src or '', 'translation': tgt})

    user = {'task': 'Polish translated subtitles.',
            'source_language': 'source', 'target_language': 'target',
            'rules': ['Return only JSON: {"items": [{"index":0,"text":"fixed","delete":false}]}'],
            'items': items}

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': json.dumps(user, ensure_ascii=False)},
        ],
        'temperature': 0.1,
        'max_tokens': 6000,
    }
    if provider in ('openrouter', 'openai'):
        payload['response_format'] = {'type': 'json_object'}

    errors = []
    for cred in keys:
        try:
            if provider == 'openrouter':
                headers = {'HTTP-Referer': 'https://subsync.local',
                           'X-OpenRouter-Title': 'SubSync'}
                resp = _callOpenAI(provider, cred['key'], model, payload, request_post=request_post)
            else:
                resp = _callOpenAI(provider, cred['key'], model, payload, request_post=request_post)
            parsed = _cleanResponse(resp)
            result = list(targetCues)  # copy
            for item in parsed.get('items', []):
                idx = int(item.get('index', -1))
                if 0 <= idx < len(result):
                    if item.get('delete'):
                        result[idx] = ''
                    elif item.get('text'):
                        result[idx] = str(item['text']).strip()
            return result
        except Exception as e:
            errors.append(str(e))
            continue

    logger.warning('AI polish failed (all keys): %s', ' | '.join(errors))
    return list(targetCues)
