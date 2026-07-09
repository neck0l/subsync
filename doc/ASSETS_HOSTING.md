# Asset hosting & signing (fork)

SubSync downloads speech models / dictionaries as signed ZIPs listed in an
`assets.json`. Downloads are verified against trusted RSA public keys before
install (`subsync/pubkey.py`).

## Trusted keys (multi-key)
`pubkey.verify()` accepts a signature if **any** `*.pub` next to
`subsync/key.pub` verifies it:
- `subsync/key.pub`  — original upstream key (keeps archived upstream assets working).
- `subsync/fork.pub` — this fork's key (signs new Vosk/Whisper model assets).

The fork **private** key is NOT in the repo. It was generated with a 4096-bit RSA
key and must be kept secret by the maintainer (used only when signing releases).

## Signing a new asset (maintainer)
```python
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
key = RSA.import_key(open('fork_private.pem','rb').read())
data = open('model.zip','rb').read()
sig  = PKCS1_v1_5.new(key).sign(SHA256.new(data))
open('model.zip.sig','wb').write(sig)
```
(See also `assets/scripts/sign.py` for the upstream batch-signing workflow.)

## `assets.json` entry (per model)
```json
{
  "speech/eng-vosk": {
    "type": "zip",
    "url":  "https://<your-host>/vosk-model-small-en-us-0.15.zip",
    "sig":  "https://<your-host>/vosk-model-small-en-us-0.15.zip.sig",
    "version": "1.0.0"
  }
}
```
The list URL is `config.assetsurl` (`subsync/config.py.template`). Point it at the
fork's own hosting to serve new engine models; upstream Sphinx models can still be
pulled from the (still-live) upstream release URL.

## Local model descriptor
For a locally-installed Vosk model, drop `<lang>.vosk.speech` in the assets
`speech/` dir (see `subsync/synchro/speech.py::loadVoskModel`), e.g.:
```json
{ "lang":"eng", "engine":"vosk",
  "vosk": { "model": "./vosk-model-small-en-us-0.15" },
  "version":"1.0.0", "samplerate":"16000", "sampleformat":"S16" }
```
