"""Generate subtitles (transcribe) from video/audio using the bundled Whisper engine.

This is separate from speech-based *sync* — it produces a standalone transcript
SRT. It uses the existing Whisper model asset (same one the sync engine uses) by
feeding it raw decoded audio and collecting the output word stream, then grouping
words into subtitle cues.
"""

import os
import math
import logging

logger = logging.getLogger(__name__)


def transcribeToCues(demux, extractor, whisper_engine, audio_format, audio_no):
    """Run a whisper pipeline over the audio stream and return SubtitleCue-list."""
    try:
        from gizmo import AudioDec, Resampler
    except ImportError:
        logger.warning('gizmo not available; ASR transcript generation skipped')
        return []

    dec = AudioDec()
    resampler = Resampler()
    dec.connectOutput(resampler)
    resampler.connectOutput(whisper_engine, audio_format)
    demux.connectDec(dec, audio_no)

    extractor.selectTimeWindow(0, math.inf)
    extractor.start('WhisperTranscript')

    words = []
    def onWord(word):
        words.append({'text': word.text, 'time': word.time,
                       'duration': getattr(word, 'duration', 0.0),
                       'score': getattr(word, 'score', 1.0)})

    whisper_engine.addWordsListener(onWord)
    try:
        extractor.wait()
    except Exception:
        pass
    whisper_engine.removeWordsListener(onWord)

    if not words:
        return []

    # Group words into subtitle lines: gap > 1.0s = new cue, max ~10 words / 72 chars.
    cues = []
    current_words = []
    current_start = None
    for w in words:
        if not current_words:
            current_words = [w]
            current_start = w['time']
            continue
        gap = w['time'] - (current_words[-1]['time'] + current_words[-1]['duration'])
        # New cue when gap is large, line gets long, or punctuation ends
        text = ' '.join(c['text'] for c in current_words)
        if (gap > 1.0 or len(current_words) >= 10 or len(text) > 72 or
                (text and text[-1] in '.!?' and len(current_words) >= 3 and gap > 0.3)):
            end = current_words[-1]['time'] + current_words[-1]['duration']
            cues.append({'start': current_start, 'end': end,
                         'text': text.strip()})
            current_words = [w]
            current_start = w['time']
        else:
            current_words.append(w)

    if current_words:
        text = ' '.join(c['text'] for c in current_words)
        end = current_words[-1]['time'] + current_words[-1]['duration']
        cues.append({'start': current_start, 'end': end,
                     'text': text.strip()})

    return cues


def saveCuesAsSrt(cues, path):
    """Save a list of {'start','end','text'} dicts as an SRT file."""
    import pysubs2
    subs = pysubs2.SSAFile()
    for c in cues:
        subs.append(pysubs2.SSAEvent(
            start=c['start'] * 1000.0,
            end=c['end'] * 1000.0,
            text=c['text']))
    subs.save(path, format_='srt')


def transcribeMedia(mediaPath, outputPath, whisper_engine=None,
                    modelPath=None, language='auto'):
    """High-level: open a media file, transcribe the audio, save an SRT.

    whisper_engine:  a pre-configured gizmo.VoskSpeechRecognition-like AVOutput
                     (WhisperSpeechRecognition or SpeechRecognition).
                     If None, creates one from modelPath (a whisper ggml file).
    """
    try:
        import gizmo
    except ImportError:
        raise RuntimeError('gizmo not available; cannot transcribe')

    demux = gizmo.Demux(mediaPath)
    streams = demux.getStreamsInfo()
    # pick the first audio stream
    audio_no = None
    for s in streams:
        if s.type == 'audio':
            audio_no = s.no
            break
    if audio_no is None:
        raise RuntimeError('no audio stream found in %s' % mediaPath)

    extractor = gizmo.Extractor(demux)
    audioFormat = gizmo.AudioFormat(gizmo.AVSampleFormat.FLT, 16000, 1)

    if whisper_engine is None:
        if not hasattr(gizmo, 'WhisperSpeechRecognition'):
            raise RuntimeError('Whisper engine not available in this build')
        engine = gizmo.WhisperSpeechRecognition()
        engine.setModel(modelPath)
        engine.setSampleRate(16000)
        engine.setLanguage(language)
    else:
        engine = whisper_engine

    cues = transcribeToCues(demux, extractor, engine, audioFormat, audio_no)
    if not cues:
        raise RuntimeError('No speech detected (0 cues)')

    saveCuesAsSrt(cues, outputPath)
    return len(cues)
