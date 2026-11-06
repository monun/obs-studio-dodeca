cmake_minimum_required(VERSION 3.28...3.30)

add_executable(test-audio-tracks audio-tracks.cpp)
target_link_libraries(test-audio-tracks PRIVATE OBS::libobs)
target_include_directories(test-audio-tracks PRIVATE "${CMAKE_SOURCE_DIR}/frontend")
target_compile_definitions(test-audio-tracks PRIVATE AUDIO_TRACK_FIXTURES="${CMAKE_CURRENT_SOURCE_DIR}/fixtures")
add_test(NAME audio-tracks COMMAND test-audio-tracks)
set_tests_properties(audio-tracks PROPERTIES TIMEOUT 30)

add_executable(test-upstream-stability upstream-stability.cpp)
target_link_libraries(test-upstream-stability PRIVATE OBS::libobs)
if(OS_WINDOWS)
  target_compile_definitions(test-upstream-stability PRIVATE TEST_GRAPHICS_MODULE="$<TARGET_FILE:libobs-d3d11>")
  add_dependencies(test-upstream-stability libobs-d3d11)
else()
  target_compile_definitions(test-upstream-stability PRIVATE TEST_GRAPHICS_MODULE="$<TARGET_FILE:libobs-opengl>")
  add_dependencies(test-upstream-stability libobs-opengl)
endif()
foreach(case IN ITEMS audio graphics groups)
  add_test(NAME upstream-${case} COMMAND test-upstream-stability ${case})
  set_tests_properties(upstream-${case} PROPERTIES TIMEOUT 15)
  if(OS_WINDOWS)
    set_tests_properties(upstream-${case} PROPERTIES WORKING_DIRECTORY "${CMAKE_BINARY_DIR}/rundir/$<CONFIG>/bin/64bit")
  endif()
endforeach()

add_executable(
  test-hybrid-final-flush
  hybrid-final-flush.c
  "${CMAKE_SOURCE_DIR}/plugins/obs-outputs/rtmp-av1.c"
  $<$<BOOL:${ENABLE_HEVC}>:${CMAKE_SOURCE_DIR}/plugins/obs-outputs/rtmp-hevc.c>
)
target_link_libraries(test-hybrid-final-flush PRIVATE OBS::libobs)
add_test(NAME hybrid-final-flush COMMAND test-hybrid-final-flush)
set_tests_properties(hybrid-final-flush PROPERTIES TIMEOUT 15)
