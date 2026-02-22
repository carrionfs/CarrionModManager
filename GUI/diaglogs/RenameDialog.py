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
# 修改配置名称弹窗
# =========================

class RenameDialog(MessageBoxBase):
    """ 重命名对话框 """
    def __init__(self, parent=None, old_name=""):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("修改配置名称")
        self.nameEdit = LineEdit()
        self.nameEdit.setPlaceholderText("请输入新的配置名称")
        self.nameEdit.setText(old_name)
        self.nameEdit.setClearButtonEnabled(True)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameEdit)
        self.widget.setMinimumWidth(350)
    def getName(self):
        return self.nameEdit.text()

