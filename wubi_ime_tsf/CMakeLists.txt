cmake_minimum_required(VERSION 3.16)
project(WubiIME_TSF VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# TSF IME DLL
add_library(WubiIME_TSF SHARED
    src/dllmain.cpp
    src/factory.cpp
    src/factory.h
    src/text_service.cpp
    src/text_service.h
    src/engine.cpp
    src/engine.h
    src/candidate_window.cpp
    src/candidate_window.h
    src/utils.cpp
    src/utils.h
    src/common.h
    src/resource.rc
    src/WubiIME_TSF.def
)

target_include_directories(WubiIME_TSF PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(WubiIME_TSF PRIVATE
    user32
    gdi32
    shell32
    ole32
    oleaut32
    uuid
    pathcch
)

target_compile_definitions(WubiIME_TSF PRIVATE
    _WIN32_WINNT=_WIN32_WINNT_WIN10
    WIN32_LEAN_AND_MEAN
    NOMINMAX
    UNICODE
    _UNICODE
)

# Force UTF-8 source/execution character set to avoid C4819 on Chinese Windows.
if(MSVC)
    target_compile_options(WubiIME_TSF PRIVATE /utf-8)
endif()

# Set output name
set_target_properties(WubiIME_TSF PROPERTIES
    OUTPUT_NAME "WubiIME_TSF"
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Copy data file to output directory
add_custom_command(TARGET WubiIME_TSF POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_CURRENT_SOURCE_DIR}/data
    ${CMAKE_BINARY_DIR}/bin/data
)
