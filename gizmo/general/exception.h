#ifndef __EXCEPTION_H__
#define __EXCEPTION_H__

#include "current_function.h"

#include <stdexcept>
#include <string>
#include <map>
#include <sstream>


class Exception : public std::exception
{
	public:
		Exception() noexcept;
		Exception(const std::string &msg) noexcept;
		Exception(const std::string &msg, const std::string &detail) noexcept;
		Exception(const Exception &ex) noexcept;
		virtual ~Exception() noexcept;

		static const Exception *getCurrentException();

		virtual const char* what() const noexcept;
		const char *message() const noexcept;
		const std::map<std::string, std::string> &fields() const noexcept;

		std::string &operator[] (const std::string &field) noexcept;
		const std::string &operator[] (const std::string &field) const noexcept;

		Exception &add(const std::string &field, const std::string &val) noexcept;

		template <typename T>
			Exception &add(const std::string &field, const T &val) noexcept
			{
				std::stringstream ss;
				ss << val;
				return add(field, ss.str());
			}

		Exception &module(const std::string &m) noexcept;
		Exception &module(const std::string &m1, const std::string &m2,
				const std::string &m3="", const std::string &m4="") noexcept;
		Exception &code(int code) noexcept;
		Exception &averror(int errnum) noexcept;
		Exception &file(const std::string &file) noexcept;
		Exception &line(const std::string &line) noexcept;
		Exception &time(double timestamp) noexcept;

		const std::string &get(const std::string &field) const noexcept;

	private:
		std::string msg;
		std::map<std::string, std::string> vals;

		mutable std::string str;
		mutable std::string fieldsStr;
};


class ExceptionTerminated : public Exception
{
	public:
		ExceptionTerminated() noexcept;
		ExceptionTerminated(const Exception &ex) noexcept;
		virtual ~ExceptionTerminated() noexcept;
};


std::string makeSourceString(const char *file, int line, const char *func) noexcept;
std::string ffmpegCodeDescription(int code) noexcept;

#define EXCEPTION_ADD_SOURCE \
	add("source", makeSourceString(__FILE__, __LINE__, BOOST_CURRENT_FUNCTION))

#define EXCEPTION(msg) \
	Exception(msg).EXCEPTION_ADD_SOURCE

#define EXCEPTION_FFMPEG(msg, val) \
	Exception(msg, ffmpegCodeDescription(val)).averror(val).EXCEPTION_ADD_SOURCE

#endif
