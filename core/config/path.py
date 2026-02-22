import json
import os
import sys

# =========================
# 固定 config.json 位置（改为 AppData）
# =========================

def _get_appdata_config_dir():
    """
    获取 AppData 配置目录：
    C:/Users/用户名/AppData/Roaming/CarrionModManager/
    """
    appdata = os.getenv("APPDATA")

    # 如果极端情况下 APPDATA 不存在
    if not appdata:
        appdata = os.path.expanduser("~")

    app_dir = os.path.join(appdata, "CarrionModManager")
    os.makedirs(app_dir, exist_ok=True)

    return app_dir


CONFIG_PATH = os.path.join(_get_appdata_config_dir(), "config.json")

# =========================
# ⭐ 应用程序根目录（用于 tools 等资源）
# =========================

def get_app_base_dir():
    """
    获取程序根目录：
    - 开发环境：项目目录
    - 打包后：PyInstaller 临时目录
    """
    if getattr(sys, "frozen", False):
        return sys._MEIPASS

    return os.path.dirname(os.path.abspath(__file__))


def get_xnbcli_path():
    return os.path.join(get_app_base_dir(), "tools", "xnbcli-windows-x64")

# =========================
# xnbcli 工具路径
# =========================

def get_xnbcli_path():
    return os.path.join(get_app_base_dir(), "tools", "xnbcli-windows-x64")

# =========================
# 内部工具
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
# 路径规范化
# =========================

def _normalize_path(path: str) -> str:
    if not path:
        return ""
    return os.path.abspath(os.path.normpath(path))


def _ensure_game_root(path: str) -> str:
    """
    如果用户误选了 Mods 目录，则自动修正为游戏根目录
    """
    path = _normalize_path(path)

    if path.lower().endswith("mods"):
        return os.path.dirname(path)

    return path


# =========================
# Mods 路径
# =========================

def load_mods_path() -> str:
    return _load_config().get("mods_path", "")


def save_mods_path(mods_path: str):
    mods_path = _normalize_path(mods_path)

    cfg = _load_config()
    cfg["mods_path"] = mods_path
    _save_config(cfg)


def is_valid_mods_folder(path: str) -> bool:
    path = _normalize_path(path)

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
# Nexus API Key
# =========================

def get_nexus_api_key() -> str:
    return _load_config().get("nexus_api_key", "")


def set_nexus_api_key(key: str):
    cfg = _load_config()
    cfg["nexus_api_key"] = key
    _save_config(cfg)


# =========================
# Game 根目录
# =========================

def get_game_path() -> str:
    cfg = _load_config()
    path = cfg.get("game_path", "")

    if not path:
        return ""

    path = _ensure_game_root(path)

    # 自动修正存储错误
    if path != cfg.get("game_path"):
        cfg["game_path"] = path
        _save_config(cfg)

    return path


def set_game_path(path: str):
    path = _ensure_game_root(path)

    cfg = _load_config()
    cfg["game_path"] = path

    # 自动同步 Mods 目录
    mods_path = os.path.join(path, "Mods")
    cfg["mods_path"] = mods_path

    _save_config(cfg)


# =========================
# 下载目录
# =========================

def get_download_dir() -> str:
    cfg = _load_config()
    return cfg.get("download_dir") or os.path.join(
        os.path.expanduser("~"), "Downloads"
    )


def set_download_dir(path: str):
    path = _normalize_path(path)

    cfg = _load_config()
    cfg["download_dir"] = path
    _save_config(cfg)


# =========================
# Profile 根目录
# =========================

def get_profiles_root() -> str:
    cfg = _load_config()
    return cfg.get("profiles_root", "")


def set_profiles_root(path: str):
    path = _normalize_path(path)

    cfg = _load_config()
    cfg["profiles_root"] = path
    _save_config(cfg)