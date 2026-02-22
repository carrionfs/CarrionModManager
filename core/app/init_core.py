import os

from core.mod.scanner import ModScanner
from core.mod.sync_manager import SyncManager
from core.database.database import DatabaseManager
from core.profile.profile_store import (
    init_profile_store,
    get_active_profile,
    get_storage_dir,
    get_profile_root,
)
from core.config.config_manager import load_mods_path


def init_core():
    """
    正式应用用的初始化入口
    """

    # =========================
    #  初始化 Profile 系统
    # =========================
    init_profile_store()

    # =========================
    #  Mods 根目录
    # =========================
    mods_root = load_mods_path()
    if not mods_root:
        raise RuntimeError("Mods 路径未配置")

    if not os.path.isdir(mods_root):
        raise RuntimeError(f"Mods 路径不存在: {mods_root}")

    # =========================
    #  当前 Profile
    # =========================
    active_profile = get_active_profile()

    profile_root = get_profile_root(active_profile)
    storage_path = get_storage_dir(active_profile)

    # =========================
    #  每个 Profile 独立数据库
    # =========================
    db_path = os.path.join(profile_root, "mods.db")
    db = DatabaseManager(db_path)

    # =========================
    #  Scanner
    # =========================
    game_scanner = ModScanner(mods_root)
    storage_scanner = ModScanner(storage_path)

    # =========================
    #   Sync
    # =========================
    sync = SyncManager(
        game_scanner=game_scanner,
        storage_scanner=storage_scanner,
        db=db,
        storage_path=storage_path
    )

    sync.sync()

    return db