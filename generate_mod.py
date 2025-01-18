#!/usr/bin/env python3
import os
import argparse
import subprocess
import shutil
import re
from pathlib import Path

class ModGenerator:
    def __init__(self, mod_name: str, profile_name: str, base_dir: str):
        self.mod_name = mod_name + "Cpp"
        self.profile_name = profile_name
        self.base_dir = Path(base_dir)
        # Create Mods subdirectory if it doesn't exist
        self.mods_dir = self.base_dir / "Mods"
        self.mods_dir.mkdir(exist_ok=True)
        # Place mod directory inside Mods/
        self.mod_dir = self.mods_dir / self.mod_name
        self.template_url = "https://github.com/modestimpala/SampleCppMod.git"

    def clone_template(self):
        """Clone the SampleCppMod template repository."""
        print(f"Cloning template from {self.template_url}...")
        subprocess.run(["git", "clone", self.template_url, self.mod_name], cwd=self.mods_dir, check=True)
        
        # Remove the .git directory to detach from template repo
        shutil.rmtree(self.mod_dir / ".git", ignore_errors=True)

    def modify_cmake(self):
        """Modify the existing CMakeLists.txt file."""
        cmake_path = self.mod_dir / "CMakeLists.txt"
        
        with open(cmake_path, "r") as f:
            content = f.read()
        
        # Replace project name while preserving formatting
        pattern = r'(project\s*\(\s*)SampleCppMod(\s*\))'
        content = re.sub(pattern, f'\\1{self.mod_name}\\2', content)
        
        # Update the variable definition
        pattern = r'set\(MOD_OUTPUT_PATH\s+"[^"]*"\s+CACHE\s+PATH\s+"[^"]*"\)'
        new_path = f'set(MOD_OUTPUT_PATH_{self.mod_name.upper()} "C:/Users/$ENV{{USERNAME}}/AppData/Roaming/r2modmanPlus-local/VotV/profiles/{self.profile_name}/shimloader/mod/{self.mod_name}/dlls" CACHE PATH "Path to mod output directory")'
        content = re.sub(pattern, new_path, content)
        
        # Update references to MOD_OUTPUT_PATH in the copy command
        pattern = r'\${MOD_OUTPUT_PATH}'
        content = re.sub(pattern, f'${{MOD_OUTPUT_PATH_{self.mod_name.upper()}}}', content)
        
        # Write the modified content with original line endings
        with open(cmake_path, "w", newline='\n') as f:
            f.write(content)

    def modify_dllmain(self):
        """Modify the existing dllmain.cpp file."""
        dllmain_path = self.mod_dir / "src" / "dllmain.cpp"
        
        with open(dllmain_path, "r") as f:
            content = f.read()
        
        # Create the class name with "Cpp" suffix
        class_name = f"{self.mod_name}Cpp"
        
        # Replace class name and mod name
        content = re.sub(
            r'class \w+ : public RC::CppUserModBase',
            f'class {class_name} : public RC::CppUserModBase',
            content
        )
        
        # Replace mod name in STR
        content = re.sub(
            r'ModName = STR\("\w+"\)',
            f'ModName = STR("{self.mod_name}")',
            content
        )
        
        # Update constructor and destructor
        content = re.sub(
            r'\w+\(\) : CppUserModBase\(\)',
            f'{class_name}() : CppUserModBase()',
            content
        )
        
        content = re.sub(
            r'~\w+\(\)',
            f'~{class_name}()',
            content
        )
        
        # Update define and return statement
        content = re.sub(
            r'#define MY_AWESOME_MOD_API',
            f'#define {self.mod_name.upper()}_MOD_API',
            content
        )
        
        content = re.sub(
            r'MY_AWESOME_MOD_API',
            f'{self.mod_name.upper()}_MOD_API',
            content, count=2  # Replace both occurrences in extern "C" block
        )
        
        # Update the return new statement
        content = re.sub(
            r'return new \w+\(\);',
            f'return new {class_name}();',
            content
        )
        
        with open(dllmain_path, "w") as f:
            f.write(content)

    def update_mods_cmake(self):
        """Update the main CMakeLists.txt to include the new mod."""
        main_cmake_path = self.base_dir / "Mods" /  "CMakeLists.txt"
        if not main_cmake_path.exists():
            print("Error: Mods CMakeLists.txt not found!")
            return

        with open(main_cmake_path, "r") as f:
            content = f.read()
        # Add subdirectory with Mods prefix
        content += f"\nadd_subdirectory({self.mod_name})\n"
    
        with open(main_cmake_path, "w") as f:
            f.write(content)

    def setup_mod(self):
        """Set up the mod by cloning template and modifying files."""
        try:
            self.clone_template()
            self.modify_cmake()
            self.modify_dllmain()
            self.update_mods_cmake()
            print(f"Successfully created mod: {self.mod_name}")
        except Exception as e:
            print(f"Error creating mod: {e}")
            # Clean up if something went wrong
            if self.mod_dir.exists():
                shutil.rmtree(self.mod_dir)
            raise

def main():
    parser = argparse.ArgumentParser(description="Generate a new UE4SS mod project from template")
    parser.add_argument("mod_name", help="Name of the mod to create")
    parser.add_argument("profile_name", help="r2modman profile name")
    parser.add_argument("--base-dir", default=".", help="Base directory for the mod (default: current directory)")
    
    args = parser.parse_args()
    
    generator = ModGenerator(args.mod_name, args.profile_name, args.base_dir)
    generator.setup_mod()
    
    print("\nNext steps:")
    print("1. Review the modified files")
    print("2. Build the project using CMake")
    print(f"3. The mod will be automatically copied to: C:/Users/%USERNAME%/AppData/Roaming/r2modmanPlus-local/VotV/profiles/{args.profile_name}/shimloader/mod/{args.mod_name}/dlls")

if __name__ == "__main__":
    main()