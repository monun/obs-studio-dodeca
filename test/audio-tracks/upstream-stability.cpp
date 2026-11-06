#include <obs.hpp>

#include <atomic>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <thread>

#define CHECK(condition) \
	do { \
		if (!(condition)) \
			throw std::runtime_error(std::string(__func__) + ": " + #condition); \
	} while (false)

struct TaskState {
	obs_task_type type;
	std::atomic<int> completed{0};
};

static void CheckTaskQueue(obs_task_type type)
{
	TaskState state{type};
	obs_queue_task(
		type,
		[](void *param) {
			auto *state = static_cast<TaskState *>(param);
			std::thread producer([state] {
				obs_queue_task(
					state->type, [](void *param) { static_cast<TaskState *>(param)->completed++; },
					state, false);
			});
			producer.join();
		},
		&state, true);
	obs_queue_task(type, [](void *) {}, nullptr, true);
	CHECK(state.completed == 1);
}

static void CheckSceneGroups()
{
	obs_source_info info{};
	info.id = "stability-audio";
	info.type = OBS_SOURCE_TYPE_INPUT;
	info.output_flags = OBS_SOURCE_AUDIO;
	info.get_name = [](void *) {
		return "Stability audio";
	};
	info.create = [](obs_data_t *, obs_source_t *source) {
		return static_cast<void *>(source);
	};
	info.destroy = [](void *) {
	};
	obs_register_source(&info);
	OBSSceneAutoRelease scene = obs_scene_create_private("preview");
	OBSSourceAutoRelease source = obs_source_create_private("stability-audio", "child", nullptr);
	CHECK(source);
	obs_source_set_audio_mixers(source, 1u << 11);
	CHECK(obs_source_get_audio_mixers(source) == (1u << 11));
	obs_sceneitem_t *group = obs_scene_add_group(scene, "group");
	CHECK(group);
	obs_sceneitem_t *item = obs_scene_add(obs_sceneitem_group_get_scene(group), source);
	CHECK(item);
	OBSSceneAutoRelease copy = obs_scene_duplicate(scene, "program", OBS_SCENE_DUP_PRIVATE_REFS);
	CHECK(copy);
	obs_sceneitem_t *copiedGroup = nullptr;
	obs_scene_enum_items(
		copy,
		[](obs_scene_t *, obs_sceneitem_t *item, void *param) {
			*static_cast<obs_sceneitem_t **>(param) = item;
			return false;
		},
		&copiedGroup);
	CHECK(copiedGroup);
	CHECK(obs_sceneitem_get_source(copiedGroup) != obs_sceneitem_get_source(group));
	obs_sceneitem_t *copiedItem = obs_scene_find_source(obs_sceneitem_group_get_scene(copiedGroup), "child");
	CHECK(copiedItem);
	CHECK(obs_sceneitem_get_source(copiedItem) == source);
	CHECK(obs_source_get_audio_mixers(source) == (1u << 11));
	vec2 before{};
	obs_sceneitem_get_pos(copiedItem, &before);
	vec2 changed{before.x + 20.0f, before.y + 30.0f};
	obs_sceneitem_set_pos(item, &changed);
	vec2 after{};
	obs_sceneitem_get_pos(copiedItem, &after);
	CHECK(after.x == before.x && after.y == before.y);
}

int main(int argc, char **argv)
{
	if (argc != 2 || !obs_startup("en-US", nullptr, nullptr)) {
		return 1;
	}
	int result = 0;
	try {
		std::string test = argv[1];
		obs_audio_info audio{48000, SPEAKERS_STEREO};
		CHECK(obs_reset_audio(&audio));
		if (test != "audio") {
			obs_video_info video{};
			video.graphics_module = TEST_GRAPHICS_MODULE;
			video.fps_num = 30;
			video.fps_den = 1;
			video.base_width = video.output_width = 320;
			video.base_height = video.output_height = 180;
			video.output_format = VIDEO_FORMAT_RGBA;
			CHECK(obs_reset_video(&video) == OBS_VIDEO_SUCCESS);
		}
		if (test == "groups") {
			CheckSceneGroups();
		} else if (test == "audio") {
			CheckTaskQueue(OBS_TASK_AUDIO);
		} else if (test == "graphics") {
			CheckTaskQueue(OBS_TASK_GRAPHICS);
		} else {
			throw std::runtime_error("Unknown test");
		}
		std::printf("PASS upstream stability: %s\n", argv[1]);
	} catch (const std::exception &error) {
		std::fprintf(stderr, "FAIL %s\n", error.what());
		result = 1;
	}
	obs_shutdown();
	return result;
}
