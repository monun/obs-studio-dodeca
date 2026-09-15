cmake_minimum_required(VERSION 3.28...3.30)

add_executable(test-audio-tracks audio-tracks.cpp)
target_link_libraries(test-audio-tracks PRIVATE OBS::libobs)
target_include_directories(test-audio-tracks PRIVATE "${CMAKE_SOURCE_DIR}/frontend")
target_compile_definitions(test-audio-tracks PRIVATE AUDIO_TRACK_FIXTURES="${CMAKE_CURRENT_SOURCE_DIR}/fixtures")
add_test(NAME audio-tracks COMMAND test-audio-tracks)
set_tests_properties(audio-tracks PROPERTIES TIMEOUT 30)
