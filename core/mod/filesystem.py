import os
import shutil
import uuid
import zipfile
import tempfile
import subprocess

from core.mod.parser import scan_mod_info_from_folder, extract_nexus_id_from_filename
# =========================
#用于导入mod时导入mod内容识别
# =========================

def is_archive(path: str) -> bool:
    return path.lower().endswith((".zip", ".rar", ".7z"))


def extract_archive(archive_path: str, target_dir: str) -> str:
    base_name = os.path.splitext(os.path.basename(archive_path))[0]
    extract_path = os.path.join(target_dir, base_name)
    os.makedirs(extract_path, exist_ok=True)

    if archive_path.lower().endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(extract_path)
        return extract_path

    subprocess.run(
        ["7z", "x", archive_path, f"-o{extract_path}", "-y"],
        check=True
    )
    return extract_path


def copy_folder(src: str, dst_root: str) -> str:
    base = os.path.basename(src.rstrip("/\\"))
    dst = os.path.join(dst_root, base)

    if os.path.exists(dst):
        dst = os.path.join(dst_root, f"{base}_{uuid.uuid4().hex[:6]}")

    shutil.copytree(src, dst)
    return dst


def preview_mod_info_from_archive(archive_path: str) -> dict:
    if not os.path.exists(archive_path):
        return {}

    tmp_dir = tempfile.mkdtemp(prefix="mod_preview_")
    try:
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(tmp_dir)

        info = scan_mod_info_from_folder(tmp_dir)

        if not info.get("nexus_id"):
            info["nexus_id"] = extract_nexus_id_from_filename(
                os.path.basename(archive_path)
            )

        info["source_url"] = (
            f"https://www.nexusmods.com/stardewvalley/mods/{info['nexus_id']}"
            if info.get("nexus_id") else ""
        )

        return info
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
