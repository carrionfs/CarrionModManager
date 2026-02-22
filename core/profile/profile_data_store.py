import json
import os
from core.profile.profile_store import get_profile_root

# =========================
#每个profile的data相关
# =========================

def get_profile_data_path(profile_id: str):
    return os.path.join(
        get_profile_root(profile_id),
        "profile_data.json"
    )


def load_profile_data(profile_id: str):
    path = get_profile_data_path(profile_id)

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile_data(profile_id: str, data):
    path = get_profile_data_path(profile_id)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)