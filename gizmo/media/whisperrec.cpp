#include "whisperrec.h"
#include "text/utf8.h"
#include "general/exception.h"
#include "general/logger.h"
#include <cstring>
#include <sstream>

using namespace std;


WhisperSpeechRecognition::WhisperSpeechRecognition() :
	m_language("en"),
	m_threads(2),
	m_sampleRate(16000),
	m_chunkSamples(30 * 16000),
	m_ctx(NULL),
	m_timeBase(0.0),
	m_deltaTime(-1.0),
	m_processedSamples(0),
	m_minProb(0.0f),
	m_minLen(0)
{
}

WhisperSpeechRecognition::~WhisperSpeechRecognition()
{
	if (m_ctx)
		whisper_free(m_ctx);
}

void WhisperSpeechRecognition::setModel(const string &path)
{
	m_modelPath = path;
}

void WhisperSpeechRecognition::setSampleRate(int sampleRate)
{
	m_sampleRate = sampleRate;
	m_chunkSamples = (size_t) 30 * sampleRate;
}

void WhisperSpeechRecognition::setLanguage(const string &lang)
{
	if (!lang.empty())
		m_language = lang;
}

void WhisperSpeechRecognition::setThreads(int threads)
{
	if (threads > 0)
		m_threads = threads;
}

void WhisperSpeechRecognition::addWordsListener(WordsListener listener)
{
	m_wordsNotifier.addListener(listener);
}

bool WhisperSpeechRecognition::removeWordsListener(WordsListener listener)
{
	return m_wordsNotifier.removeListener(listener);
}

void WhisperSpeechRecognition::setMinWordProb(float minProb)
{
	m_minProb = minProb;
}

void WhisperSpeechRecognition::setMinWordLen(unsigned minLen)
{
	m_minLen = minLen;
}

void WhisperSpeechRecognition::start(const AVStream *stream)
{
	if (m_modelPath.empty())
		throw EXCEPTION("Whisper model path not set")
			.module("WhisperSpeechRecognition", "start");

	whisper_context_params cparams = whisper_context_default_params();
	m_ctx = whisper_init_from_file_with_params(m_modelPath.c_str(), cparams);
	if (m_ctx == NULL)
		throw EXCEPTION("can't load Whisper model")
			.module("WhisperSpeechRecognition", "whisper_init_from_file_with_params")
			.add("path", m_modelPath);

	m_buffer.clear();
	m_deltaTime = -1.0;
	m_processedSamples = 0;
	m_timeBase = av_q2d(stream->time_base);
}

void WhisperSpeechRecognition::stop()
{
	if (m_ctx)
	{
		processBuffer();
		whisper_free(m_ctx);
		m_ctx = NULL;
	}
}

void WhisperSpeechRecognition::feed(const AVFrame *frame)
{
	if (m_deltaTime < 0.0)
		m_deltaTime = m_timeBase * frame->pts;

	const float *data = (const float*) frame->data[0];
	size_t n = frame->nb_samples;
	m_buffer.insert(m_buffer.end(), data, data + n);

	if (m_buffer.size() >= m_chunkSamples)
		processBuffer();
}

void WhisperSpeechRecognition::flush()
{
	processBuffer();
}

void WhisperSpeechRecognition::discontinuity()
{
	processBuffer();
	m_buffer.clear();
	m_deltaTime = -1.0;
	m_processedSamples = 0;
}

void WhisperSpeechRecognition::processBuffer()
{
	if (m_ctx == NULL || m_buffer.empty())
		return;

	const double chunkBase = m_deltaTime +
		(double) m_processedSamples / (double) m_sampleRate;

	whisper_full_params params = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
	params.n_threads        = m_threads;
	params.print_progress   = false;
	params.print_realtime   = false;
	params.print_timestamps = false;
	params.print_special    = false;
	params.translate        = false;
	params.language         = m_language.c_str();
	params.no_context       = true;
	params.single_segment   = false;

	int res = whisper_full(m_ctx, params, m_buffer.data(), (int) m_buffer.size());
	if (res != 0)
	{
		logger::warn("whisper", "whisper_full failed with code %d", res);
		m_processedSamples += m_buffer.size();
		m_buffer.clear();
		return;
	}

	const int n = whisper_full_n_segments(m_ctx);
	for (int i = 0; i < n; i++)
	{
		const char *ctext = whisper_full_get_segment_text(m_ctx, i);
		if (!ctext)
			continue;

		// t0/t1 are in centiseconds (10 ms units) relative to the chunk start.
		const double t0 = whisper_full_get_segment_t0(m_ctx, i) / 100.0;
		const double t1 = whisper_full_get_segment_t1(m_ctx, i) / 100.0;

		// Split the segment text into words, spreading [t0, t1] proportionally.
		std::string seg = ctext;
		std::vector<std::string> words;
		std::istringstream ss(seg);
		std::string tok;
		size_t totalChars = 0;
		while (ss >> tok)
		{
			words.push_back(tok);
			totalChars += tok.size();
		}
		if (words.empty() || totalChars == 0)
			continue;

		const double segDur = (t1 > t0) ? (t1 - t0) : 0.0;
		double acc = 0.0;
		for (const auto &w : words)
		{
			const double frac = (double) w.size() / (double) totalChars;
			const double wStart = t0 + acc * segDur;
			const double wDur = frac * segDur;
			acc += frac;

			if (Utf8::size(w) >= m_minLen && m_minProb <= 1.0f)
				m_wordsNotifier.notify(
						Word(w, (float)(chunkBase + wStart), (float) wDur, 1.0f));
		}
	}

	m_processedSamples += m_buffer.size();
	m_buffer.clear();
}
