import os

def generate_project_audit(root_dir, output_file="project_audit.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"=== BioDash Project Audit: {root_dir} ===\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            # Calculate the depth for indentation
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            
            # Write the current directory
            folder_name = os.path.basename(root)
            if folder_name:
                f.write(f"{indent}📂 {folder_name}/\n")
            
            # Write the files in that directory
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                # Highlight potential duplicates or temp files
                note = ""
                if file.endswith('.csv'): note = " <-- [Data File]"
                if "__pycache__" in root: note = " <-- [Auto-generated]"
                
                f.write(f"{sub_indent}📄 {file}{note}\n")

if __name__ == "__main__":
    # Get current directory
    current_path = os.getcwd()
    generate_project_audit(current_path)
    print(f"✅ Audit complete! Open 'project_audit.txt' to see your structure.")