import os
import tempfile
import time

from PyQt5.QtWidgets import QFileDialog, QApplication, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QEvent

from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit, TextEdit,
    PrimaryPushButton, RoundMenu
)
from PyQt5.QtWidgets import QAction

# =========================
# 修改mod信息弹窗
# =========================
class EditModDialog(MessageBoxBase):
    """修改 MOD 信息"""
    def _add_form_block(self, title, widget):
        label = SubtitleLabel(title)
        self.viewLayout.addWidget(label)
        self.viewLayout.addWidget(widget)

    def __init__(self, mod: dict, parent=None):
        super().__init__(parent)

        self.mod = mod
        self.image_path = mod.get("image_url", "") or ""

        # ================= 标题 =================
        self.titleLabel = SubtitleLabel("修改MOD信息")
        self.viewLayout.addWidget(self.titleLabel)

        # ================= 图片预览 =================
        self.preview = QLabel()
        self.preview.setFixedSize(500, 180)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("""
            QLabel {
                background-color: rgba(0,0,0,20);
                border-radius: 10px;
            }
        """)
        self.viewLayout.addWidget(self.preview)

        self.preview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preview.customContextMenuRequested.connect(self._show_image_menu)
        self.preview.installEventFilter(self)

        # ================= 选择图片 =================
        self.btnChooseImg = PrimaryPushButton("选择图片")
        self.btnChooseImg.clicked.connect(self.choose_image)
        self.viewLayout.addWidget(self.btnChooseImg)

        # ================= 表单 =================
        self.nameEdit = LineEdit()
        self.nameEdit.setText(mod.get("name", ""))
        self.nameEdit.setPlaceholderText("请输入 Mod 名称")
        self.viewLayout.addWidget(self.nameEdit)

        self.descEdit = TextEdit()
        self.descEdit.setPlainText(mod.get("description", ""))
        self.descEdit.setPlaceholderText("请输入 Mod 描述")
        self.descEdit.setFixedHeight(110)
        self.viewLayout.addWidget(self.descEdit)

        self.versionEdit = LineEdit()
        self.versionEdit.setText(mod.get("version", ""))
        self.versionEdit.setPlaceholderText("例如：1.0.0")
        self.viewLayout.addWidget(self.versionEdit)

        self.categoryEdit = LineEdit()
        self.categoryEdit.setText(mod.get("category", "默认"))
        self.categoryEdit.setPlaceholderText("例如：家具 / 功能 / 美化")
        self.viewLayout.addWidget(self.categoryEdit)

        self.sourceEdit = LineEdit()
        self.sourceEdit.setText(mod.get("source_url", ""))
        self.sourceEdit.setPlaceholderText("Mod 发布页面 URL")
        self.viewLayout.addWidget(self.sourceEdit)
        # ================= 按钮 =================
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(520)

        self._refresh_preview()

    # ================= 图片显示 =================
    def _refresh_preview(self):
        if not self.image_path or not os.path.exists(self.image_path):
            self.preview.clear()
            self.preview.setText("无图片")
            return

        pix = QPixmap(self.image_path)
        if pix.isNull():
            self.preview.clear()
            return

        pix = pix.scaled(
            self.preview.width(),
            self.preview.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.preview.setPixmap(pix)

    # ================= 选择图片 =================
    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self.image_path = path
            self._refresh_preview()

    # ================= 剪贴板 =================
    def paste_image_from_clipboard(self):
        pix = QApplication.clipboard().pixmap()
        if pix and not pix.isNull():
            path = os.path.join(
                tempfile.gettempdir(),
                f"mod_image_{int(time.time())}.png"
            )
            pix.save(path, "PNG")
            self.image_path = path
            self._refresh_preview()

    def _show_image_menu(self, pos):
        menu = RoundMenu(self.preview)
        act = QAction("从剪贴板粘贴图片", self.preview)
        act.triggered.connect(self.paste_image_from_clipboard)
        menu.addAction(act)
        menu.exec(self.preview.mapToGlobal(pos))

    def eventFilter(self, obj, event):
        if hasattr(self, "preview"):
            if obj is self.preview and event.type() == QEvent.KeyPress:
                if event.matches(QEvent.Paste):
                    self.paste_image_from_clipboard()
                    return True
        return super().eventFilter(obj, event)

    # ================= 返回数据 =================
    def get_data(self):
        return {
            "name": self.nameEdit.text().strip(),
            "description": self.descEdit.toPlainText().strip(),
            "version": self.versionEdit.text().strip(),
            "category": self.categoryEdit.text().strip() or "默认",
            "source_url": self.sourceEdit.text().strip(),
            "image_url": self.image_path
        }
