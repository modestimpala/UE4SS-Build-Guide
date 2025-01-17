# UE4SS Header Converter

See [dump_converter.py](Tools/dump_converter.py)

A tool for converting UE4SS-generated C++ headers to a FIELD()-type macro format used in game modding/reverse engineering.

## Requirements

Requires [StructUtil.hpp](https://github.com/modestimpala/libvotv/blob/main/include/StructUtil.hpp) or [libvotv](https://github.com/modestimpala/libvotv)

## Background

UE4SS can dump C++ headers from Unreal Engine games using CTRL+H (configurable in Mods/Keybinds/Scripts/main.lua). These dumps contain:
- Blueprint classes (.hpp files)
- Base engine classes (ProjectName.hpp or EngineModule.hpp)
- Enums (in separate _enums.hpp files)
- Most importantly, offset definitions 

While useful, these raw dumps need conversion to use FIELD() macros for proper memory layout and offset handling in mod development.

## Features

- Converts UE4SS dump format to FIELD() macro format
- Preserves memory offsets and class relationships
- Handles multiple field types:
  - Standard fields (FIELD)
  - Vector fields (VECTOR_INT_FIELD)
  - Bit fields (BIT_FIELD)
  - Enum fields (ENUM_FIELD)
- Maintains directory structure
- Preserves original filenames
- Supports common UE4 types with proper RC::Unreal namespace

## Requirements

- Python 3.6+
- UE4SS dump files

## Usage

```bash
python dump_converter.py <input_directory> <output_directory>
```

Example:
```bash
python dump_converter.py ./UE4SS_Dumps ./Converted_Headers
```

## Input Format

The converter expects UE4SS dumps with memory offsets in the following format:
```cpp
class UTimelineComponent* getUpTimeline;                          // 0x05F8 (size: 0x8)
```

## Output Format

Converts to FIELD() macro format:
```cpp
FIELD(0x05F8, RC::Unreal::UTimelineComponent*, getUpTimeline);
```

## UE4SS Dump Configuration

For best results, use these UE4SS settings:

```ini
[CXXHeaderGenerator]
DumpOffsetsAndSizes=1     # Required for offset information
KeepMemoryLayout=0        # UE4SS Readme says this is useless 
LoadAllAssetsBeforeGeneratingCXXHeaders=01  # Recommended
```

Warning: Setting LoadAllAssetsBeforeGeneratingCXXHeaders=1 may result in crashes proceeding past menu.

## Type Handling

The converter handles common UE4 types including:
- Basic types (bool, float, int32_t)
- UE4 types (FString, FName, FText, FVector, etc.)
- Class pointers (AActor*, UObject*)
- Enums and bit fields
- Template types

## Limitations

- Requires properly formatted UE4SS dumps with offset comments
- Some complex template types may need manual adjustment
- Nested class definitions need manual review
- Custom types may need adding to type_mappings

## Contributing

Feel free to:
- Add support for additional types
- Improve type conversion accuracy
- Enhance error handling
- Add batch processing features