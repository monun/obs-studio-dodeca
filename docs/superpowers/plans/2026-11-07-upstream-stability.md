# Upstream stability backports implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement the approved selection below. Steps use checkbox syntax for tracking.

**Goal:** Apply upstream stability fixes to the 32.2.2 Dodeca fork without adopting the 33.0 directory layout.

**Architecture:** Preserve the upstream patches and Dodeca's twelve-track changes. Keep existing dependencies, module paths, portable packaging, disabled application updates, and version. Add focused regressions to the existing opt-in audio test suite.

**Tech Stack:** C/C++, CMake, Windows x64 / Visual Studio 2026, existing Python media verification tools.

**Spec:** User-approved selection from the upstream investigation; project constraints in `AGENTS.md`.

## Scope

Apply these upstream commits from `obsproject/obs-studio`:

| Commit | Files / behavior |
| --- | --- |
| `4315559a098308604df5cdbf3b1546787a19f050` | `libobs/obs-{audio,video}.c`: execute tasks outside the queue mutex |
| `1bb3a4ee739b43acb3fa77a3c8f2556543e54701` | `libobs/obs.c`: leave graphics context on video initialization failure |
| `575c77f19d704f6abc4bc0dcb250b67002a6601b` | `plugins/obs-outputs/mp4-mux.c`: retain the final packet when flushing |
| `cfc81c9ad44f292fda960693c230a01d6249667c` | `libobs-d3d11/d3d11-shader.cpp`: tolerate invalid shader caches |
| `36d134ee9afff90ab7b067598949fed99b652559` | `frontend/widgets/AudioMixer.cpp`: keep the logged string alive |
| `dfad5c86f66aa5656ddf8d22bd231b85d869b4c3` | `frontend/widgets/OBSBasic_Profiles.cpp`: save pending profile defaults |
| `3bf06991a5db445a96a12c2081686840c8c3b2dd` | `frontend/components/SourceSelectButton.cpp`: read rename signal as a string |
| `0969e43a83db8bbc84eeea5f1b4210ac573d0750` | `plugins/obs-ffmpeg/texture-amf.cpp`: correct B-frame DTS offset |
| `8126df7cd0dd8bd9af29357ec33c86e576a26eef` | `libobs/obs-scene.c`, `frontend/widgets/OBSBasic_Clipboard.cpp`: isolate duplicated groups |
| `0820d804bcabe7a14f0474f73584321b882c7080` | `plugins/linux-alsa/alsa-input.c`: prevent reopening during destruction |

Exclude directory/module loader changes, CEF/dependency upgrades, monitoring API migration, ASIO/VST3, and `f89ad4bee` (file splitting deadline behavior needs separate investigation).

## Global constraints

- Keep 12 independent audio mixes, eight maximum spatial channels, the six-stream SRT/RIST limit, and existing scene migration.
- Keep `bin/`, `data/`, `obs-plugins/` portable layout and application updates disabled.
- Rebuild libobs, frontend and bundled modules together. Do not change submodule revisions or release workflows.
- Use a fresh workspace-local portable installation for runtime verification. Do not control the user's running OBS.
- Preserve historical platform results; record untested platforms and hardware explicitly. Do not commit or push without a request.

## Review focus

- Audio/video callbacks that need another thread to enqueue a task must complete without deadlock.
- Private scene copies must isolate group item transforms while retaining shared source routing.
- Hybrid MP4/MOV must retain final audio/video samples and handle empty/single-packet queues safely.
- Invalid shader cache and video initialization error paths must release resources.
- No 33.0 layout, public monitoring API, six-track defaults, or updater behavior may enter this backport.

## Task 1: Regressions and upstream patches

- [x] Add real queue re-entry and group isolation tests in `test/audio-tracks/upstream-stability.cpp` and final flush tests in `test/audio-tracks/hybrid-final-flush.c`; register them in the existing CMake test suite.
- [x] Build and run against the original code; record expected failures before applying production patches.
- [x] Apply the ten selected patches with the documented chapter guard; compare every production diff with upstream.
- [x] Rebuild and run the full configured CTest suite and Python tests; expect zero failures.

## Task 2: Native validation and review

- [x] Build and install Windows RelWithDebInfo to a fresh prefix; verify portable version and the existing directory layout.
- [x] Exercise twelve-track recording with existing fixtures and inspect decoded audio, names and packet continuity, including Hybrid MP4/MOV where practical.
- [x] Run clang-format 22.1.3, gersemi 0.25.0, `git diff --check`, and strict existing OpenSpec validation.
- [x] Review the complete diff and record source hashes, exact results, and limitations in the Windows validation documents.

## Execution decisions

- Work in place on `fix/upstream-stability-backports` to reuse the existing Windows build and dependency cache. The user already approved the selection; no additional design or worktree approval is needed.
- The initial implementation was left uncommitted. The user subsequently requested a portable build and `github-merge`, authorizing commit, push, PR creation, squash merge and branch cleanup after verification.
- Review found that `575c77f19` also serializes the chapter-duration sentinel. A regression reproduced the extra chapter; retain the sentinel exclusion only for chapter tracks. Other production changes remain identical to upstream.
- A final fragment containing only one audio/video packet still has no preceding fragment sample from which to infer duration and may drop it. This pre-existing upstream limitation is not expanded into a separate muxer redesign here.
- Windows and Linux builds and CTest (5/5 each), Python tests (4/4), and profile switching passed. Seven Windows media files passed decoding, names, tone separation and synchronization. Six passed strict packet continuity; the replay tail discrepancy was reproduced in the pre-backport installation. See the platform validation reports for the MOV frame-count observation and remaining hardware coverage.
