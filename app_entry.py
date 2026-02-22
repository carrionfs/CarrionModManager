# coding:utf-8
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QSize, QTimer, QEventLoop
from PyQt5.QtGui import QIcon
from qfluentwidgets import SplashScreen
from qframelesswindow import FramelessWindow

# =========================================================
# profile / config
from core.profile.profile_store import (
    init_profile_store,
    is_initialized,
    mark_initialized,
    get_active_profile,
    get_profile_root
)
from core.config.config_manager import (
    get_game_path,
    get_download_dir,
    load_mods_path,
    load_config,
)

# =========================================================
# FRW
from GUI.diaglogs.FirstRunWizard import FirstRunWizard

# =========================================================
# core init & UI
from core.app.init_core import init_core
from main_UI import MainWindow_Moudle_select
from core.database.database import DatabaseManager

import sys
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def need_first_run() -> bool:
    return not (
        get_game_path()
        and load_mods_path()
        and get_download_dir()
    )


def has_loose_mods(mods_root: str) -> bool:
    if not mods_root or not os.path.isdir(mods_root):
        return False

    for name in os.listdir(mods_root):
        path = os.path.join(mods_root, name)
        if not os.path.isdir(path):
            continue
        if "_" in name and name.split("_", 1)[0].isdigit():
            continue
        return True

    return False


class SplashWindow(FramelessWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carrion's Mod Manager")
        icon_path = resource_path("assets/icon/Horse.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1020, 750)
        desktop = QApplication.desktop().availableGeometry()
        self.move(
            desktop.width() // 2 - self.width() // 2,
            desktop.height() // 2 - self.height() // 2
        )

        # 判断是否首次启动
        config = load_config()
        profiles_root = config.get("profiles_root")
        init_profile_store(meta_root=os.path.join(os.path.dirname(__file__), "data"), profiles_root=profiles_root)

        if not is_initialized() or need_first_run():
            # ❌ 首次启动：不显示 splash，直接初始化
            self.initApp(showSplash=False)
        else:
            # ✅ 正常启动：显示 splash
            self.splash = SplashScreen(self.windowIcon(), self)
            self.splash.setIconSize(QSize(96, 96))
            self.show()
            self.splash.show()
            QApplication.processEvents()
            QTimer.singleShot(100, lambda: self.initApp(showSplash=True))

    def initApp(self, showSplash: bool):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DATA_ROOT = os.path.join(BASE_DIR, "data")

        config = load_config()
        profiles_root = config.get("profiles_root")

        init_profile_store(
            meta_root=DATA_ROOT,
            profiles_root=profiles_root
        )

        dummy_parent = QWidget()
        dummy_parent.setWindowTitle("Initializing...")
        dummy_parent.resize(900, 600)
        dummy_parent.show()

        if not is_initialized() or need_first_run():
            wizard = FirstRunWizard(dummy_parent)

            if not wizard.exec():
                sys.exit(0)

            mark_initialized(
                mods_path=wizard.game_path,
                download_dir=wizard.download_dir
            )

            config = load_config()
            profiles_root = config.get("profiles_root")

            init_profile_store(
                meta_root=DATA_ROOT,
                profiles_root=profiles_root
            )

            print("[ENTRY] After wizard, profiles_root =", profiles_root)

        dummy_parent.close()

        mods_root = load_mods_path()

        if has_loose_mods(mods_root):
            print("[ENTRY] Loose mods detected, running init_core()")
            db = init_core()
        else:
            print("[ENTRY] Mods already categorized, skip init_core()")
            active_profile = get_active_profile()
            profile_root = get_profile_root(active_profile)
            db_path = os.path.join(profile_root, "mods.db")
            db = DatabaseManager(db_path)

        # 模拟加载延迟（可选）
        loop = QEventLoop(self)
        QTimer.singleShot(300, loop.quit)
        loop.exec()

        # 启动主窗口
        self.main = MainWindow_Moudle_select(db=db)
        self.main.show()
        self.main.load_profiles()

        # 关闭 splash 和自身
        if showSplash:
            self.splash.finish()
        self.close()


def main():
    app = QApplication(sys.argv)
    splash = SplashWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
