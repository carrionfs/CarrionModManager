from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QLabel

from qfluentwidgets import (
    PushButton, PrimaryPushButton, ToolButton,
    BodyLabel, CheckBox, TitleLabel, TableWidget,
    HyperlinkLabel, InfoBar, setTheme, SubtitleLabel,
    MessageBoxBase, Theme, FluentIcon,
    InfoBarPosition, LineEdit
)

# =========================
# 已弃用，整合进FRW
# =========================

class profileosDialog(MessageBoxBase):
    """首次启动：选择数据存储位置"""

    def __init__(self, parent=None, default_path=""):
        super().__init__(parent)

        self.titleLabel = SubtitleLabel("首次使用，设置数据存储位置")

        self.pathEdit = LineEdit()
        self.pathEdit.setReadOnly(True)
        self.pathEdit.setText(default_path)
        self.pathEdit.setPlaceholderText("请选择 Mod 管理器数据存储位置")

        self.browseButton = PushButton("浏览...")
        self.browseButton.clicked.connect(self.choosePath)

        self.useDefaultCheck = CheckBox("使用默认路径（推荐）")
        self.useDefaultCheck.setChecked(True)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.pathEdit)
        self.viewLayout.addWidget(self.browseButton)
        self.viewLayout.addWidget(self.useDefaultCheck)

        self.widget.setMinimumWidth(420)

        self._selected_path = default_path

    def choosePath(self):
        path = QFileDialog.getExistingDirectory(
            self, "选择数据存储目录"
        )
        if path:
            self._selected_path = path
            self.pathEdit.setText(path)
            self.useDefaultCheck.setChecked(False)

    def useDefault(self) -> bool:
        return self.useDefaultCheck.isChecked()

    def getPath(self) -> str:
        return self._selected_path