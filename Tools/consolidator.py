import os
import re
from pathlib import Path
from typing import Dict, Set, List, Optional
from collections import defaultdict

class HeaderConsolidator:
    def __init__(self):
        # Known engine modules to exclude
        self.engine_modules = {
            'Engine', 'CoreUObject', 'UMG', 'Slate', 'SlateCore', 
            'InputCore', 'ControlRig', 'Niagara', 'NavigationSystem',
            'AIModule', 'GameplayTags', 'PhysicsCore', 'AnimGraphRuntime',
            'MovieScene', 'LevelSequence', 'GameplayTasks', 'AudioMixer',
            'Paper2D', 'CinematicCamera', 'AssetRegistry', 'AugmentedReality',
            'MRMesh', 'GeometryCollectionEngine', 'ChaosSolverEngine', 'DatasmithContent',
            'DatasmithCore', 'GeometryCollectionSimulationCore'
        }
        
        # Module categorization
        self.module_categories = {
            'Gameplay': ['Character', 'Player', 'Game', 'Save', 'Inventory'],
            'UI': ['HUD', 'Menu', 'Widget'],
            'Props': ['Item', 'Prop', 'Container'],
            'Systems': ['Day', 'Night', 'Weather', 'Power'],
            'Audio': ['Sound', 'Music', 'Voice'],
            'Physics': ['Physics', 'Collision'],
        }

        # Content patterns
        self.class_pattern = re.compile(r'class\s+(\w+)(?:\s*:\s*public\s+(\w+))?')
        self.struct_pattern = re.compile(r'struct\s+(\w+)')
        self.enum_pattern = re.compile(r'enum\s+(?:class\s+)?(\w+)')
        self.field_pattern = re.compile(r'\s*FIELD\((0x[0-9A-F]+),\s*([^,]+),\s*(\w+)\);')
        
        # Track content
        self.structs: Dict[str, str] = {}
        self.classes: Dict[str, str] = {}
        self.enums: Dict[str, str] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)

    def should_skip_file(self, filename: str) -> bool:
        """Check if file should be skipped (engine files)"""
        base_name = Path(filename).stem
        
        # Skip known engine modules
        if any(module in base_name for module in self.engine_modules):
            return True
            
        # Skip generated engine headers
        if base_name == 'Engine' or base_name.endswith('_enums'):
            return True
            
        return False

    def determine_module(self, content: str) -> str:
        """Determine appropriate module based on content"""
        for category, keywords in self.module_categories.items():
            if any(keyword.lower() in content.lower() for keyword in keywords):
                return category
        return 'Game'  # Default module

    def extract_dependencies(self, content: str) -> Set[str]:
        """Extract class and struct dependencies from content"""
        deps = set()
        
        # Find parent classes
        for match in self.class_pattern.finditer(content):
            if match.group(2):  # Has parent class
                deps.add(match.group(2))
                
        # Find field types
        for match in self.field_pattern.finditer(content):
            type_name = match.group(2).strip()
            # Remove RC::Unreal:: namespace
            type_name = type_name.replace('RC::Unreal::', '')
            # Remove template parameters
            type_name = re.sub(r'<.*>', '', type_name)
            # Remove pointer
            type_name = type_name.rstrip('*')
            if type_name not in {'bool', 'float', 'int32_t', 'uint32_t'}:
                deps.add(type_name)
                
        return deps

    def process_file(self, filepath: str) -> Optional[str]:
        """Process a single file and categorize its content"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if content contains engine types
        if any(module in content for module in self.engine_modules):
            return None

        def clean_identifier(name: str) -> str:
            """Clean and validate C++ identifiers"""
            if not name:
                return name
            # If starts with number, prefix with 'C'
            if name[0].isdigit():
                name = 'C' + name
            return name

        # Find all declarations with cleaned names
        for match in self.class_pattern.finditer(content):
            class_name = clean_identifier(match.group(1))
            class_content = self.extract_block(content, match.start())
            if class_content:
                # Replace the original class name with the cleaned version
                class_content = class_content.replace(match.group(1), class_name)
                self.classes[class_name] = class_content
                self.dependencies[class_name] = self.extract_dependencies(class_content)

        for match in self.struct_pattern.finditer(content):
            struct_name = match.group(1)
            if struct_name.startswith('Fstruct_'):
                struct_content = self.extract_block(content, match.start())
                if struct_content:
                    self.structs[struct_name] = struct_content

        for match in self.enum_pattern.finditer(content):
            enum_name = match.group(1)
            enum_content = self.extract_block(content, match.start())
            if enum_content:
                self.enums[enum_name] = enum_content

        return self.determine_module(content)

    def extract_block(self, content: str, start_pos: int) -> Optional[str]:
        """Extract a complete code block starting from position"""
        brace_count = 0
        found_start = False
        block_lines = []
        
        for line in content[start_pos:].split('\n'):
            if '{' in line:
                found_start = True
                brace_count += line.count('{')
            if '}' in line:
                brace_count -= line.count('}')
            
            if found_start:
                block_lines.append(line)
                
            if found_start and brace_count == 0:
                return '\n'.join(block_lines)
                
        return None

    def sort_declarations(self) -> Dict[str, List[str]]:
        """Sort declarations based on dependencies"""
        ordered_content: Dict[str, List[str]] = defaultdict(list)
        
        # Add enums first
        for enum_name, enum_content in sorted(self.enums.items()):
            ordered_content['Enums'].append(enum_content)
            
        # Add structs second
        for struct_name, struct_content in sorted(self.structs.items()):
            ordered_content['Structs'].append(struct_content)
            
        # Add classes in dependency order
        processed = set()
        while self.classes:
            for class_name, deps in self.dependencies.items():
                if class_name not in self.classes:
                    continue
                if deps <= processed:
                    module = self.determine_module(self.classes[class_name])
                    ordered_content[module].append(self.classes[class_name])
                    processed.add(class_name)
                    del self.classes[class_name]
                    break
            else:
                # Handle circular dependencies by adding remaining classes
                for class_name, content in sorted(self.classes.items()):
                    module = self.determine_module(content)
                    ordered_content[module].append(content)
                break
                
        return ordered_content

    def consolidate_headers(self, input_dir: str, output_dir: str):
        """Main consolidation process"""
        # Process all input files
        input_path = Path(input_dir)
        for hpp_file in input_path.glob('**/*.hpp'):
            if self.should_skip_file(str(hpp_file)):
                print(f"Skipping engine file: {hpp_file}")
                continue
                
            print(f"Processing: {hpp_file}")
            self.process_file(str(hpp_file))
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Sort and organize content
        ordered_content = self.sort_declarations()
        
        # Write base includes file
        includes_path = os.path.join(output_dir, 'GameIncludes.hpp')
        with open(includes_path, 'w', encoding='utf-8') as f:
            f.write('#pragma once\n\n')
            f.write('// Core includes\n')
            f.write('#include <Unreal/UObject.hpp>\n')
            f.write('#include <Unreal/AActor.hpp>\n')
            f.write('#include <Unreal/TArray.hpp>\n')
            f.write('#include <Unreal/FString.hpp>\n')
            f.write('#include "StructUtil.hpp"\n\n')
            
            # Add module includes
            f.write('// Game modules\n')
            for module in sorted(ordered_content.keys()):
                if module not in {'Enums', 'Structs'}:
                    f.write(f'#include "Game{module}.hpp"\n')
        
        # Write content files
        for module, content_list in ordered_content.items():
            if not content_list:
                continue
                
            filename = 'GameEnums.hpp' if module == 'Enums' else \
                      'GameStructs.hpp' if module == 'Structs' else \
                      f'Game{module}.hpp'
                      
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('#pragma once\n')
                f.write('#include "GameIncludes.hpp"\n\n')
                f.write('namespace game {\n\n')
                
                for content in content_list:
                    f.write(f'{content}\n\n')
                    
                f.write('} // namespace game\n')
                
            print(f"Created {filename}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Consolidate converted UE4SS headers')
    parser.add_argument('input_dir', help='Directory containing converted headers')
    parser.add_argument('output_dir', help='Directory for consolidated output')
    
    args = parser.parse_args()
    
    consolidator = HeaderConsolidator()
    consolidator.consolidate_headers(args.input_dir, args.output_dir)

if __name__ == '__main__':
    main()