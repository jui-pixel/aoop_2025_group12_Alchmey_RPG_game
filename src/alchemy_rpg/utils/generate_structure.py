import os
import ast

def get_definitions(file_path):
    definitions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                definitions.append(f"  - **Class**: `{node.name}`")
                # Optional: List methods if needed, but keeping it high-level for now as per "structure"
            elif isinstance(node, ast.FunctionDef):
                definitions.append(f"  - **Function**: `{node.name}`")
            elif isinstance(node, ast.AsyncFunctionDef):
                 definitions.append(f"  - **Async Function**: `{node.name}`")
    except Exception as e:
        # definitions.append(f"  - (Error parsing file: {e})")
        pass
    return definitions

def generate_structure_md(start_path, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# Project Structure\n\n")
        
        for root, dirs, files in os.walk(start_path):
            # Sort for consistent output
            dirs.sort()
            files.sort()

            # Ignore hidden directories and specific folders
            if ".git" in dirs:
                dirs.remove(".git")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            if ".pytest_cache" in dirs:
                dirs.remove(".pytest_cache")
            if "backup" in dirs:
                dirs.remove("backup")
            if "build" in dirs:
                dirs.remove("build")
            if "assets" in dirs:
                dirs.remove("assets")
            if ".gemini" in dirs: 
                dirs.remove(".gemini") # Don't list my own brain folder if it's there
            if "docs" in dirs and root == start_path:
                 # We are generating into docs, but we might want to list other docs. 
                 # Let's keep docs but maybe be careful not to recurse infinitely if we were writing there?
                 # Actually, os.walk is fine, just don't parse the output file itself if it exists.
                 pass

            level = root.replace(start_path, '').count(os.sep)
            indent = '  ' * level
            
            # Write directory name
            folder_name = os.path.basename(root)
            if folder_name == '':
                folder_name = '.'
            
            out.write(f"{indent}- **{folder_name}/**\n")
            
            subindent = '  ' * (level + 1)
            for f in files:
                if f == "structure.md" and "docs" in root and "architecture" in root:
                    continue # Skip the file we are writing if it exists
                if f == os.path.basename(__file__):
                    continue # Skip this script
                
                # 修改後的寫法 (輸出 file://root/...)
                full_path = os.path.join(root, f)
                # 計算相對於 start_path (專案根目錄) 的路徑
                relative_path = os.path.relpath(full_path, start_path).replace(os.sep, '/')
                # 組合新的連結格式
                out.write(f"{subindent}- [{f}](file://root/{relative_path})\n")
                
                if f.endswith(".py"):
                    defs = get_definitions(os.path.join(root, f))
                    for d in defs:
                        out.write(f"{subindent}  {d}\n")

if __name__ == "__main__":
    start_dir = "."
    output_path = os.path.join("docs", "architecture", "structure.md")
    
    # Ensure directory exists just in case
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Generating structure from {os.path.abspath(start_dir)} into {output_path}...")
    generate_structure_md(start_dir, output_path)
    print("Done.")
