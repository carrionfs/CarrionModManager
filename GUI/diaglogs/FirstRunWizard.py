# coding:utf-8
import os
from PyQt5.QtWidgets import QFileDialog, QWidget, QHBoxLayout

from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    BodyLabel,
    LineEdit,
    ToolButton,
    FluentIcon,
    InfoBar,
    InfoBarPosition
)

from core.config.config_manager import (
    set_game_path,
    set_download_dir,
    save_mods_path
)
from core.profile.profile_store import set_profile_root

# =========================
# 首次启动保存路径弹窗
# =========================

class FirstRunWizard(MessageBoxBase):
    """首次启动初始化向导"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ===== 标题 =====
        self.titleLabel = SubtitleLabel("首次使用初始化")
        self.descLabel = BodyLabel(
            "欢迎使用 Mod 管理器。\n\n"
            "首次使用需要完成以下设置："
        )

        # ===== 游戏 Mods 路径 =====
        self.gamePathEdit = LineEdit()
        self.gamePathEdit.setReadOnly(True)
        self.gamePathEdit.setPlaceholderText("请选择游戏 Mods 文件夹")

        self.gameBrowseBtn = ToolButton(FluentIcon.FOLDER)
        self.gameBrowseBtn.clicked.connect(self.chooseGamePath)

        gamePathRow = QWidget()
        gamePathLayout = QHBoxLayout(gamePathRow)
        gamePathLayout.setContentsMargins(0, 0, 0, 0)
        gamePathLayout.addWidget(self.gamePathEdit)
        gamePathLayout.addWidget(self.gameBrowseBtn)

        # ===== Profile 存储路径 =====
        self.profilePathEdit = LineEdit()
        self.profilePathEdit.setReadOnly(True)
        self.profilePathEdit.setPlaceholderText("请选择 Profile 存储根目录")

        self.profileBrowseBtn = ToolButton(FluentIcon.FOLDER)
        self.profileBrowseBtn.clicked.connect(self.chooseProfileRoot)

        profilePathRow = QWidget()
        profilePathLayout = QHBoxLayout(profilePathRow)
        profilePathLayout.setContentsMargins(0, 0, 0, 0)
        profilePathLayout.addWidget(self.profilePathEdit)
        profilePathLayout.addWidget(self.profileBrowseBtn)

        # ===== 下载目录 =====
        self.downloadPathEdit = LineEdit()
        self.downloadPathEdit.setReadOnly(True)
        self.downloadPathEdit.setPlaceholderText("请选择浏览器下载目录")

        self.downloadBrowseBtn = ToolButton(FluentIcon.FOLDER)
        self.downloadBrowseBtn.clicked.connect(self.chooseDownloadDir)

        downloadPathRow = QWidget()
        downloadPathLayout = QHBoxLayout(downloadPathRow)
        downloadPathLayout.setContentsMargins(0, 0, 0, 0)
        downloadPathLayout.addWidget(self.downloadPathEdit)
        downloadPathLayout.addWidget(self.downloadBrowseBtn)

        # ===== Layout =====
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.descLabel)

        self.viewLayout.addWidget(BodyLabel("游戏 Mods 路径"))
        self.viewLayout.addWidget(gamePathRow)

        self.viewLayout.addWidget(BodyLabel("Profile 存储路径"))
        self.viewLayout.addWidget(profilePathRow)

        self.viewLayout.addWidget(BodyLabel("浏览器下载目录"))
        self.viewLayout.addWidget(downloadPathRow)

        self.widget.setMinimumWidth(520)

        # ===== 内部状态 =====
        self._game_path = ""
        self._profile_root = ""
        self._download_dir = ""

    # ---------- Path Choosers ----------

    def chooseGamePath(self):
        path = QFileDialog.getExistingDirectory(self, "选择游戏 Mods 目录")
        if path:
            self._game_path = path
            self.gamePathEdit.setText(path)

    def chooseProfileRoot(self):
        path = QFileDialog.getExistingDirectory(self, "选择 Profile 存储根目录")
        if path:
            self._profile_root = path
            self.profilePathEdit.setText(path)

    def chooseDownloadDir(self):
        path = QFileDialog.getExistingDirectory(self, "选择浏览器下载目录")
        if path:
            self._download_dir = path
            self.downloadPathEdit.setText(path)

    # ---------- Dialog OK ----------

    def accept(self):
        if not (self._game_path and self._profile_root and self._download_dir):
            InfoBar.error(
                "未完成",
                "请完成所有必填设置后再继续",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return

        # ===== 写入配置 =====
        set_game_path(self._game_path)
        save_mods_path(self._game_path)
        set_profile_root(self._profile_root)
        set_download_dir(self._download_dir)

        super().accept()

    # ---------- 外部访问接口（新增） ----------

    @property
    def game_path(self):
        return self._game_path

    @property
    def profile_root(self):
        return self._profile_root

    @property
    def download_dir(self):
        return self._download_dir
