import os
import json
from typing import Dict, Optional
from core.config import config_manager  # ✅ 新增导入
import sys

# =========================
#profile文件的生成及管理
# =========================

def get_base_dir():
    if hasattr(sys, '_MEIPASS'):
        # onefile 才会走这里
        return os.path.dirname(sys.executable)
    else:
        # 开发 or onedir
        return os.path.dirname(os.path.abspath(sys.argv[0]))

# ==================== 常量 ====================

PROFILE_META_FILE = "profile.json"

# ==================== 内部状态 ====================

_meta_root: Optional[str] = None          # data 目录
_profiles_root: Optional[str] = None     # profile 目录
_profiles_file: Optional[str] = None
_initialized: bool = False


# ==================== 初始化 ====================

def init_profile_store(meta_root: Optional[str] = None,
                       profiles_root: Optional[str] = None):
    global _meta_root, _profiles_root, _profiles_file, _initialized

    # 如果已经 set 过，就不要覆盖
    if meta_root is not None:
        _meta_root = os.path.abspath(meta_root)
    elif _meta_root is None:
        _meta_root = os.path.join(get_base_dir(), "data")

    if profiles_root is not None:
        _profiles_root = os.path.abspath(profiles_root)
    elif _profiles_root is None:
        _profiles_root = os.path.join(get_base_dir(), "profile")

    os.makedirs(_meta_root, exist_ok=True)
    os.makedirs(_profiles_root, exist_ok=True)

    _profiles_file = os.path.join(_meta_root, PROFILE_META_FILE)


# ==================== 状态接口 ====================

def is_initialized() -> bool:
    return _load().get("initialized", False)





def mark_initialized(mods_path=None, download_dir=None):
    global _profiles_root  # 确保使用的是当前设置的路径

    data = _load()
    data["initialized"] = True

    # 如果没有 active_profile，设置默认 profile
    if "active_profile" not in data:
        default_id = "default"
        data["active_profile"] = default_id

        if "profiles" not in data:
            data["profiles"] = {}

        if default_id not in data["profiles"]:
            data["profiles"][default_id] = {"name": "默认配置"}

        # 确保目录存在
        if _profiles_root is None:
            raise RuntimeError("未设置 profiles_root，请先调用 init_profile_store()")

        _ensure_profile_dirs(default_id)

    _save(data)

    # 同步写入 config.json
    if mods_path and download_dir:
        from core.config import config_manager  # 避免循环导入
        config_manager.first_time_setup(
            mods_path=mods_path,
            download_dir=download_dir,
            profiles_root=_profiles_root
        )


    if mods_path and download_dir:
        config_manager.first_time_setup(
            mods_path=mods_path,
            download_dir=download_dir,
            profiles_root=_profiles_root
        )


def get_meta_root() -> str:
    _ensure_initialized()
    return _meta_root


def get_profiles_root() -> str:
    _ensure_initialized()
    return _profiles_root


def get_active_profile() -> str:
    data = _load()
    active = data.get("active_profile")
    if not active:
        raise RuntimeError("尚未设置 active_profile，请先调用 set_active_profile()")
    return active


def set_active_profile(profile_id: str):
    data = _load()
    data["active_profile"] = profile_id
    _save(data)


def set_profile_root(path: str):
    global _profiles_root

    path = os.path.abspath(os.path.normpath(path))
    os.makedirs(path, exist_ok=True)

    _profiles_root = path


def set_meta_root(path: str):
    global _meta_root

    path = os.path.abspath(os.path.normpath(path))
    os.makedirs(path, exist_ok=True)

    _meta_root = path


# ==================== Profile 信息 ====================

def get_profiles() -> Dict[str, dict]:
    return _load()["profiles"]


def get_profile_name(profile_id: str) -> str:
    return get_profiles().get(profile_id, {}).get("name", profile_id)


def rename_profile(profile_id: str, new_name: str):
    data = _load()
    data["profiles"][profile_id]["name"] = new_name
    _save(data)


# ==================== Profile 路径 ====================

def get_profile_root(profile_id: str) -> str:
    return os.path.join(_profiles_root, profile_id)


def get_disabled_dir(profile_id: str) -> str:
    return os.path.join(get_profile_root(profile_id), "disabled")


def get_storage_dir(profile_id: str) -> str:
    return os.path.join(get_profile_root(profile_id), "storage")


def get_data_json_path(profile_id: str) -> str:  # 新增：每个 profile 的 data.json 路径
    return os.path.join(get_profile_root(profile_id), "data.json")


# ==================== 内部工具 ====================

def _ensure_profile_dirs(profile_id: str):
    os.makedirs(get_profile_root(profile_id), exist_ok=True)
    os.makedirs(get_disabled_dir(profile_id), exist_ok=True)
    os.makedirs(get_storage_dir(profile_id), exist_ok=True)


def _ensure_initialized():
    if not _initialized:
        raise RuntimeError("profile_store 未初始化")


def _load():
    if not os.path.exists(_profiles_file):
        os.makedirs(os.path.dirname(_profiles_file), exist_ok=True)

        default_data = {
            "initialized": False,
            "profiles": {}
        }

        with open(_profiles_file, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)

        return default_data

    with open(_profiles_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    with open(_profiles_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
