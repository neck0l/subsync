#include "voskrec.h"
#include "text/utf8.h"
#include "general/exception.h"
#include "general/logger.h"
#include "thirdparty/json.hpp"
#include <cstdint>
#include <map>
#include <mutex>

using namespace std;
using json = nlohmann::json;


// Segment G (perf): Vosk models are reference-counted and shareable across
// recognizers/threads. Loading the model is by far the most expensive step, so we
// cache one VoskModel per path for the whole process. Parallel sync jobs then
// share a single in-memory model instead of each loading its own copy.
namespace {
	std::mutex g_modelMutex;
	std::map<std::string, VoskModel*> g_modelCache;

	VoskModel *acquireSharedModel(const std::string &path)
	{
		std::lock_guard<std::mutex> lock(g_modelMutex);
		auto it = g_modelCache.find(path);
		if (it != g_modelCache.end())
			return it->second;

		VoskModel *model = vosk_model_new(path.c_str());
		if (model)
			g_modelCache[path] = model;
		return model;
	}
}



VoskSpeechRecognition::VoskSpeechRecognition() :
	m_model(NULL),
	m_rec(NULL),
	m_sampleRate(16000),
	m_timeBase(0.0),
	m_deltaTime(-1.0),
	m_minProb(0.0f),
	m_minLen(0)
{
	vosk_set_log_level(-1);
}

VoskSpeechRecognition::~VoskSpeechRecognition()
{
	if (m_rec)
		vosk_recognizer_free(m_rec);
	// m_model is owned by the process-wide shared cache; do not free it here.
}

void VoskSpeechRecognition::setModel(const string &path)
{
	m_modelPath = path;
}

void VoskSpeechRecognition::setSampleRate(int sampleRate)
{
	m_sampleRate = sampleRate;
}

void VoskSpeechRecognition::addWordsListener(WordsListener listener)
{
	m_wordsNotifier.addListener(listener);
}

bool VoskSpeechRecognition::removeWordsListener(WordsListener listener)
{
	return m_wordsNotifier.removeListener(listener);
}

void VoskSpeechRecognition::setMinWordProb(float minProb)
{
	m_minProb = minProb;
}

void VoskSpeechRecognition::setMinWordLen(unsigned minLen)
{
	m_minLen = minLen;
}

void VoskSpeechRecognition::start(const AVStream *stream)
{
	if (m_modelPath.empty())
		throw EXCEPTION("Vosk model path not set")
			.module("VoskSpeechRecognition", "start");

	if (m_model == NULL)
	{
		m_model = acquireSharedModel(m_modelPath);
		if (m_model == NULL)
			throw EXCEPTION("can't load Vosk model")
				.module("VoskSpeechRecognition", "vosk_model_new")
				.add("path", m_modelPath);
	}

	m_rec = vosk_recognizer_new(m_model, (float) m_sampleRate);
	if (m_rec == NULL)
		throw EXCEPTION("can't create Vosk recognizer")
			.module("VoskSpeechRecognition", "vosk_recognizer_new");

	vosk_recognizer_set_words(m_rec, 1);

	m_deltaTime = -1.0;
	m_timeBase = av_q2d(stream->time_base);
}

void VoskSpeechRecognition::stop()
{
	if (m_rec)
	{
		parseResult(vosk_recognizer_final_result(m_rec));
		vosk_recognizer_free(m_rec);
		m_rec = NULL;
	}
}

void VoskSpeechRecognition::feed(const AVFrame *frame)
{
	if (m_deltaTime < 0.0)
		m_deltaTime = m_timeBase * frame->pts;

	const short *data = (const short*) frame->data[0];
	int nsamples = frame->nb_samples;

	int res = vosk_recognizer_accept_waveform_s(m_rec, data, nsamples);
	if (res < 0)
		throw EXCEPTION("speech recognition error")
			.module("VoskSpeechRecognition", "vosk_recognizer_accept_waveform_s");

	if (res == 1)
		parseResult(vosk_recognizer_result(m_rec));
}

void VoskSpeechRecognition::flush()
{
}

void VoskSpeechRecognition::discontinuity()
{
	if (m_rec)
	{
		parseResult(vosk_recognizer_final_result(m_rec));
		vosk_recognizer_reset(m_rec);
	}
	m_deltaTime = -1.0;
}

void VoskSpeechRecognition::parseResult(const char *jsonStr)
{
	if (jsonStr == NULL)
		return;

	json j;
	try
	{
		j = json::parse(jsonStr);
	}
	catch (...)
	{
		return;
	}

	auto it = j.find("result");
	if (it == j.end() || !it->is_array())
		return;

	for (const auto &w : *it)
	{
		string word = w.value("word", string());
		if (word.empty())
			continue;

		double start = w.value("start", 0.0);
		double end   = w.value("end", start);
		float  conf  = w.value("conf", 1.0f);

		if (Utf8::size(word) >= m_minLen && conf >= m_minProb)
			m_wordsNotifier.notify(
					Word(word, (float)(start + m_deltaTime),
						(float)(end - start), conf));
	}
}
