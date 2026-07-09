// Segment D: version-gated FFmpeg compat shim — compiles on 5.1 through 7.1+.
//
// In FFmpeg 7.0 the deprecated «channels» / «channel_layout» fields on
// AVCodecContext and AVFrame were removed, together with helpers such as
// av_get_default_channel_layout(), av_get_channel_name(),
// av_get_channel_description(), av_get_channel_layout_channel_index() and
// swr_alloc_set_opts().
//
// Their replacements — the AVChannelLayout struct and the av_channel_layout_*()
// / swr_alloc_set_opts2() family — were all introduced in FFmpeg 5.1, so the
// wrappers below compile unchanged from 5.1 onward. Internally SubSync keeps the
// legacy uint64_t channel-layout bitmask (AudioFormat.channelLayout stays a
// uint64_t and the Python API is unchanged); these helpers translate to/from the
// new struct-based API at the FFmpeg boundary only.

#pragma once
#include <cstdint>

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/frame.h>
#include <libavutil/channel_layout.h>
#include <libswresample/swresample.h>
}

// Convert a single-bit channel mask (legacy AV_CH_*) to an AVChannel enum value.
// In native channel order the enum value equals the bit index of the mask.
inline int su_channel_from_mask(uint64_t channel_mask)
{
    for (int b = 0; b < 64; ++b)
        if (channel_mask == (uint64_t(1) << b))
            return b;
    return -1;
}

// --- read legacy channel info from modern structures ---

inline int su_get_channels(const AVCodecContext *ctx)  { return ctx->ch_layout.nb_channels; }
inline int su_get_channels(const AVFrame *frame)        { return frame->ch_layout.nb_channels; }
inline uint64_t su_get_channel_layout(const AVCodecContext *ctx)  { return (uint64_t) ctx->ch_layout.u.mask; }
inline uint64_t su_get_channel_layout(const AVFrame *frame)       { return (uint64_t) frame->ch_layout.u.mask; }

// --- default layout mask from channel count (was av_get_default_channel_layout) ---

inline uint64_t su_get_default_channel_layout(int channels)
{
    AVChannelLayout l;
    av_channel_layout_default(&l, channels);
    uint64_t mask = (uint64_t) l.u.mask;
    av_channel_layout_uninit(&l);
    return mask;
}

// --- set a frame's layout from a legacy mask (0 => default from channel count) ---

inline void su_set_frame_layout(AVFrame *frame, uint64_t mask, int channels)
{
    av_channel_layout_uninit(&frame->ch_layout);
    if (mask != 0)
        av_channel_layout_from_mask(&frame->ch_layout, mask);
    else
        av_channel_layout_default(&frame->ch_layout, channels);
}

// --- ensure a decoded frame carries a valid layout (was: if 0 use default) ---

inline void su_ensure_frame_layout(AVFrame *frame)
{
    if (frame->ch_layout.u.mask == 0 && frame->ch_layout.nb_channels > 0)
    {
        int nb = frame->ch_layout.nb_channels;
        av_channel_layout_uninit(&frame->ch_layout);
        av_channel_layout_default(&frame->ch_layout, nb);
    }
}

// --- channel name / description (were av_get_channel_name/description) ---
// The new API writes into a buffer; we return a pointer to a thread-local buffer,
// which is consumed immediately by callers (string building / Python conversion).

inline const char *su_get_channel_name(uint64_t channel_mask)
{
    static thread_local char buf[64];
    int chan = su_channel_from_mask(channel_mask);
    if (chan < 0) return nullptr;
    if (av_channel_name(buf, sizeof(buf), (enum AVChannel) chan) < 0) return nullptr;
    return buf;
}

inline const char *su_get_channel_description(uint64_t channel_mask)
{
    static thread_local char buf[128];
    int chan = su_channel_from_mask(channel_mask);
    if (chan < 0) return nullptr;
    if (av_channel_description(buf, sizeof(buf), (enum AVChannel) chan) < 0) return nullptr;
    return buf;
}

// --- index of a channel within a layout (was av_get_channel_layout_channel_index) ---

inline int su_get_channel_index(uint64_t layout_mask, uint64_t channel_mask)
{
    int chan = su_channel_from_mask(channel_mask);
    if (chan < 0) return -1;

    AVChannelLayout l;
    av_channel_layout_from_mask(&l, layout_mask);
    int idx = av_channel_layout_index_from_channel(&l, (enum AVChannel) chan);
    av_channel_layout_uninit(&l);
    return idx;
}

// --- allocate/configure a SwrContext from legacy masks (was swr_alloc_set_opts) ---
// Returns 0 on success, <0 on error; (*ps) is reused if non-NULL.
inline int su_swr_set_opts(struct SwrContext **ps,
        uint64_t out_mask, enum AVSampleFormat out_fmt, int out_rate,
        uint64_t in_mask,  enum AVSampleFormat in_fmt,  int in_rate)
{
    AVChannelLayout outL, inL;
    av_channel_layout_from_mask(&outL, out_mask);
    av_channel_layout_from_mask(&inL,  in_mask);
    int res = swr_alloc_set_opts2(ps,
            &outL, out_fmt, out_rate,
            &inL,  in_fmt,  in_rate,
            0, nullptr);
    av_channel_layout_uninit(&outL);
    av_channel_layout_uninit(&inL);
    return res;
}
