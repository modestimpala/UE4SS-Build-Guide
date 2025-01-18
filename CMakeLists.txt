cmake_minimum_required(VERSION 3.18)

project(MyMods)

if(MSVC)
    add_compile_options(/FS)
endif()

add_subdirectory(RE-UE4SS)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/extern/libvotv")
    add_subdirectory(extern/libvotv)
else()
    message(STATUS "libvotv directory not found, skipping...")
endif()



add_subdirectory(Mods)


# After all add_subdirectory calls
include(${CMAKE_CURRENT_SOURCE_DIR}/folder_organization.cmake)