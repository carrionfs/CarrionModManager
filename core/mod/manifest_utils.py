import re
# =========================
#用于N网同步时从mainfest提取网址
# =========================
NEXUS_PATTERN = re.compile(r"Nexus:(\d+)", re.IGNORECASE)

def extract_nexus_url(manifest: dict) -> str:
    """
    从 manifest.json 中提取 Nexus Mod URL
    """
    keys = []

    if "UpdateKeys" in manifest:
        keys = manifest.get("UpdateKeys", [])
    elif "UpdateKey" in manifest:
        keys = [manifest.get("UpdateKey")]

    for key in keys:
        if not isinstance(key, str):
            continue

        match = NEXUS_PATTERN.search(key)
        if match:
            mod_id = match.group(1)
            return f"https://www.nexusmods.com/stardewvalley/mods/{mod_id}"

    return ""
