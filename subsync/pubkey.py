import os
import glob
from subsync import config

# Segment K: support verifying downloaded-asset signatures against MULTIPLE
# public keys. The archived upstream assets are signed with the original
# 'key.pub'; this fork signs its own (Vosk/Whisper) model assets with an
# additional 'fork.pub'. Any '*.pub' placed next to key.pub in the data dir is
# trusted. A signature is accepted if ANY trusted key verifies it.

_pubkeys_crypto = None
_pubkeys_cryptography = None


def _keyPaths():
    paths = []
    if config.keypath and os.path.isfile(config.keypath):
        paths.append(config.keypath)
    keydir = os.path.dirname(config.keypath) if config.keypath else config.datadir
    for p in sorted(glob.glob(os.path.join(keydir, '*.pub'))):
        if p not in paths:
            paths.append(p)
    return paths


def verify_cryptography(hash, sig):
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding, utils

    global _pubkeys_cryptography
    if _pubkeys_cryptography is None:
        _pubkeys_cryptography = []
        for kp in _keyPaths():
            with open(kp, 'rb') as fp:
                _pubkeys_cryptography.append(
                        serialization.load_pem_public_key(fp.read(), backend=default_backend()))

    lastErr = None
    for key in _pubkeys_cryptography:
        try:
            key.verify(sig, hash.digest(), padding.PKCS1v15(),
                    utils.Prehashed(hashes.SHA256()))
            return
        except Exception as e:
            lastErr = e
    raise lastErr or Exception('no trusted public keys found')


def verify_crypto(hash, sig):
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5

    global _pubkeys_crypto
    if _pubkeys_crypto is None:
        _pubkeys_crypto = []
        for kp in _keyPaths():
            with open(kp, 'rb') as fp:
                _pubkeys_crypto.append(RSA.importKey(fp.read()))

    for key in _pubkeys_crypto:
        verifier = PKCS1_v1_5.new(key)
        if verifier.verify(hash, sig):
            return
    raise Exception('signature does not match any trusted public key')


try:
    from Crypto.Hash import SHA256
    verify = verify_crypto
    sha256 = SHA256.new

except ImportError:
    import hashlib
    verify = verify_cryptography
    sha256 = hashlib.sha256
