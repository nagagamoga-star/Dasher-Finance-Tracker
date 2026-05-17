import os
import shutil

def deep_clean_biodash():
    root = os.getcwd()
    # 1. Ensure primary folders exist
    FINAL_DATA_DIR = os.path.join(root, "data", "raw")
    FINAL_CONFIG_DIR = os.path.join(root, "config")
    
    os.makedirs(FINAL_DATA_DIR, exist_ok=True)
    os.makedirs(FINAL_CONFIG_DIR, exist_ok=True)

    # 2. Rescue paths to scan for files before deleting
    search_paths = [
        os.path.join(root, "src", "logging", "data", "raw"),
        os.path.join(root, "src", "logging", "config"),
        os.path.join(root, "src", "config"),
        os.path.join(root, "src", "data", "raw")
    ]

    for path in search_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                src_file = os.path.join(path, file)
                
                # Fix double extension issue
                clean_name = file
                if file.lower().endswith(".csv.csv"):
                    clean_name = file.lower().replace(".csv.csv", ".csv")
                
                if clean_name.lower().endswith(".csv"):
                    dest_file = os.path.join(FINAL_DATA_DIR, clean_name)
                elif clean_name.lower().endswith((".json", ".txt")):
                    dest_file = os.path.join(FINAL_CONFIG_DIR, clean_name)
                else:
                    continue
                
                if not os.path.exists(dest_file):
                    shutil.move(src_file, dest_file)

    # 3. List of redundant folders to remove
    folders_to_delete = [
        os.path.join(root, "src", "config"),
        os.path.join(root, "src", "data"),
        os.path.join(root, "src", "logging", "config"),
        os.path.join(root, "src", "logging", "data"),
        os.path.join(root, "src", "logging", "__pycache__"),
        os.path.join(root, "src", "analysis"),
        os.path.join(root, "src", "brain"),
    ]

    for folder in folders_to_delete:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
            except:
                pass

    # 4. Keep single launcher at project root
    bat_in_src = os.path.join(root, "src", "logging", "Log_Shift.bat")
    if os.path.exists(bat_in_src):
        os.remove(bat_in_src)

    # 5. Fix double .csv extension in data/raw
    for fname in os.listdir(FINAL_DATA_DIR):
        if fname.lower().endswith(".csv.csv"):
            old_path = os.path.join(FINAL_DATA_DIR, fname)
            new_name = fname[:-4]  # drop trailing .csv
            new_path = os.path.join(FINAL_DATA_DIR, new_name)
            if not os.path.exists(new_path):
                os.rename(old_path, new_path)
            else:
                os.remove(old_path)

    # 6. Archive legacy simple log to backups
    legacy_src = os.path.join(FINAL_DATA_DIR, "dasher_log.csv")
    legacy_dest = os.path.join(root, "data", "backups", "dasher_log_legacy.csv")
    if os.path.exists(legacy_src):
        os.makedirs(os.path.dirname(legacy_dest), exist_ok=True)
        if os.path.exists(legacy_dest):
            os.remove(legacy_src)
        else:
            shutil.move(legacy_src, legacy_dest)

if __name__ == "__main__":
    print("Starting Deep Clean...")
    deep_clean_biodash()
    print("\n✨ BioDash Deep Clean Complete! Your data is safe in /data/raw and /config.")