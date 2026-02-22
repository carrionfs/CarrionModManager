from core.config.config_manager import get_nexus_api_key
from core.nexus.nexus_api import validate_api_key
from core.nexus.nexus_api import NexusApiError
from core.nexus.auto_fill import fetch_mod_info,extract_mod_id_from_url
# =========================
#  用于检测mod的更新状态
# =========================

def check_updates_from_nexus(db):
    """
    检测所有 mod 是否有新版本，并写入 latest_version
    """
    api_key = get_nexus_api_key()
    validate_api_key(api_key)

    mods = db.get_all_mods()

    for uid, mod in mods.items():
        source_url = mod.get("source_url")
        if not source_url:
            continue

        mod_id = extract_mod_id_from_url(source_url)
        if not mod_id:
            continue

        try:
            info = fetch_mod_info(api_key, mod_id)
        except NexusApiError:
            continue

        latest = (info.get("version") or "").strip()
        current = (mod.get("version") or "").strip()

        if latest and latest != current:
            db.update_latest_version(uid, latest)
        else:
            db.clear_latest_version(uid)
