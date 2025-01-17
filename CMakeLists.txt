cmake_minimum_required(VERSION 3.18)

project(MyMods)

if(MSVC)
    add_compile_options(/FS)
endif()

add_subdirectory(RE-UE4SS)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/libvotv")
    add_subdirectory(libvotv)
else()
    message(STATUS "libvotv directory not found, skipping...")
endif()




