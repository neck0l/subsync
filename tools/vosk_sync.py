#!/usr/bin/env python3
"""Vosk engine end-to-end test (Segment G verification).

Runs the real synchronization pipeline but forces the speech model to the local
Vosk model, so we can compare Vosk accuracy against the PocketSphinx golden
reference (doc/GOLDEN_REFERENCE.txt) on the same inputs.

Usage:
    py -3.11 tools/vosk_sync.py SUB SUB_LANG REF REF_LANG OUT VOSK_MODEL_DIR [JOBS]
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.add_dll_directory(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subsync
from subsync.synchro import speech


def main():
    sub_path, sub_lang, ref_path, ref_lang, out_path, model_dir = sys.argv[1:7]
    jobs = int(sys.argv[7]) if len(sys.argv) > 7 else 2

    # Force the speech pipeline to use the local Vosk model.
    def fakeLoadSpeechModel(lang):
        return {
            'lang': lang,
            'engine': 'vosk',
            'vosk': {'model': model_dir},
            'samplerate': '16000',
            'sampleformat': 'S16',
            'version': '1.0.0',
        }
    speech.loadSpeechModel = fakeLoadSpeechModel

    sub = {'path': sub_path, 'lang': sub_lang}
    ref = {'path': ref_path, 'lang': ref_lang, 'streamByType': 'audio'}
    out = {'path': out_path}
    options = {} if jobs <= 0 else {'jobsNo': jobs}
    minEffort = os.environ.get('SUBSYNC_MIN_EFFORT')
    if minEffort:
        options['minEffort'] = float(minEffort)

    print('== subsync', subsync.version()[0], '(engine: VOSK) ==')
    print('model:', model_dir, '| jobs:', jobs)

    t0 = time.time()
    result, status = subsync.synchronize(sub, ref, out, offline=True, options=options)
    dt = time.time() - t0

    print('\n---- RESULT ----')
    print('success   :', getattr(result, 'success', None))
    print('path      :', getattr(result, 'path', None))
    print('---- STATUS ----')
    print('correlated:', getattr(status, 'correlated', None))
    print('factor(R) :', getattr(status, 'factor', None))
    print('points    :', getattr(status, 'points', None))
    print('maxChange :', getattr(status, 'maxChange', None))
    formula = getattr(status, 'formula', None)
    if formula is not None:
        print('formula   : ref = %.8f * sub + %.4f' % (formula.a, formula.b))
    print('elapsed(s):', round(dt, 1))


if __name__ == '__main__':
    sys.exit(main())
