/* Exercise the production packet queue without exporting muxer internals. */
#include "../../plugins/obs-outputs/mp4-mux.c"

#define CHECK(condition) \
	do { \
		if (!(condition)) { \
			fprintf(stderr, "FAIL %s:%d: %s\n", __func__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (false)

const char *obs_module_text(const char *text)
{
	return text;
}

static void check_flush(enum mp4_track_type type, size_t count, bool final, size_t expected)
{
	struct mp4_mux mux = {0};
	struct mp4_track track = {0};
	track.type = type;
	track.timebase_num = 1;
	track.timebase_den = type == TRACK_VIDEO ? 30 : 48000;
	uint32_t duration = type == TRACK_VIDEO ? 1 : 1024;
	mux.next_frag_pts = final ? 0 : 1000000;
	for (size_t i = 0; i < count; i++) {
		struct encoder_packet packet = {0};
		packet.type = type == TRACK_VIDEO ? OBS_ENCODER_VIDEO : OBS_ENCODER_AUDIO;
		packet.pts = packet.dts = (int64_t)i * duration;
		packet.timebase_num = 1;
		packet.timebase_den = (int32_t)track.timebase_den;
		packet.size = 4;
		deque_push_back(&track.packets, &packet, sizeof(packet));
	}
	uint64_t size = 0;
	process_packets(&mux, &track, &size);
	CHECK(track.samples == expected);
	CHECK(track.fragment_samples.num == expected);
	CHECK(track.duration == expected * duration);
	CHECK(size == expected * 4);
	for (size_t i = 0; i < expected; i++) {
		CHECK(track.fragment_samples.array[i].duration == duration);
	}
	free_track(&track);
}

static void check_chapter_sentinel(void)
{
	struct mp4_mux mux = {0};
	struct mp4_track track = {0};
	track.type = TRACK_CHAPTERS;
	struct encoder_packet packet;
	mp4_create_chapter_pkt(&packet, 0, "Start");
	deque_push_back(&track.packets, &packet, sizeof(packet));
	mp4_create_chapter_pkt(&packet, 10000000, "Dummy");
	deque_push_back(&track.packets, &packet, sizeof(packet));
	uint64_t size = 0;
	process_packets(&mux, &track, &size);
	CHECK(track.samples == 1);
	CHECK(track.fragment_samples.num == 1);
	CHECK(track.duration == 10000);
	CHECK(track.fragment_samples.array[0].duration == 10000);
	free_track(&track);
}

int main(void)
{
	check_chapter_sentinel();
	for (int type = TRACK_VIDEO; type <= TRACK_AUDIO; type++) {
		check_flush(type, 0, true, 0);
		check_flush(type, 1, true, 0);
		check_flush(type, 3, false, 2);
		check_flush(type, 3, true, 3);
	}
	puts("PASS Hybrid MP4/MOV final packet retention");
	return 0;
}
