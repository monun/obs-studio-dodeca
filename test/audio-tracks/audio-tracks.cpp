#include <obs.hpp>
#include <utility/AudioTracks.hpp>
#include <media-io/media-remux.h>

#include <cstdio>
#include <stdexcept>
#include <string>

static_assert(MAX_AUDIO_MIXES == 12);
static_assert(MAX_OUTPUT_AUDIO_ENCODERS == MAX_AUDIO_MIXES);
static_assert(MAX_AUDIO_CHANNELS == 8);
static_assert(AUDIO_MIXES_MASK == 0xFFF);

#define CHECK(condition) \
	do { \
		if (!(condition)) \
			throw std::runtime_error(std::string(__func__) + ": " + #condition); \
	} while (false)

static void RegisterTypes()
{
	obs_source_info source{};
	source.id = "track-test";
	source.type = OBS_SOURCE_TYPE_INPUT;
	source.output_flags = OBS_SOURCE_AUDIO;
	source.get_name = [](void *) {
		return "Audio track test";
	};
	source.create = [](obs_data_t *, obs_source_t *source) {
		return static_cast<void *>(source);
	};
	source.destroy = [](void *) {
	};
	obs_register_source(&source);
	source.id = "track-test-monitor";
	source.output_flags |= OBS_SOURCE_MONITOR_BY_DEFAULT;
	obs_register_source(&source);

	obs_encoder_info encoder{};
	encoder.id = "track-test-encoder";
	encoder.type = OBS_ENCODER_AUDIO;
	encoder.codec = "aac";
	encoder.get_name = source.get_name;
	encoder.create = [](obs_data_t *, obs_encoder_t *encoder) {
		return static_cast<void *>(encoder);
	};
	encoder.destroy = [](void *) {
	};
	encoder.encode = [](void *, encoder_frame *, encoder_packet *, bool *) {
		return false;
	};
	encoder.get_frame_size = [](void *) -> size_t {
		return 1024;
	};
	obs_register_encoder(&encoder);

	obs_output_info output{};
	output.id = "track-test-output";
	output.flags = OBS_OUTPUT_AUDIO | OBS_OUTPUT_ENCODED | OBS_OUTPUT_MULTI_TRACK_AUDIO;
	output.get_name = source.get_name;
	output.create = [](obs_data_t *, obs_output_t *output) {
		return static_cast<void *>(output);
	};
	output.destroy = [](void *) {
	};
	output.start = [](void *) {
		return false;
	};
	output.stop = [](void *, uint64_t) {
	};
	output.encoded_packet = [](void *, encoder_packet *) {
	};
	obs_register_output(&output);
}

static void CheckRouting()
{
	OBSSourceAutoRelease source = obs_source_create("track-test", "new", nullptr, nullptr);
	CHECK(source);
	CHECK(obs_source_get_audio_mixers(source) == 0xFFF);
	uint32_t signaled = 0;
	OBSSignal signal(
		obs_source_get_signal_handler(source), "audio_mixers",
		[](void *data, calldata_t *params) {
			*static_cast<uint32_t *>(data) = calldata_int(params, "mixers");
			calldata_set_int(params, "mixers", calldata_int(params, "mixers") | (1u << 31));
		},
		&signaled);
	obs_source_set_audio_mixers(source, (1u << 31) | (1u << 11));
	CHECK(signaled == (1u << 11));
	CHECK(obs_source_get_audio_mixers(source) == (1u << 11));
	obs_source_set_audio_mixers(source, 0);
	CHECK(obs_source_get_audio_mixers(source) == 0);
}

static void CheckMigration()
{
	OBSDataAutoRelease fixture = obs_data_create_from_json_file(AUDIO_TRACK_FIXTURES "/legacy-sources.json");
	CHECK(fixture);
	OBSDataArrayAutoRelease cases = obs_data_get_array(fixture, "cases");
	CHECK(obs_data_array_count(cases) == 11);
	for (size_t i = 0; i < obs_data_array_count(cases); i++) {
		OBSDataAutoRelease data = obs_data_array_item(cases, i);
		obs_data_set_default_string(data, "id", "track-test");
		obs_data_set_default_int(data, "prev_ver", LIBOBS_API_VER);
		uint32_t expected = obs_data_get_int(data, "expected");
		OBSSourceAutoRelease source = obs_load_source(data);
		CHECK(source);
		CHECK(obs_source_get_audio_mixers(source) == expected);
		OBSDataAutoRelease saved = obs_save_source(source);
		CHECK(obs_data_get_int(saved, "dodeca_audio_tracks_version") == 1);
		CHECK(obs_data_get_int(saved, "mixers") == expected);
		OBSSourceAutoRelease loaded = obs_load_source(saved);
		CHECK(obs_source_get_audio_mixers(loaded) == expected);
		OBSSourceAutoRelease copy = obs_source_duplicate(source, "copy", true);
		CHECK(obs_source_get_audio_mixers(copy) == expected);
		std::printf("PASS migration: %s\n", obs_data_get_string(data, "name"));
	}
}

static void CheckOutputSlots()
{
	OBSOutputAutoRelease output = obs_output_create("track-test-output", "output", nullptr, nullptr);
	CHECK(output);
	for (size_t i = 0; i < MAX_AUDIO_MIXES; i++) {
		std::string name = "track-" + std::to_string(i + 1);
		OBSEncoderAutoRelease encoder =
			obs_audio_encoder_create("track-test-encoder", name.c_str(), nullptr, i, nullptr);
		CHECK(encoder);
		obs_output_set_audio_encoder(output, encoder, i);
		CHECK(obs_encoder_get_mixer_index(obs_output_get_audio_encoder(output, i)) == i);
		CHECK(name == obs_encoder_get_name(obs_output_get_audio_encoder(output, i)));
	}
	OBSEncoder last = obs_output_get_audio_encoder(output, 11);
	ClearUnusedAudioEncoders(output);
	obs_output_set_audio_encoder(output, last, 0);
	CHECK(obs_encoder_get_mixer_index(obs_output_get_audio_encoder(output, 0)) == 11);
	for (size_t i = 1; i < MAX_OUTPUT_AUDIO_ENCODERS; i++) {
		CHECK(!obs_output_get_audio_encoder(output, i));
	}
	CHECK(ValidStreamingAudioTracks(1 | 2 | 4 | 64 | 1024 | 2048));
	CHECK(!ValidStreamingAudioTracks(1 | 2 | 4 | 8 | 64 | 1024 | 2048));
	CHECK(!ValidStreamingAudioTracks(1u << 12));
	CHECK(AudioTrackCount(1 | 64 | 2048) == 3);
}

int main(int argc, char **argv)
{
	if (argc == 4 && std::string(argv[1]) == "--remux") {
		media_remux_job_t job = nullptr;
		if (!media_remux_job_create(&job, argv[2], argv[3])) {
			return 1;
		}
		bool success = media_remux_job_process(job, nullptr, nullptr);
		media_remux_job_destroy(job);
		return success ? 0 : 1;
	}
	if (!obs_startup("en-US", nullptr, nullptr)) {
		return 1;
	}
	int result = 0;
	try {
		obs_audio_info audio{48000, SPEAKERS_STEREO};
		CHECK(obs_reset_audio(&audio));
		RegisterTypes();
		CheckRouting();
		CheckMigration();
		CheckOutputSlots();
		std::puts("PASS audio track regressions");
	} catch (const std::exception &error) {
		std::fprintf(stderr, "FAIL %s\n", error.what());
		result = 1;
	}
	obs_shutdown();
	return result;
}
