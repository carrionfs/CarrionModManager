import json
import os
from core.config.path import CONFIG_PATH

# =========================
# 内部函数
# =========================

def _get_config_path():
    return CONFIG_PATH


def _load_config() -> dict:
    path = _get_config_path()

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_config(cfg: dict):
    path = _get_config_path()

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# =========================
# 对外公开：读取完整 config（for app_entry ）
# =========================

def load_config() -> dict:
    return _load_config()


# =========================
# Mods 路径 
# =========================

def load_mods_path():
    return _load_config().get("mods_path")


def save_mods_path(mods_path: str):
    cfg = _load_config()
    cfg["mods_path"] = mods_path
    _save_config(cfg)


def is_valid_mods_folder(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    try:
        return any(
            os.path.isdir(os.path.join(path, d))
            for d in os.listdir(path)
        )
    except Exception:
        return False


# =========================
#  Nexus API Key 
# =========================

def get_nexus_api_key() -> str:
    return _load_config().get("nexus_api_key", "")


def set_nexus_api_key(key: str):
    cfg = _load_config()
    cfg["nexus_api_key"] = key
    _save_config(cfg)


# =========================
# Game 路径
# =========================

def get_game_path() -> str:
    return _load_config().get("game_path", "")


def set_game_path(path: str):
    cfg = _load_config()
    cfg["game_path"] = path
    _save_config(cfg)


# =========================
# 浏览器下载目录
# =========================

def get_download_dir() -> str:
    cfg = _load_config()
    return cfg.get("download_dir") or os.path.join(
        os.path.expanduser("~"), "Downloads"
    )


def set_download_dir(path: str):
    cfg = _load_config()
    cfg["download_dir"] = path
    _save_config(cfg)


# =========================
# Profile 根目录
# =========================

def get_profiles_root() -> str:
    return _load_config().get("profiles_root", "")


def set_profiles_root(path: str):
    cfg = _load_config()
    cfg["profiles_root"] = path
    _save_config(cfg)


# =========================
#  每个 profile 的 storage 路径（只读）
# =========================

def get_profile_storage_path(profile_id: str) -> str:
    profiles_root = get_profiles_root()
    if not profiles_root:
        return ""
    return os.path.join(profiles_root, profile_id, "storage")


# =========================
# 首次初始化设置（由 FirstRunWizard 或 mark_initialized 调用）
# =========================

def first_time_setup(mods_path: str, download_dir: str, profiles_root: str):
    cfg = _load_config()

    if "mods_path" not in cfg:
        cfg["mods_path"] = mods_path

    if "download_dir" not in cfg:
        cfg["download_dir"] = download_dir

    if "profiles_root" not in cfg:
        cfg["profiles_root"] = profiles_root

    _save_config(cfg)
