# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QWidget
from qfluentwidgets import (
    SettingCardGroup, PushSettingCard, ScrollArea,
    InfoBar, InfoBarPosition, ExpandLayout,
    TitleLabel, IndeterminateProgressBar
)
from qfluentwidgets import FluentIcon as FIF

from core.config.config_manager import (
    set_game_path,
    set_nexus_api_key,
    get_nexus_api_key,
    get_download_dir,
    set_download_dir
)
from core.profile.profile_store import set_profile_root
from core.tasks.auto_fill_worker import AutoFillWorker

# =========================
# 设置页面
# =========================

class SettingsPage(ScrollArea):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db

        self.setObjectName("settings")

        # ===== 页面标题 =====
        self.settingLabel = TitleLabel(self.tr("设置"), self)
        self.settingLabel.setObjectName("settingLabel")
        self.setViewportMargins(0, 120, 0, 20)
        self.settingLabel.move(60, 63)

        # ===== 进度条（初始化但不显示）=====
        self.progressBar = IndeterminateProgressBar(self)
        self.progressBar.setFixedHeight(6)
        self.progressBar.setTextVisible(True)
        self.progressBar.setFormat(self.tr("正在自动补全 Mod 信息..."))
        self.progressBar.setObjectName("autoFillProgressBar")
        self.progressBar.hide()

        # ===== 滚动区域内容 =====
        self.scrollWidget = QWidget(self)
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # ===== 路径设置 =====
        self.pathGroup = SettingCardGroup(self.tr("路径设置"), self.scrollWidget)

        self.gamePathCard = PushSettingCard(
            self.tr("选择文件夹"), FIF.FOLDER,
            self.tr("游戏 Mod 目录"), self.tr("Stardew Valley Mods 文件夹位置"),
            self.pathGroup
        )

        self.profilePathCard = PushSettingCard(
            self.tr("选择文件夹"), FIF.FOLDER,
            self.tr("Profile 根目录"), self.tr("所有 Profile 的数据存储位置"),
            self.pathGroup
        )

        self.downloadDirCard = PushSettingCard(
            self.tr("选择文件夹"), FIF.DOWNLOAD,
            self.tr("浏览器下载目录"), self.tr("用于监听 NexusMods 下载的压缩包"),
            self.pathGroup
        )

        self.pathGroup.addSettingCard(self.downloadDirCard)
        self.pathGroup.addSettingCard(self.gamePathCard)
        self.pathGroup.addSettingCard(self.profilePathCard)

        # ===== Nexus 设置 =====
        self.nexusGroup = SettingCardGroup(self.tr("NexusMods"), self.scrollWidget)

        self.nexusApiCard = PushSettingCard(
            self.tr("设置"), FIF.INFO,
            self.tr("NexusMods API Key"), self.tr("用于获取 Mod 信息、封面图、自动更新"),
            self.nexusGroup
        )

        self.autoFillCard = PushSettingCard(
            self.tr("自动补全"), FIF.DOWNLOAD,
            self.tr("自动补全 Mod 信息"), self.tr("从 NexusMods 获取封面、描述、作者等信息"),
            self.nexusGroup
        )

        self.nexusGroup.addSettingCard(self.nexusApiCard)
        self.nexusGroup.addSettingCard(self.autoFillCard)

        # ===== 布局设置 =====
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(60, 10, 60, 0)
        self.expandLayout.addWidget(self.pathGroup)
        self.expandLayout.addWidget(self.nexusGroup)

        # ===== 信号绑定 =====
        self.gamePathCard.clicked.connect(self.chooseGamePath)
        self.profilePathCard.clicked.connect(self.chooseProfileRoot)
        self.nexusApiCard.clicked.connect(self.setNexusApi)
        self.autoFillCard.clicked.connect(self.autoFillMods)
        self.downloadDirCard.clicked.connect(self.chooseDownloadDir)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "progressBar"):
            self.progressBar.setFixedWidth(self.viewport().width() - 120)
            self.progressBar.move(60, self.settingLabel.y() + self.settingLabel.height() + 10)

    def chooseGamePath(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("选择游戏 Mod 目录"))
        if path:
            set_game_path(path)
            InfoBar.success(
                self.tr("成功"), self.tr("游戏 Mod 目录已保存"),
                parent=self.window(), position=InfoBarPosition.TOP_RIGHT
            )

    def chooseProfileRoot(self):
        from core.config.config_manager import set_profiles_root
        path = QFileDialog.getExistingDirectory(self, self.tr("选择 Profile 根目录"))
        if path:
            set_profile_root(path)
            set_profiles_root(path)
            InfoBar.success(
                self.tr("成功"), self.tr("Profile 根目录已保存"),
                parent=self.window(), position=InfoBarPosition.TOP_RIGHT
            )

    def chooseDownloadDir(self):
        path = QFileDialog.getExistingDirectory(
            self, self.tr("选择浏览器下载目录"), get_download_dir()
        )
        if path:
            set_download_dir(path)
            InfoBar.success(
                self.tr("成功"), self.tr("浏览器下载目录已保存"),
                parent=self.window(), position=InfoBarPosition.TOP_RIGHT
            )

    def setNexusApi(self):
        from GUI.diaglogs.NexusApiDialog import NexusApiDialog
        from core.nexus.nexus_api import validate_api_key, NexusApiError

        dialog = NexusApiDialog(parent=self.window(), default_text=get_nexus_api_key())
        if not dialog.exec():
            return

        key = dialog.apiKey()
        if not key:
            return

        try:
            if validate_api_key(key):
                set_nexus_api_key(key)
                InfoBar.success(
                    self.tr("成功"), self.tr("NexusMods API Key 验证成功，已保存"),
                    parent=self.window(), position=InfoBarPosition.TOP_RIGHT
                )
            else:
                InfoBar.error(
                    self.tr("失败"), self.tr("API Key 无效，请检查后重试"),
                    parent=self.window(), position=InfoBarPosition.TOP_RIGHT
                )
        except NexusApiError as e:
            InfoBar.error(
                self.tr("错误"), str(e),
                parent=self.window(), position=InfoBarPosition.TOP_RIGHT
            )

    def autoFillMods(self):
        from core.profile.profile_store import get_active_profile, get_profile_root

        print("[UI] Auto Fill button clicked")

        profile_id = get_active_profile()
        profile_root = get_profile_root(profile_id)

        self.autoFillCard.setEnabled(False)

        self.progressBar.setFormat(self.tr("正在自动补全 Mod 信息..."))
        self.progressBar.setTextVisible(True)
        self.progressBar.show()
        self.progressBar.start()

        self.worker = AutoFillWorker(self.db.db_path, profile_root)
        self.worker.progress_signal.connect(self.onAutoFillProgress)
        self.worker.finished_signal.connect(self.onAutoFillFinished)
        self.worker.error_signal.connect(self.onAutoFillError)
        self.worker.start()

    def onAutoFillProgress(self, current, total):
        percent = int(current / total * 100)
        self.progressBar.setFormat(self.tr(f"正在自动补全 Mod 信息...（{percent}%）"))

    def onAutoFillFinished(self):
        self.autoFillCard.setEnabled(True)
        self.progressBar.stop()
        self.progressBar.hide()
        InfoBar.success(
            self.tr("成功"), self.tr("已从 NexusMods 自动补全 Mod 信息"),
            parent=self.window(), position=InfoBarPosition.TOP_RIGHT
        )

    def onAutoFillError(self, message):
        self.autoFillCard.setEnabled(True)
        self.progressBar.stop()
        self.progressBar.hide()
        InfoBar.error(
            self.tr("失败"), message,
            parent=self.window(), position=InfoBarPosition.TOP_RIGHT
        )
