import os
import json
import re
from typing import Optional
# =========================
# 用于导入文件夹类型mod
# =========================

def find_mod_root(folder: str):
    # print("[DEBUG] find_mod_root called with:", folder)

    if not os.path.exists(folder):
        # print("[DEBUG] folder does NOT exist")
        return None

    # 打印当前目录内容
    # try:
        # print("[DEBUG] top-level files:", os.listdir(folder))
    # except Exception as e:
        # print("[DEBUG] cannot list folder:", e)

    # 当前目录是否有 manifest.json
    manifest_path = os.path.join(folder, "manifest.json")
    # print("[DEBUG] checking:", manifest_path)

    if os.path.isfile(manifest_path):
        # print("[DEBUG] manifest.json FOUND at root")
        return folder

    # 向下扫描
    for root, dirs, files in os.walk(folder):
        # print("[DEBUG] walking:", root)
        # print("        files:", files)

        if "manifest.json" in files:
            # print("[DEBUG] manifest.json FOUND at:", root)
            return root

    # print("[DEBUG] manifest.json NOT FOUND")
    return None



def scan_mod_info_from_folder(folder: str) -> dict:
    try:
        mod_root = find_mod_root(folder)
        if not mod_root:
            return {}

        manifest_path = os.path.join(mod_root, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        source_url = ""
        for key in data.get("UpdateKeys", []):
            if isinstance(key, str) and key.startswith("Nexus:"):
                mod_id = key.split(":", 1)[1]
                source_url = f"https://www.nexusmods.com/stardewvalley/mods/{mod_id}"
                break

        return {
            "name": data.get("Name", ""),
            "version": data.get("Version", ""),
            "author": data.get("Author", ""),
            "description": data.get("Description", ""),
            "source_url": source_url,
            "unique_id": data.get("UniqueID", ""),
        }

    except Exception as e:
        print("[DEBUG] scan_mod_info_from_folder failed:", e)
        return {}


def extract_nexus_id_from_filename(filename: str) -> str:
    m = re.search(r"-(\d+)-\d", filename)
    return m.group(1) if m else ""
