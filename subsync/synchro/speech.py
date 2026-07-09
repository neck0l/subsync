import gizmo
import os, json
from subsync import assets
from subsync import config
from subsync import error
from subsync.translations import _

import logging
logger = logging.getLogger(__name__)


def loadSpeechModel(lang, engine=None):
    if engine is None:
        try:
            from subsync.settings import settings
            engine = settings().get('speechEngine') or 'sphinx'
        except Exception:
            engine = 'sphinx'

    logger.info('loading speech recognition model for language %s (engine=%s)',
            lang, engine)

    if engine == 'vosk':
        model = loadVoskModel(lang)
        if model is not None:
            logger.debug('vosk model ready: %s', model)
            return model
        logger.warning('no Vosk model for language %s, falling back to sphinx', lang)

    if engine == 'whisper':
        model = loadWhisperModel(lang)
        if model is not None:
            logger.debug('whisper model ready: %s', model)
            return model
        logger.warning('no Whisper model for language %s, falling back to sphinx', lang)

    asset = assets.getAsset('speech', [lang])
    if asset.localVersion():
        model = asset.readSpeechModel()
        logger.debug('model ready: %s', model)
        return model

    raise error.Error(_('There is no speech recognition model for language {}')
            .format(lang)).add('language', lang)


def loadVoskModel(lang):
    """Load a Vosk model descriptor (<lang>.vosk.speech) from the assets dir.

    This is kept separate from the (PocketSphinx) '<lang>.speech' asset so that
    the classic installed application is never affected by fork-only files.
    """
    path = os.path.join(config.assetdir, 'speech', lang + '.vosk.speech')
    if not os.path.isfile(path):
        return None

    with open(path, encoding='utf8') as fp:
        model = json.load(fp)

    model['engine'] = 'vosk'

    dirname = os.path.abspath(os.path.dirname(path))
    vosk = model.get('vosk')
    if isinstance(vosk, dict):
        mdl = vosk.get('model')
        if mdl and mdl.startswith('./'):
            vosk['model'] = os.path.join(dirname, *mdl.split('/')[1:])

    return model


def loadWhisperModel(lang):
    """Load a Whisper model descriptor (<lang>.whisper.speech) from the assets dir."""
    path = os.path.join(config.assetdir, 'speech', lang + '.whisper.speech')
    if not os.path.isfile(path):
        return None

    with open(path, encoding='utf8') as fp:
        model = json.load(fp)

    model['engine'] = 'whisper'
    model.setdefault('sampleformat', 'FLT')
    model.setdefault('samplerate', '16000')

    dirname = os.path.abspath(os.path.dirname(path))
    whisper = model.get('whisper')
    if isinstance(whisper, dict):
        mdl = whisper.get('model')
        if mdl and mdl.startswith('./'):
            whisper['model'] = os.path.join(dirname, *mdl.split('/')[1:])

    return model


def createSpeechRec(model):
    engine = model.get('engine', 'sphinx')

    if engine == 'vosk':
        if not hasattr(gizmo, 'VoskSpeechRecognition'):
            raise error.Error(_('This build has no Vosk speech engine support'))
        speechRec = gizmo.VoskSpeechRecognition()
        vosk = model.get('vosk', {})
        modelDir = vosk.get('model') or model.get('dir')
        if not modelDir:
            raise error.Error(_('Vosk model path is missing'))
        speechRec.setModel(modelDir)
        sampleRate = model.get('samplerate', 16000)
        speechRec.setSampleRate(int(sampleRate))
        return speechRec

    if engine == 'whisper':
        if not hasattr(gizmo, 'WhisperSpeechRecognition'):
            raise error.Error(_('This build has no Whisper speech engine support'))
        speechRec = gizmo.WhisperSpeechRecognition()
        whisper = model.get('whisper', {})
        modelFile = whisper.get('model') or model.get('dir')
        if not modelFile:
            raise error.Error(_('Whisper model path is missing'))
        speechRec.setModel(modelFile)
        speechRec.setSampleRate(int(model.get('samplerate', 16000)))
        speechRec.setLanguage(whisper.get('language', 'en'))
        if whisper.get('threads'):
            speechRec.setThreads(int(whisper['threads']))
        return speechRec

    speechRec = gizmo.SpeechRecognition()
    if 'sphinx' in model:
        for key, val in model['sphinx'].items():
            speechRec.setParam(key, val)
    return speechRec


def getSpeechAudioFormat(speechModel):
    try:
        sampleFormat = getattr(gizmo.AVSampleFormat,
                speechModel.get('sampleformat', 'S16'))

        sampleRate = speechModel.get('samplerate', 16000)
        if type(sampleRate) == str:
            sampleRate = int(sampleRate)

        return gizmo.AudioFormat(sampleFormat, sampleRate, 1)
    except:
        raise error.Error(_('Invalid speech audio format'))
