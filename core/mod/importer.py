import os
import uuid

from core.profile.profile_store import (
    get_storage_dir,
    get_active_profile
)

from core.mod.parser import scan_mod_info_from_folder, extract_nexus_id_from_filename
from core.mod.filesystem import is_archive, extract_archive, copy_folder

# =========================
#  导入mod
# =========================
class ModImporter:

    @staticmethod
    def import_mod(data: dict, db, profile_id: str = None) -> str:
        mod_path = data.get("mod_path")
        if not mod_path:
            raise ValueError("未选择 Mod 文件夹或压缩包")

        if profile_id is None:
            profile_id = get_active_profile()

        storage_root = get_storage_dir(profile_id)
        os.makedirs(storage_root, exist_ok=True)

        if is_archive(mod_path):
            final_path = extract_archive(mod_path, storage_root)
        else:
            final_path = copy_folder(mod_path, storage_root)

        info = scan_mod_info_from_folder(final_path)

        nexus_id = info.get("nexus_id") or extract_nexus_id_from_filename(
            os.path.basename(mod_path)
        )
        auto_url = (
            f"https://www.nexusmods.com/stardewvalley/mods/{nexus_id}"
            if nexus_id else ""
        )

        name = data.get("name") or info.get("name", "")
        version = data.get("version") or info.get("version", "")
        author = data.get("author") or info.get("author", "")
        description = data.get("description") or info.get("description", "")
        source_url = data.get("source_url") or auto_url
        category = data.get("category", "默认")

        mod_order = len(db.get_mods_by_category(category)) + 1
        uid = info.get("unique_id")
        if not uid:
            raise ValueError("无法从 manifest.json 读取 UniqueID")

        db.upsert_mod({
            "unique_id": uid,
            "name": name,
            "version": version,
            "author": author,
            "description": description,
            "folder_path": final_path,
            "status": "disabled",
            "category": category,
            "category_order": 9999,
            "mod_order": mod_order,
            "source_url": source_url,
            "image_url": data.get("image_url", "")
        })


        return uid
