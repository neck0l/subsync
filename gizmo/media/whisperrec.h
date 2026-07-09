#ifndef __WHISPERREC_H__
#define __WHISPERREC_H__

#include "avout.h"
#include "text/words.h"
#include <string>
#include <vector>
#include <whisper.h>


// Segment H: Whisper (whisper.cpp) speech-recognition engine. Opt-in / heaviest,
// highest accuracy. Same AVOutput + words-listener contract as the other engines.
// Whisper is not streaming, so audio is buffered and decoded in fixed chunks.
// Requires 16 kHz mono float32 input (descriptor sampleformat = "FLT").
// Compiled only when WITH_WHISPER is defined.

class WhisperSpeechRecognition : public AVOutput
{
	public:
		WhisperSpeechRecognition();
		virtual ~WhisperSpeechRecognition();

		WhisperSpeechRecognition(const WhisperSpeechRecognition&) = delete;
		WhisperSpeechRecognition& operator= (const WhisperSpeechRecognition&) = delete;

		void setModel(const std::string &path);
		void setSampleRate(int sampleRate);
		void setLanguage(const std::string &lang);
		void setThreads(int threads);

		virtual void start(const AVStream *stream);
		virtual void stop();

		void addWordsListener(WordsListener listener);
		bool removeWordsListener(WordsListener listener);

		void setMinWordProb(float minProb);
		void setMinWordLen(unsigned minLen);

		virtual void feed(const AVFrame *frame);
		virtual void flush();
		virtual void discontinuity();

	private:
		void processBuffer();

	private:
		std::string m_modelPath;
		std::string m_language;
		int m_threads;
		int m_sampleRate;
		size_t m_chunkSamples;

		struct whisper_context *m_ctx;

		std::vector<float> m_buffer;
		double m_timeBase;
		double m_deltaTime;
		size_t m_processedSamples;

		WordsNotifier m_wordsNotifier;
		float m_minProb;
		unsigned m_minLen;
};

#endif
