from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from qfluentwidgets import SplitFluentWindow, FluentIcon

from core.profile.profile_store import (
    get_profiles,
    get_profile_name,
    get_active_profile,
    set_active_profile,
)

from GUI.moddata.moddata_logic import moddata
from GUI.settings.SettingsPage import SettingsPage

import sys
import os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow_Moudle_select(SplitFluentWindow):
    def __init__(self, db):
        super().__init__()

        self.setWindowTitle("carrion's mod manager")
        icon_path = resource_path("assets/icon/Horse.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1020, 745)

        desktop = QApplication.desktop().availableGeometry()
        self.move(
            desktop.width() // 2 - self.width() // 2,
            desktop.height() // 2 - self.height() // 2
        )

        self.navigationInterface.setExpandWidth(150)
        self.navigationInterface.expand(useAni=False)

        self.db = db
        self.profile_pages = {}

        self.stackedWidget.currentChanged.connect(self.onPageChanged)

        from qfluentwidgets import NavigationItemPosition

        # ===== 设置页 =====
        self.navigationInterface.addSeparator(
            position=NavigationItemPosition.BOTTOM
        )

        self.settings_page = SettingsPage(self, db=self.db)
        self.settings_page.setObjectName("settings")

        self.addSubInterface(
            self.settings_page,
            FluentIcon.SETTING,
            "设置",
            position=NavigationItemPosition.BOTTOM
        )

    def load_profiles(self):
        profiles = get_profiles()
        active = get_active_profile()

        for pid in profiles:
            page = moddata(self, pid, self.db)
            self.profile_pages[pid] = page

            self.addSubInterface(
                page,
                FluentIcon.LIBRARY_FILL,
                get_profile_name(pid)
            )

        if active in self.profile_pages:
            self.switchTo(self.profile_pages[active])
        elif profiles:
            self.switchTo(self.profile_pages[profiles[0]])

    def onPageChanged(self, index):
        widget = self.stackedWidget.widget(index)
        for pid, page in self.profile_pages.items():
            if page is widget:
                set_active_profile(pid)
                break
