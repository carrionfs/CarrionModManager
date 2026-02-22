from qfluentwidgets import MessageBoxBase, SubtitleLabel, LineEdit, PushButton
from PyQt5.QtWidgets import QFileDialog
from core.config.config_manager import is_valid_mods_folder

# =========================
# 修改Mods文件夹的路径弹窗（已弃用）
# =========================

class ModsPathDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.titleLabel = SubtitleLabel("请选择 Stardew Valley 的 Mods 文件夹")
        self.pathEdit = LineEdit()
        self.pathEdit.setPlaceholderText("例如：Stardew Valley/Mods")

        self.browseButton = PushButton("浏览…")
        self.browseButton.clicked.connect(self.browse)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.pathEdit)
        self.viewLayout.addWidget(self.browseButton)

        self.widget.setMinimumWidth(420)

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择 Mods 文件夹")
        if path:
            self.pathEdit.setText(path)

    def getPath(self) -> str:
        path = self.pathEdit.text().strip()
        return path if is_valid_mods_folder(path) else ""
