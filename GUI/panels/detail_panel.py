import os
from PyQt5.QtGui import QPixmap, QDesktopServices
from PyQt5.QtCore import Qt, QUrl

# =========================
#  软件右侧信息栏相关
# =========================

class DetailPanel:
    def __init__(self, parent):
        self.parent = parent
        self.table = parent.tableView
        self.db = parent.db
        self.sync_manager = getattr(parent, "sync_manager", None)

        self.name_label = parent.name
        self.desc_label = parent.discription
        self.image_label = parent.image
        self.link_label = parent.link
        self.context_menu = parent.context_menu

        # ===== 当前链接缓存=====
        self._current_url = None
        self.link_label.clicked.connect(self._open_link)

    def bind_events(self):
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    # =============== 右侧详情刷新 ===============
    def update_right_panel(self, mod):
        self.name_label.setText(f"名称：{mod.get('name', '')}")
        self.desc_label.setText(f"Mod描述：{mod.get('description', '')}")

        # ===== 图片 =====
        image_path = (mod.get("image_url") or "").strip()

        self.image_label.clear()
        self.image_label.setAlignment(Qt.AlignCenter)

        if image_path and os.path.exists(image_path):
            pix = QPixmap(image_path)
            if not pix.isNull():
                pix = pix.scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(pix)
            else:
                self.image_label.setText("图片加载失败")
        else:
            # 这里明确区分“没有图片”和“路径无效”
            if image_path:
                self.image_label.setText("图片未缓存")
            else:
                self.image_label.setText("图片")

        # ===== HyperlinkLabel=====
        url = (mod.get("source_url") or "").strip()
        if url:
            tail = url.rstrip("/").split("/")[-1]
            self._current_url = url
            self.link_label.setText(f"网址尾号：{tail}")
            self.link_label.setEnabled(True)
        else:
            self._current_url = None
            self.link_label.setText("网址尾号：")
            self.link_label.setEnabled(False)

    # =============== 打开链接（HyperlinkLabel 点击）==============
    def _open_link(self):
        if self._current_url:
            QDesktopServices.openUrl(QUrl(self._current_url))

    # =============== 选中行变化 ===============
    def _on_selection_changed(self):
        items = self.table.selectedItems()
        if not items:
            return

        row = items[0].row()
        item = self.table.item(row, 2)
        if not item:
            return

        data = item.data(Qt.UserRole)
        if isinstance(data, dict):
            return

        uid = data
        mod = self.db.get_all_mods().get(uid)
        if mod:
            self.update_right_panel(mod)

    # =============== 右键菜单 ===============
    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        uid_item = self.table.item(row, 2)
        if not uid_item:
            return

        uid = uid_item.data(Qt.UserRole)
        if not uid:
            return

        mod = self.db.get_all_mods().get(uid)
        if not mod:
            return

        self.context_menu.open(self.table.mapToGlobal(pos), mod)

    # =============== 编辑弹窗 ===============
    def open_edit_dialog(self, mod):
        from GUI.diaglogs.edit_mod_dialog import EditModDialog

        dialog = EditModDialog(mod, self.parent.window())
        if not dialog.exec():
            return

        data = dialog.get_data()
        new_mod = {**mod, **data}

        old_cat = (mod.get("category") or "默认").strip()
        new_cat = (new_mod.get("category") or "默认").strip()

        self.db.upsert_mod(new_mod)

        # UI 立刻刷新（解决“必须重启才看到”的体验问题）
        if hasattr(self.parent, "refresh_mods"):
            self.parent.refresh_mods()
        elif hasattr(self.parent, "table_builder"):
            self.parent.table_builder.fill_table()

        # 统一收口：让 Sync 去做 FS 重排
        self.parent.commit_db_change()

    def _select_mod_in_table(self, uid):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)
            if not item:
                continue
            data = item.data(Qt.UserRole)
            if data == uid:
                self.table.setCurrentCell(row, 2)
                return
