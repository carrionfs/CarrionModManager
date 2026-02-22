from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from qfluentwidgets import (
    MessageBoxBase,
    LineEdit,
    SubtitleLabel,
    BodyLabel,
    HyperlinkLabel
)

from core.nexus.nexus_api import validate_api_key, NexusApiError

# =========================
# 获取N网API弹窗
# =========================

class NexusApiDialog(MessageBoxBase):
    """Fluent NexusMods API Key Dialog"""

    def __init__(self, parent=None, default_text=""):
        super().__init__(parent)

        # 标题
        self.titleLabel = SubtitleLabel("NexusMods API Key")

        # 说明文字
        self.descLabel = BodyLabel(
            "请输入你的 NexusMods API Key。\n"
            "该 Key 用于获取 Mod 信息、封面图和自动更新。"
        )

        # 🔗 超链接（手动绑定点击事件）
        self.linkLabel = HyperlinkLabel(
            "👉 点击这里前往 NexusMods 官网获取 API Key",
            ""
        )
        self.linkLabel.clicked.connect(self.openNexusPage)

        # 输入框
        self.apiEdit = LineEdit()
        self.apiEdit.setPlaceholderText("NexusMods API Key")
        self.apiEdit.setText(default_text)

        # 下载额度标签（初始为空）
        self.quotaLabel = BodyLabel("")
        self.quotaLabel.setStyleSheet("color: #0078D4; font-weight: bold;")

        # 布局
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.descLabel)
        layout.addWidget(self.linkLabel)
        layout.addWidget(self.apiEdit)
        layout.addWidget(self.quotaLabel)

        self.viewLayout.addLayout(layout)

        self.yesButton.setText("确认")
        self.cancelButton.setText("取消")
        self.yesButton.clicked.connect(self.onConfirmClicked)

    def openNexusPage(self):
        QDesktopServices.openUrl(
            QUrl("https://www.nexusmods.com/users/myaccount?tab=api")
        )

    def apiKey(self) -> str:
        return self.apiEdit.text().strip()

    def onConfirmClicked(self):
        api_key = self.apiKey()
        try:
            result = validate_api_key(api_key)
            if result["valid"]:
                left = result.get("daily_left", "?")
                limit = result.get("daily_limit", "?")
                self.quotaLabel.setText(f"今日剩余下载额度：{left} / {limit}")
            else:
                self.quotaLabel.setText("❌ API Key 无效，请重新输入")
        except NexusApiError as e:
            self.quotaLabel.setText(f"⚠️ {str(e)}")
