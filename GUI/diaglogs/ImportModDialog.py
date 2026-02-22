import os
import tempfile
import time

from PyQt5.QtWidgets import (
    QFileDialog, QLabel, QApplication, QWidget, QHBoxLayout, QVBoxLayout
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QEvent
from qfluentwidgets import (
    MessageBoxBase, LineEdit, TextEdit,
    PrimaryPushButton, RoundMenu, InfoBar, InfoBarPosition,
    ToolButton, FluentIcon
)
from PyQt5.QtWidgets import QAction
from core.mod.parser import scan_mod_info_from_folder
from core.mod.filesystem import preview_mod_info_from_archive

# =========================
# 导入mod弹窗
# =========================

class ImportModDialog(MessageBoxBase):
    """导入 MOD"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 隐藏 MessageBoxBase 自带标题栏
        if hasattr(self, "headerWidget"):
            self.headerWidget.hide()

        self.mod_path = ""
        self.image_path = ""

        # ================= 顶部图片 =================
        self.preview = QLabel()
        self.preview.setFixedSize(520, 200)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("""
            QLabel {
                background-color: rgba(0,0,0,20);
                border-radius: 10px;
            }
        """)
        self.viewLayout.addWidget(self.preview)

        # 选择图片按钮
        self.btnChooseImg = PrimaryPushButton("选择图片")
        self.btnChooseImg.clicked.connect(self.choose_image)
        self.viewLayout.addWidget(self.btnChooseImg)

        # ================= 中间双列布局 =================
        form_container = QWidget()
        form_layout = QHBoxLayout(form_container)
        form_layout.setSpacing(20)

        # 左列
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        # left_col.addWidget(SubtitleLabel("名称"))
        self.nameEdit = LineEdit()
        self.nameEdit.setPlaceholderText("Mod 名称")
        left_col.addWidget(self.nameEdit)

        # left_col.addWidget(SubtitleLabel("作者"))
        self.authorEdit = LineEdit()
        self.authorEdit.setPlaceholderText("作者（可选）")
        left_col.addWidget(self.authorEdit)

        # left_col.addWidget(SubtitleLabel("版本"))
        self.versionEdit = LineEdit()
        self.versionEdit.setPlaceholderText("版本号，例如 1.0.0")
        left_col.addWidget(self.versionEdit)

        # left_col.addWidget(SubtitleLabel("分类"))
        self.categoryEdit = LineEdit()
        self.categoryEdit.setPlaceholderText("分类，例如：默认 / 家具 / 美化")
        left_col.addWidget(self.categoryEdit)

        # 右列
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        # right_col.addWidget(SubtitleLabel("URL"))
        self.sourceEdit = LineEdit()
        self.sourceEdit.setPlaceholderText("Mod 发布页面 URL（可选）")
        right_col.addWidget(self.sourceEdit)

        # right_col.addWidget(SubtitleLabel("描述"))
        self.descEdit = TextEdit()
        self.descEdit.setPlaceholderText("Mod 描述")
        self.descEdit.setFixedHeight(120)
        right_col.addWidget(self.descEdit)

        form_layout.addLayout(left_col)
        form_layout.addLayout(right_col)
        self.viewLayout.addWidget(form_container)

        # ================= 底部：Mod 路径选择 =================
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setSpacing(10)

        self.pathEdit = LineEdit()
        self.pathEdit.setPlaceholderText("未选择 Mod 文件夹或压缩包")
        self.pathEdit.setReadOnly(True)

        # 图标按钮（FolderAdd）
        self.btnChooseMod = ToolButton(FluentIcon.FOLDER_ADD)
        self.btnChooseMod.setToolTip("选择 Mod 文件夹或压缩包")
        self.btnChooseMod.clicked.connect(self.choose_mod_path)

        bottom_layout.addWidget(self.pathEdit)
        bottom_layout.addWidget(self.btnChooseMod)

        self.viewLayout.addWidget(bottom_container)

        # ================= 按钮 =================
        self.yesButton.setText("导入")
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(560)

        # 右键菜单支持粘贴图片
        self.preview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preview.customContextMenuRequested.connect(self._show_image_menu)
        self.preview.installEventFilter(self)

    # ================= 选择 Mod：弹出菜单 =================
    def choose_mod_path(self):
        menu = RoundMenu(self)

        act_folder = QAction("选择 Mod 文件夹", self)
        act_archive = QAction("选择压缩包 (.zip/.rar/.7z)", self)

        act_folder.triggered.connect(self._choose_folder)
        act_archive.triggered.connect(self._choose_archive)

        menu.addAction(act_folder)
        menu.addAction(act_archive)

        menu.exec(self.btnChooseMod.mapToGlobal(self.btnChooseMod.rect().bottomLeft()))

    def _choose_folder(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "选择 Mod 文件夹",
            ""
        )
        if not path:
            return

        self.mod_path = path
        self.pathEdit.setText(path)

        # 兜底名称（文件夹名）
        base = os.path.basename(path.rstrip("/\\"))
        self.nameEdit.setText(base)

        # 自动扫描文件夹内 manifest.json
        info = scan_mod_info_from_folder(path)

        # 自动填充（只在有值时覆盖）
        if info.get("name"):
            self.nameEdit.setText(info["name"])

        if info.get("version"):
            self.versionEdit.setText(info["version"])

        if info.get("author"):
            self.authorEdit.setText(info["author"])

        if info.get("description"):
            self.descEdit.setPlainText(info["description"])

        if info.get("source_url"):
            self.sourceEdit.setText(info["source_url"])

    def _choose_archive(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择压缩包",
            "",
            "压缩包 (*.zip *.rar *.7z)"
        )
        if not path:
            return

        self.mod_path = path
        self.pathEdit.setText(path)

        # 自动识别名称（来自文件名）
        base = os.path.basename(path)
        if "." in base:
            base = base.split(".")[0]
        self.nameEdit.setText(base)

        # 自动扫描压缩包内部信息
        info = preview_mod_info_from_archive(path)

        # 自动填充 UI（只填空字段）
        if info.get("name"):
            self.nameEdit.setText(info["name"])

        if info.get("version"):
            self.versionEdit.setText(info["version"])

        if info.get("author"):
            self.authorEdit.setText(info["author"])

        if info.get("description"):
            self.descEdit.setPlainText(info["description"])

        if info.get("source_url"):
            self.sourceEdit.setText(info["source_url"])

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
        if not self.mod_path:
            InfoBar.error(
                title='路径错误❌',
                content="请先选择 Mod 文件夹或压缩包",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            return {}

        return {
            "mod_path": self.mod_path,
            "name": self.nameEdit.text().strip(),
            "description": self.descEdit.toPlainText().strip(),
            "version": self.versionEdit.text().strip(),
            "author": self.authorEdit.text().strip(),
            "category": self.categoryEdit.text().strip() or "默认",
            "source_url": self.sourceEdit.text().strip(),
            "image_url": self.image_path
        }
