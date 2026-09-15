#pragma once

#include <obs.hpp>

#include <bitset>

/* Expanding the available mixes does not change the service's stream count. */
constexpr size_t MAX_STREAM_AUDIO_TRACKS = 6;

inline size_t AudioTrackCount(uint32_t mask)
{
	return std::bitset<32>(mask & AUDIO_MIXES_MASK).count();
}

inline bool ValidStreamingAudioTracks(uint32_t mask)
{
	return (mask & ~AUDIO_MIXES_MASK) == 0 && AudioTrackCount(mask) <= MAX_STREAM_AUDIO_TRACKS;
}

inline void ClearUnusedAudioEncoders(obs_output_t *output, size_t first = 0)
{
	if (!output || obs_output_active(output)) {
		return;
	}
	size_t count = (obs_output_get_flags(output) & OBS_OUTPUT_MULTI_TRACK_AUDIO) ? MAX_OUTPUT_AUDIO_ENCODERS : 1;
	for (size_t i = first; i < count; i++) {
		obs_output_set_audio_encoder(output, nullptr, i);
	}
}
