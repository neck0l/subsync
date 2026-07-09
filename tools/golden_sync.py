#!/usr/bin/env python3
"""Golden-reference sync harness (Segment O).

Runs subsync's high-level API on a (sub, ref, out) triple and prints the
resulting correlation formula and statistics, so builds/engines can be compared
objectively. Uses offline mode (assumes required assets are already installed).

Usage:
    py -3.11 tools/golden_sync.py SUB SUB_LANG REF REF_LANG OUT [--ref-type audio|sub] [--ref-stream N]
"""
import sys, os, time, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subsync


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sub')
    ap.add_argument('sub_lang')
    ap.add_argument('ref')
    ap.add_argument('ref_lang')
    ap.add_argument('out')
    ap.add_argument('--ref-type', dest='ref_type', default='audio', choices=['audio', 'sub'])
    ap.add_argument('--ref-stream', dest='ref_stream', type=int, default=None)
    args = ap.parse_args()

    sub = {'path': args.sub, 'lang': args.sub_lang}
    ref = {'path': args.ref, 'lang': args.ref_lang}
    if args.ref_stream is not None:
        ref['stream'] = args.ref_stream
    else:
        ref['streamByType'] = args.ref_type
    out = {'path': args.out}

    print('== subsync', subsync.version()[0], '==')
    print('sub:', sub)
    print('ref:', ref)
    print('out:', out)

    t0 = time.time()
    result, status = subsync.synchronize(sub, ref, out, offline=True)
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
        print('formula.a :', formula.a)
        print('formula.b :', formula.b)
        print('formula   : ref = %.8f * sub + %.4f' % (formula.a, formula.b))
    print('elapsed(s):', round(dt, 1))


if __name__ == '__main__':
    sys.exit(main())
