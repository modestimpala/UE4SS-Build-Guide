# folder_organization.cmake
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Create main category groupings
set(FOLDER_CATEGORIES
    "Mods"                  # Your game mods
    "Core/First"           # First-party core libraries
    "Core/Parsing"         # Parsing-related
    "Core/Unreal"          # UE4-specific
    "ThirdParty/Assembly"  # ASM-related third party
    "ThirdParty/Debug"     # Debug/profiling tools
    "ThirdParty/Cargo"     # Rust/Cargo related
    "ThirdParty/Other"     # Other third party libs
)

# Core/First
set_target_properties(
    ASMHelper
    DynamicOutput
    File
    Input
    SinglePassSigScanner
    PROPERTIES FOLDER "Core/First"
)

# Core/Parsing
set_target_properties(
    ArgsParser_DEV_TEST
    IniParser
    JSON
    ParserBase
    PROPERTIES FOLDER "Core/Parsing"
)

# Core/Unreal
set_target_properties(
    UE4SS
    Unreal
    UnrealVTableDumper
    proxy
    proxy_files
    proxy_generator
    PROPERTIES FOLDER "Core/Unreal"
)

# ThirdParty/Assembly
set_target_properties(
    asmjit
    asmtk
    PolyHook_2
    Zydis
    Zycore
    PROPERTIES FOLDER "ThirdParty/Assembly"
)

# ThirdParty/Debug
set_target_properties(
    TracyClient
    raw_pdb
    Examples
    PROPERTIES FOLDER "ThirdParty/Debug"
)

# ThirdParty/Cargo
set_target_properties(
    cargo-build_patternsleuth_bind
    cargo-clean
    cargo-clean_patternsleuth_bind
    cargo-prebuild
    cargo-prebuild_patternsleuth_bind
    PROPERTIES FOLDER "ThirdParty/Cargo"
)

# ThirdParty/Other
set_target_properties(
    ImGui
    LuaMadeSimple
    LuaRaw
    PROPERTIES FOLDER "ThirdParty/Other"
)


# This doesn't seem to work 
# Get all targets and put uncategorized ones in Mods
function(organize_uncategorized_targets)
    # Get all targets in the project
    get_all_targets_recursive(all_targets ${CMAKE_CURRENT_SOURCE_DIR})
    
    foreach(target ${all_targets})
        # Check if target already has a folder property
        get_target_property(folder ${target} FOLDER)
        if(NOT folder)
            # If no folder is set and the target exists in Mods directory
            get_target_property(target_source_dir ${target} SOURCE_DIR)
            if(target_source_dir MATCHES ".*/Mods/.*")
                set_target_properties(${target} PROPERTIES FOLDER "Mods")
            endif()
        endif()
    endforeach()
endfunction()

# Helper function to get all targets
function(get_all_targets_recursive targets dir)
    get_property(subdirectories DIRECTORY ${dir} PROPERTY SUBDIRECTORIES)
    foreach(subdir ${subdirectories})
        get_all_targets_recursive(${targets} ${subdir})
    endforeach()
    
    get_property(current_targets DIRECTORY ${dir} PROPERTY TARGETS)
    set(${targets} ${${targets}} ${current_targets} PARENT_SCOPE)
endfunction()

# Call the organization function
organize_uncategorized_targets()