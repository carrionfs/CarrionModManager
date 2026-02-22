import os
import time
import zipfile
import shutil
from typing import Optional
from core.config.config_manager import get_download_dir

# =========================
#  用于从N网更新mod
# =========================

_TEMP_EXTS = (".crdownload", ".part", ".download")


def wait_for_download(mod_name: str, timeout: int = 300) -> Optional[str]:
    print(f"[UPDATE] Waiting for download: {mod_name}")
    start = time.time()
    download_dir = get_download_dir()

    while time.time() - start < timeout:
        try:
            files = os.listdir(download_dir)
        except Exception as e:
            print("[UPDATE] Cannot access download dir:", e)
            return None

        zip_candidates = []

        for fname in files:
            if not fname.lower().endswith(".zip"):
                continue

            path = os.path.join(download_dir, fname)

            if any(os.path.exists(path + ext) for ext in _TEMP_EXTS):
                continue

            if mod_name.lower() in fname.lower():
                print(f"[UPDATE] Found zip by name: {path}")
                return path

            zip_candidates.append(path)

        if zip_candidates:
            latest = max(zip_candidates, key=os.path.getmtime)
            print(f"[UPDATE] Fallback to latest zip: {latest}")
            return latest

        time.sleep(1)

    print("[UPDATE] Download timeout")
    return None


def safe_remove(path: str, retries: int = 10, delay: float = 1.0):
    """
    安全删除文件，等待外部程序释放文件锁
    """
    for i in range(retries):
        try:
            os.remove(path)
            print(f"[UPDATE] Removed zip: {path}")
            return
        except PermissionError:
            print(f"[UPDATE] Zip in use, retry {i + 1}/{retries}")
            time.sleep(delay)

    print(f"[UPDATE] Failed to remove zip (in use): {path}")


def install_update(zip_path: str, target_mod_path: str):
    print(f"[UPDATE] Installing from {zip_path}")

    temp_dir = zip_path + "_tmp"
    backup_dir = target_mod_path + "_backup"

    os.makedirs(temp_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(temp_dir)

    entries = os.listdir(temp_dir)
    extracted_root = (
        os.path.join(temp_dir, entries[0])
        if len(entries) == 1
        else temp_dir
    )

    if os.path.exists(target_mod_path):
        shutil.move(target_mod_path, backup_dir)

    try:
        shutil.move(extracted_root, target_mod_path)
    except Exception:
        if os.path.exists(backup_dir):
            shutil.move(backup_dir, target_mod_path)
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir, ignore_errors=True)

        safe_remove(zip_path)

    print("[UPDATE] Install complete")
