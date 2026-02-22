import re
import requests
from core.config.config_manager import get_nexus_api_key
from core.nexus.nexus_api import validate_api_key, NexusApiError
from core.utils.image_cache import download_image

# =========================
#用于从N网获取mod信息自动填入
# =========================

def extract_mod_id_from_url(url: str):
    if not url:
        return None
    m = re.search(r"/mods/(\d+)", url)
    return int(m.group(1)) if m else None


def fetch_mod_info(api_key, mod_id):
    print(f"[NEXUS] Fetching mod info: mod_id={mod_id}")

    resp = requests.get(
        f"https://api.nexusmods.com/v1/games/stardewvalley/mods/{mod_id}.json",
        headers={"apikey": api_key},
        timeout=8
    )

    print(f"[NEXUS] Status: {resp.status_code}")

    if resp.status_code != 200:
        raise NexusApiError(f"Nexus API 错误: {resp.status_code}")

    data = resp.json()
    print("[NEXUS] Name:", data.get("name"))
    print("[NEXUS] Picture URL:", data.get("picture_url"))
    return data


def search_mod(api_key, keyword):
    resp = requests.get(
        f"https://api.nexusmods.com/v1/games/stardewvalley/mods.json?terms={keyword}",
        headers={"apikey": api_key},
        timeout=8
    )
    return resp.json() if resp.status_code == 200 else []

def auto_fill_single_mod(db, profile_root, uid, mod):
    api_key = get_nexus_api_key()
    result = validate_api_key(api_key)
    if not result.get("valid"):
        raise NexusApiError("API Key 无效或未设置")

    mod_id = extract_mod_id_from_url(mod.get("source_url"))

    if not mod_id:
        results = search_mod(api_key, mod.get("name", ""))
        if results:
            mod_id = results[0].get("mod_id")
            if mod_id:
                url = f"https://www.nexusmods.com/stardewvalley/mods/{mod_id}"
                db.update_mod_source_url(uid, url)

    if not mod_id:
        return

    info = fetch_mod_info(api_key, mod_id)

    db.update_mod_description(uid, info.get("summary") or "")
    db.update_mod_author(uid, info.get("author") or "")
    db.update_mod_version(uid, info.get("version") or "")

    local_image = download_image(
        info.get("picture_url"),
        profile_root
    )

    if local_image:
        db.update_mod_image(uid, local_image)

# def auto_fill_mod_info(db, profile_root: str):
#     """
#     自动补全 Mod 信息（图片永久缓存到 profile/.cache）
#     """
#     print("\n========== AUTO FILL START ==========")
#
#     api_key = get_nexus_api_key()
#     result = validate_api_key(api_key)
#     if not result.get("valid"):
#         raise NexusApiError("API Key 无效或未设置")
#
#     mods = db.get_all_mods()
#     print(f"[AUTO FILL] Mods count in DB: {len(mods)}")
#
#     for uid, mod in mods.items():
#         print(f"\n[AUTO FILL] Processing UID: {uid}")
#
#         mod_id = extract_mod_id_from_url(mod.get("source_url"))
#         if not mod_id:
#             results = search_mod(api_key, mod.get("name", ""))
#             if results:
#                 mod_id = results[0].get("mod_id")
#                 if mod_id:
#                     url = f"https://www.nexusmods.com/stardewvalley/mods/{mod_id}"
#                     db.update_mod_source_url(uid, url)
#
#         if not mod_id:
#             print("  [SKIP] No mod_id found")
#             continue
#
#         info = fetch_mod_info(api_key, mod_id)
#
#         db.update_mod_description(uid, info.get("summary") or "")
#         db.update_mod_author(uid, info.get("author") or "")
#         db.update_mod_version(uid, info.get("version") or "")

        print("  [IMAGE] Downloading image")
        local_image = download_image(
            info.get("picture_url"),
            profile_root
        )

        if local_image:
            db.update_mod_image(uid, local_image)

    print("========== AUTO FILL END ==========\n")

