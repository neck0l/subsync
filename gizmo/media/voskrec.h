#ifndef __VOSKREC_H__
#define __VOSKREC_H__

#include "avout.h"
#include "text/words.h"
#include <string>
#include <vosk_api.h>


// Segment G: Vosk (Kaldi) speech-recognition engine. Implements the same
// AVOutput + words-listener contract as the classic SpeechRecognition
// (PocketSphinx) class, so it is a drop-in alternative in the pipeline.
// Compiled only when WITH_VOSK is defined.

class VoskSpeechRecognition : public AVOutput
{
	public:
		VoskSpeechRecognition();
		virtual ~VoskSpeechRecognition();

		VoskSpeechRecognition(const VoskSpeechRecognition&) = delete;
		VoskSpeechRecognition(VoskSpeechRecognition&&) = delete;
		VoskSpeechRecognition& operator= (const VoskSpeechRecognition&) = delete;
		VoskSpeechRecognition& operator= (VoskSpeechRecognition&&) = delete;

		void setModel(const std::string &path);
		void setSampleRate(int sampleRate);

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
		void parseResult(const char *json);

	private:
		std::string m_modelPath;
		VoskModel *m_model;
		VoskRecognizer *m_rec;

		int m_sampleRate;
		double m_timeBase;
		double m_deltaTime;

		WordsNotifier m_wordsNotifier;
		float m_minProb;
		unsigned m_minLen;
};

#endif
