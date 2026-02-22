import webbrowser
from core.mod.updater import wait_for_download, install_update

# =========================
#  用于从N网获取更新
# =========================

def has_update(mod: dict) -> bool:
    cur = (mod.get("version") or "").strip()
    latest = (mod.get("latest_version") or "").strip()
    return bool(cur and latest and cur != latest)


def open_files_page(mod: dict):
    """
    打开 Nexus Files 页面（非 Premium 合法入口）
    """
    url = mod.get("source_url")
    if not url:
        return

    if "?tab=files" not in url:
        url = url.rstrip("/") + "?tab=files"

    webbrowser.open(url)


def open_update_page(mod: dict, db=None, on_finished=None):
    """
    UI 统一接口：打开 Mod 更新页面
    """
    if db is None:
        open_files_page(mod)
        return

    start_update_flow(mod, db, on_finished=on_finished)



def ignore_update(mod: dict, db=None):
    """
    UI 统一接口：忽略更新
    """
    if not db:
        return

    uid = mod.get("unique_id")
    if uid:
        db.clear_latest_version(uid)

def start_update_flow(mod: dict, db, on_finished=None):
    open_files_page(mod)

    zip_path = wait_for_download(mod.get("name", ""))
    if not zip_path:
        return

    install_update(zip_path, mod["folder_path"])

    db.update_mod_version(mod["unique_id"], mod["latest_version"])
    db.clear_latest_version(mod["unique_id"])

    if callable(on_finished):
        on_finished()
