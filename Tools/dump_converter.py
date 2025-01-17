import re
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set

class HPPConverter:
    def __init__(self):
        self.type_mappings = {
            'bool': 'bool',
            'float': 'float',
            'int32': 'int32_t',
            'uint8': 'uint8_t',
            'uint16': 'uint16_t',
            'uint32': 'uint32_t',
            'uint64': 'uint64_t',
            'int8': 'int8_t',
            'int16': 'int16_t',
            'int64': 'int64_t',
            'FString': 'RC::Unreal::FString',
            'FName': 'RC::Unreal::FName',
            'FText': 'RC::Unreal::FText',
            'FVector': 'RC::Unreal::FVector',
            'FRotator': 'RC::Unreal::FRotator',
            'FTransform': 'RC::Unreal::FTransform',
            'FLinearColor': 'RC::Unreal::FLinearColor',
            'UStaticMesh*': 'RC::Unreal::UStaticMesh*',
            'AActor*': 'RC::Unreal::AActor*',
            'UObject*': 'RC::Unreal::UObject*'
        }

        self.ignored_types = {
            'FPointerToUberGraphFrame',
            'TextureFilter',
            'ETimelineDirection',
            'ECollisionChannel',
            'FConnectionCallbackProxyOnSuccess',
            'FCheckGeoTrackingAvailabilityAsyncTaskBlueprintProxyOnSuccess',
            'TSoftClassPtr',
            'TSoftObjectPtr',
            'FJSONParserAsyncObjectToStringOnSuccess',
            'FBox',
            'FVector4',
            'FGuid'
        }

        self.struct_cache: Dict[str, List[str]] = {}

    def clean_name(self, name: str) -> str:
        """Clean variable names by removing numeric suffixes and GUIDs"""
        # Remove _X_GUID pattern
        name = re.sub(r'_\d+_[A-F0-9]{32}$', '', name)
        # Remove numeric suffix
        name = re.sub(r'_\d+$', '', name)
        return name

    def clean_class_name(self, name: str) -> str:
        """Clean up class names while preserving core UE4 types"""
        if not name:
            return name
                
        # Skip core UE4 types
        if name.startswith(('UObject', 'AActor', 'UActorComponent')):
            return name
            
        # Fix invalid C++ identifiers - if starts with number, prefix with 'C'
        if name[0].isdigit():
            name = 'C' + name
                
        # Clean up game-specific classes
        if name.startswith('A') and name.endswith('_C'):
            name = name[1:-2]
        elif name.startswith('U') and name.endswith('_C'):
            name = name[1:-2]
                
        return name


    def process_struct_file(self, struct_name: str, input_dir: str) -> List[str]:
        """Process a struct definition file"""
        struct_file = Path(input_dir) / f"{struct_name.lower()}.hpp"
        if not struct_file.exists():
            return []

        struct_lines = []
        in_struct = False
        
        with open(struct_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            if f"struct {struct_name}" in line:
                struct_lines.append(f"struct {struct_name} {{\n")
                in_struct = True
                continue
                
            if in_struct:
                if "};" in line:
                    struct_lines.append("};\n\n")
                    break
                    
                if "//" in line and "0x" in line:
                    field_line = self.convert_struct_field(line)
                    if field_line:
                        struct_lines.append(field_line)
                        
        return struct_lines

    def convert_struct_field(self, line: str) -> Optional[str]:
        """Convert a struct field line to FIELD() format"""
        # Match the field pattern including GUIDs
        match = re.match(r'\s*([\w<>*:]+(?:\s*[*&])?)\s+(\w+(?:_\d+)?(?:_[A-F0-9]{32})?);?\s*//\s*(0x[0-9A-F]+)', line, re.IGNORECASE)
        if not match:
            return None

        type_name, var_name, offset = match.groups()
        clean_var_name = self.clean_name(var_name)
        converted_type = self.convert_type(type_name)
        
        if not converted_type:
            return None

        return f"    FIELD({offset}, {converted_type}, {clean_var_name});\n"

    def convert_type(self, ue_type: str) -> Optional[str]:
        """Convert UE4SS type to appropriate format"""
        # Check if type should be ignored
        if any(ignored in ue_type for ignored in self.ignored_types):
            return None
                
        # Remove class prefix if present
        ue_type = re.sub(r'^class\s+', '', ue_type)
            
        # Handle TArray
        if ue_type.startswith('TArray<'):
            inner_type = re.search(r'TArray<(.+)>', ue_type).group(1)
            converted_inner = self.convert_type(inner_type)
            if converted_inner:
                return f"RC::Unreal::TArray<{converted_inner}>"
            return None

        # Handle TSubclassOf
        if ue_type.startswith('TSubclassOf<'):
            inner_type = re.search(r'TSubclassOf<(.+)>', ue_type).group(1)
            converted_inner = self.convert_type(inner_type)
            if converted_inner:
                return f"RC::Unreal::TSubclassOf<{converted_inner}>"
            return None
                
        # Don't convert core UE4 types
        if ue_type.startswith(('UObject', 'AActor', 'UActorComponent')):
            return ue_type
                
        # Check direct mappings for non-core types
        if ue_type in self.type_mappings:
            return self.type_mappings[ue_type]
                
        # Handle pointers to known types
        base_type = ue_type.rstrip('*')
        if base_type in self.type_mappings:
            return f"{self.type_mappings[base_type]}*"

        # Handle enum types
        if ue_type.startswith('TEnumAsByte<'):
            enum_type = re.search(r'TEnumAsByte<(.+)>', ue_type).group(1)
            return enum_type

        # Clean up class names
        cleaned_type = self.clean_class_name(ue_type)
        if cleaned_type != ue_type:
            return cleaned_type
                
        return ue_type

    def convert_file(self, input_path: str, input_dir: str) -> List[str]:
        """Convert file content"""
        output_lines = []
        current_class = None
        found_structs: Set[str] = set()
        
        # Add standard includes
        output_lines.extend([
            '#pragma once\n',
            '#include <Unreal/UObject.hpp>\n',
            '#include <Unreal/AActor.hpp>\n',
            '#include <Unreal/TArray.hpp>\n',
            '#include <Unreal/FString.hpp>\n',
            '#include "StructUtil.hpp"\n\n',
            'namespace game {\n\n'
        ])

        # First pass - collect struct names
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            struct_matches = re.finditer(r'struct\s+(Fstruct_\w+)', content)
            found_structs.update(match.group(1) for match in struct_matches)

        # Process struct definitions
        for struct_name in sorted(found_structs):
            struct_lines = self.process_struct_file(struct_name, input_dir)
            if struct_lines:
                output_lines.extend(struct_lines)

        # Process main file
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            class_match = re.match(r'class\s+(\w+)\s*:', line)
            if class_match:
                if current_class:
                    output_lines.append("};\n\n")
                class_name = self.clean_class_name(class_match.group(1))
                parent_match = re.search(r':\s*(?:public\s+)?(\w+)', line)
                parent_class = self.clean_class_name(parent_match.group(1)) if parent_match else ""
                parent_class = f" : public {parent_class}" if parent_class else ""
                output_lines.append(f"class {class_name}{parent_class} {{\npublic:\n")
                current_class = class_name
                continue

            if '//' in line and '0x' in line:
                field_line = self.convert_line_to_field(line)
                if field_line:
                    output_lines.append(field_line)

        if current_class:
            output_lines.append("};\n\n")

        output_lines.append("} // namespace game\n")
        return output_lines

    def convert_line_to_field(self, line: str) -> Optional[str]:
        """Convert a single line to FIELD() format"""
        match = re.match(r'\s*([\w<>*:]+(?:\s*[*&])?)\s+(\w+);?\s*//\s*(0x[0-9A-F]+)', line, re.IGNORECASE)
        if not match:
            return None

        type_name, var_name, offset = match.groups()
        converted_type = self.convert_type(type_name)
        
        if not converted_type:
            return None
            
        return f"    FIELD({offset}, {converted_type}, {var_name});\n"

def process_files(input_dir: str, output_dir: str):
    """Process all .hpp files in input directory"""
    converter = HPPConverter()
    
    os.makedirs(output_dir, exist_ok=True)
    
    input_path = Path(input_dir)
    for hpp_file in input_path.glob('**/*.hpp'):
        # Skip struct definition files, they'll be processed as needed
        if hpp_file.stem.startswith('struct_'):
            continue
            
        try:
            rel_path = hpp_file.relative_to(input_path)
            output_path = Path(output_dir) / rel_path
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            converted_lines = converter.convert_file(str(hpp_file), str(input_path))
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(converted_lines)
                
            print(f"Successfully converted {hpp_file} -> {output_path}")
            
        except Exception as e:
            print(f"Error converting {hpp_file}: {str(e)}")

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python hpp_converter.py <input_directory> <output_directory>")
        return
        
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} not found")
        return
        
    try:
        process_files(input_dir, output_dir)
        print(f"Conversion complete. Results written to {output_dir}")
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

if __name__ == "__main__":
    main()