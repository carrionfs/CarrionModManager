from .moddata_UI import moddata_ui, RenameDialog
from PyQt5.QtWidgets import QMainWindow, QHeaderView
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QUrl
from PyQt5 import QtWidgets, QtCore, QtGui
from qfluentwidgets import FluentIcon as FIF, CheckBox

import os
import subprocess

from GUI.diaglogs.edit_mod_dialog import EditModDialog
from GUI.menus.context_menu import ModContextMenu

from core.config.config_manager import load_mods_path
from core.profile.profile_store import (
    get_profile_name,
    get_storage_dir,
    rename_profile
)
from core.mod.scanner import ModScanner
from core.mod.sync_manager import SyncManager


# =======================找问题代码===================
# try:
#     super().__init__(parent)
#     self.setupUi(self)
#     print("step 1: ui setup ok")
#     self.db = db
#     self.profile_id = profile_id
#     self.profile_name = get_profile_name(profile_id)
#     self.profile_storage_path = get_storage_dir(profile_id)
#     print("step 2: profile info ok")
#     self.searchbutton.setIcon(FIF.SEARCH)
#     self.game_mods_path = load_mods_path()
#     self.game_path = self.get_game_path()
#     print("step 3: game path ok")
#     if self.game_mods_path:
#         self.sync_manager = SyncManager(ModScanner(self.game_mods_path), ModScanner(self.profile_storage_path),
#                                         self.db, self.profile_storage_path)
#     else:
#         self.sync_manager = None
#     print("step 4: sync manager ok")
#     self.profile.setText(self.profile_name)
#     self.profile.mouseDoubleClickEvent = self.renameProfile
#     self.opengamefolder.clicked.connect(lambda: self.open_folder(self.game_path))
#     self.openprofilefolder.clicked.connect(lambda: self.open_folder(self.profile_storage_path))
#     self.opengame.clicked.connect(self.start_game)
#     print("step 5: buttons connected")
#     self.image.setAlignment(Qt.AlignCenter)
#     self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
#     self.tableView.customContextMenuRequested.connect(self.show_context_menu)
#     print("step 6: table signals ok")
#     self.context_menu = ModContextMenu(self.tableView, self)
#     print("step 7: context menu ok")
#     # self._init_header_checkbox()
#     self.category_rows = {}
#     self.fill_table_from_db()
#     print("step 8: table filled")
#     self.tableView.cellClicked.connect(self.on_table_cell_clicked)
# except Exception as e:
#     print("🔥 moddata init error:", e)
#     import traceback
#     traceback.print_exc()
# super().__init__(parent)
# self.setupUi(self)
# =======================找问题代码===================
class moddata(QMainWindow, moddata_ui):
    def __init__(self, parent=None, profile_id="profile1", db=None):
        super().__init__(parent)
        self.setupUi(self)

        self.db = db
        self.profile_id = profile_id
        self.profile_name = get_profile_name(profile_id)
        self.profile_storage_path = get_storage_dir(profile_id)

        self.searchbutton.setIcon(FIF.SEARCH)

        self.game_mods_path = load_mods_path()
        self.game_path = self.get_game_path()

        if self.game_mods_path:
            self.sync_manager = SyncManager(
                ModScanner(self.game_mods_path),
                ModScanner(self.profile_storage_path),
                self.db,
                self.profile_storage_path
            )
        else:
            self.sync_manager = None

        self.profile.setText(self.profile_name)
        self.profile.mouseDoubleClickEvent = self.renameProfile

        self.opengamefolder.clicked.connect(
            lambda: self.open_folder(self.game_path)
        )
        self.openprofilefolder.clicked.connect(
            lambda: self.open_folder(self.profile_storage_path)
        )
        self.opengame.clicked.connect(self.start_game)

        self.image.setAlignment(Qt.AlignCenter)

        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.show_context_menu)
        self.tableView.cellClicked.connect(self.on_table_cell_clicked)
        self.tableView.setDragEnabled(True)
        self.tableView.setAcceptDrops(True)
        # self.tableView.setDropIndicatorShown(True)
        self.tableView.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        # self.fill_table_from_db()

        self.tableView.model().rowsMoved.connect(self._on_rows_moved)
        # self.tableView.model().rowsMoved.connect(lambda *args: self._rebuild_mod_order_from_table())
        self.context_menu = ModContextMenu(self.tableView, self)

        self.category_rows = {}
        self.fill_table_from_db()
        self.tableView.itemChanged.connect(self._on_order_edited)

    # ================= 表格（分类分组） =================
    # ================= 表格（分类分组 + 折叠） =================
    def fill_table_from_db(self):
        if not self.db:
            return

        # 暂时断开 itemChanged 信号，避免初始化时触发排序逻辑
        try:
            self.tableView.itemChanged.disconnect(self._on_order_edited)
        except:
            pass

        mods = self.db.get_all_mods()
        table = self.tableView
        table.clear()

        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["", "顺序", "名称", "分类", "作者", "版本", "状态"]
        )

        # 分类结构
        categories = {}
        for mod in mods.values():
            key = (mod["category_order"], mod["category"])
            categories.setdefault(key, []).append(mod)

        sorted_categories = sorted(categories.items(), key=lambda x: x[0][0])

        # 计算总行数（分类标题 + mod 行）
        total_rows = sum(len(v) + 1 for _, v in sorted_categories)
        table.setRowCount(total_rows)

        self.category_rows = {}  # category -> [row indices]

        row = 0
        for (cat_order, category), mod_list in sorted_categories:
            # ===== 分类标题行 =====
            title_item = QtWidgets.QTableWidgetItem(category)
            title_item.setFlags(Qt.ItemIsEnabled)
            title_item.setBackground(QtGui.QColor(240, 240, 240))
            title_item.setTextAlignment(Qt.AlignCenter)

            font = title_item.font()
            font.setBold(True)
            title_item.setFont(font)

            # 标记为分类行
            title_item.setData(QtCore.Qt.UserRole, {
                "type": "category",
                "category": category,
                "collapsed": False
            })

            table.setItem(row, 2, title_item)
            table.setSpan(row, 2, 1, 5)

            self.category_rows[category] = []
            row += 1

            # ===== 分类内 mod 行 =====
            mod_list.sort(key=lambda m: m["mod_order"])
            display_order = 1

            for mod in mod_list:
                checkbox = CheckBox()
                table.setCellWidget(row, 0, checkbox)

                # ===== 关键修改：顺序列可编辑 =====
                order_item = QtWidgets.QTableWidgetItem(str(display_order))
                order_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                table.setItem(row, 1, order_item)
                display_order += 1

                # 名称列（存 uid）
                name_item = QtWidgets.QTableWidgetItem(mod["name"])
                name_item.setData(QtCore.Qt.UserRole, mod["unique_id"])
                table.setItem(row, 2, name_item)

                table.setItem(row, 3, QtWidgets.QTableWidgetItem(mod["category"]))
                table.setItem(row, 4, QtWidgets.QTableWidgetItem(mod["author"]))
                table.setItem(row, 5, QtWidgets.QTableWidgetItem(mod["version"]))
                table.setItem(row, 6, QtWidgets.QTableWidgetItem(mod["status"]))

                self.category_rows[category].append(row)
                row += 1

        # ===== 列宽策略 =====
        header = table.horizontalHeader()

        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.resizeSection(1, 50)

        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.resizeSection(6, 80)

        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # ===== 关键修改：允许双击编辑 =====
        table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)

        # ===== 重新连接 itemChanged 信号 =====
        table.itemChanged.connect(self._on_order_edited)

    def _toggle_all_rows(self, state):
        checked = state == Qt.Checked
        for row in range(self.tableView.rowCount()):
            checkbox = self.tableView.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(checked)

    # ================= 右侧详情刷新（关键） =================
    def _update_right_panel(self, mod):
        self.name.setText(f"名称：{mod.get('name', '')}")
        self.discription.setText(f"Mod描述：{mod.get('description', '')}")

        image_path = mod.get("image_url", "")
        if image_path and os.path.exists(image_path):
            pix = QPixmap(image_path)
            if not pix.isNull():
                pix = pix.scaled(
                    self.image.width(),
                    self.image.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image.setPixmap(pix)
                self.image.setAlignment(Qt.AlignCenter)
                return

        self.image.clear()
        self.image.setText("图片")

        url = mod.get("source_url", "").strip()
        if url:
            tail = url.rstrip("/").split("/")[-1]
            self.link.setText(f"网址尾号：{tail}")
            self.link.setUrl(QUrl(url))
            self.link.setOpenExternalLinks(True)
        else:
            self.link.setText("网址尾号：")

    def _select_mod_in_table(self, uid):
        for row in range(self.tableView.rowCount()):
            item = self.tableView.item(row, 2)
            if not item:
                continue

            data = item.data(QtCore.Qt.UserRole)
            if data == uid:
                self.tableView.setCurrentCell(row, 2)
                return

    # ================= 右键菜单 =================
    def show_context_menu(self, pos):
        item = self.tableView.itemAt(pos)
        if not item:
            return

        row = item.row()
        uid_item = self.tableView.item(row, 2)
        if not uid_item:
            return

        uid = uid_item.data(QtCore.Qt.UserRole)
        if not uid:
            return

        mod = self.db.get_all_mods().get(uid)
        if not mod:
            return

        self.context_menu.open(self.tableView.mapToGlobal(pos), mod)

    def open_edit_dialog(self, mod):
        dialog = EditModDialog(mod, self.window())
        if dialog.exec():
            data = dialog.get_data()
            new_mod = {**mod, **data}

            # 1️⃣ 写回数据库
            self.db.upsert_mod(new_mod)

            # 2️⃣ 同步文件（如果有）
            if self.sync_manager:
                self.sync_manager.sync()

            # 3️⃣ 刷新表格（会清空并重建）
            self.fill_table_from_db()

            # 4️⃣ 重新选中刚刚编辑的 mod（关键）
            self._select_mod_in_table(new_mod["unique_id"])

            # 5️⃣ 更新右侧详情（最终显示）
            self._update_right_panel(new_mod)

    # ================= 表格点击 =================
    def on_table_item_clicked(self, item):
        item = self.tableView.item(item.row(), 2)
        data = item.data(QtCore.Qt.UserRole)

        # 点击的是分类标题
        if isinstance(data, dict) and data.get("type") == "category":
            category = data["category"]
            collapsed = data["collapsed"]

            for r in self.category_rows.get(category, []):
                self.tableView.setRowHidden(r, not collapsed)

            data["collapsed"] = not collapsed
            item.setData(QtCore.Qt.UserRole, data)
            return

        row = item.row()
        uid_item = self.tableView.item(row, 2)
        if not uid_item:
            return

        uid = uid_item.data(QtCore.Qt.UserRole)
        mod = self.db.get_all_mods().get(uid)
        if mod:
            self._update_right_panel(mod)

    def on_table_cell_clicked(self, row, column):
        item = self.tableView.item(row, 2)
        if not item:
            return

        data = item.data(QtCore.Qt.UserRole)

        # ===== 点击的是分类标题 =====
        if isinstance(data, dict) and data.get("type") == "category":
            category = data["category"]
            collapsed = data["collapsed"]

            for r in self.category_rows.get(category, []):
                self.tableView.setRowHidden(r, not collapsed)

            data["collapsed"] = not collapsed
            item.setData(QtCore.Qt.UserRole, data)
            return

        # ===== 普通 mod 行 =====
        uid = data
        mod = self.db.get_all_mods().get(uid)
        if mod:
            self._update_right_panel(mod)
    #==================拖拽排序实现=================
    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        pos = event.pos()
        target_row = self.tableView.rowAt(pos.y())
        source_row = self.tableView.currentRow()

        if target_row < 0 or source_row < 0:
            return

        # 判断是否跨分类
        source_cat = self._get_category_of_row(source_row)
        target_cat = self._get_category_of_row(target_row)

        uid = self._get_uid_of_row(source_row)

        if source_cat == target_cat:
            # 分类内排序
            self._move_mod_within_category(uid, source_cat, source_row, target_row)
        else:
            # 跨分类排序
            self._move_mod_to_other_category(uid, source_cat, target_cat, target_row)

        # 重建表格
        self.fill_table_from_db()

    def _get_category_of_row(self, row):
        # 向上找最近的分类标题行
        for r in range(row, -1, -1):
            item = self.tableView.item(r, 2)
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, dict) and data.get("type") == "category":
                return data["category"]
        return None

    def _get_uid_of_row(self, row):
        item = self.tableView.item(row, 2)
        if not item:
            return None
        data = item.data(QtCore.Qt.UserRole)
        return data if isinstance(data, str) else None

    def _move_mod_within_category(self, uid, category, source_row, target_row):
        mods = self.db.get_mods_by_category(category)
        # 按 mod_order 排序
        mods = sorted(mods, key=lambda m: m["mod_order"])

        # 找到 uid 对应的 mod
        ids = [m["unique_id"] for m in mods]
        ids.remove(uid)
        ids.insert(target_row - self._category_start_row(category) - 1, uid)

        # 重写 mod_order
        for i, uid in enumerate(ids, start=1):
            self.db.update_mod_order(uid, i)

    def _move_mod_to_other_category(self, uid, old_cat, new_cat, target_row):
        # 修改分类
        self.db.update_mod_category(uid, new_cat)

        # 重建新分类的顺序
        mods = self.db.get_mods_by_category(new_cat)
        mods = sorted(mods, key=lambda m: m["mod_order"])

        ids = [m["unique_id"] for m in mods]
        ids.insert(target_row - self._category_start_row(new_cat) - 1, uid)

        for i, uid in enumerate(ids, start=1):
            self.db.update_mod_order(uid, i)
    #================改变顺序排序实现===============
    def _on_order_edited(self, item):
        # 只处理“顺序”列
        if item.column() != 1:
            return

        try:
            new_order = int(item.text())
        except:
            return  # 非数字，忽略

        row = item.row()
        uid = self._get_uid_of_row(row)
        category = self._get_category_of_row(row)

        if not uid or not category:
            return

        # 获取该分类所有 mod
        mods = self.db.get_mods_by_category(category)
        mods = sorted(mods, key=lambda m: m["mod_order"])

        ids = [m["unique_id"] for m in mods]

        # 移除当前 uid
        if uid in ids:
            ids.remove(uid)

        # 插入到新位置（注意 new_order 从 1 开始）
        new_index = max(0, min(len(ids), new_order - 1))
        ids.insert(new_index, uid)

        # 重写顺序
        for i, uid in enumerate(ids, start=1):
            self.db.update_mod_order(uid, i)

        # 重建表格
        self.fill_table_from_db()

    # def _rebuild_mod_order_from_table(self):
    #     current_category = None
    #     order = 0
    #
    #     for row in range(self.tableView.rowCount()):
    #         item = self.tableView.item(row, 2)
    #         if not item:
    #             continue
    #
    #         data = item.data(QtCore.Qt.UserRole)
    #
    #         # 分类标题
    #         if isinstance(data, dict):
    #             current_category = data["category"]
    #             order = 0
    #             continue
    #
    #         # Mod 行
    #         uid = data
    #         order += 1
    #         self.db.update_mod_order(uid, order)
    def _on_rows_moved(self, *args):
        self._rebuild_mod_order_from_table()
        self.fill_table_from_db()

    # ================= 其它 =================
    def get_game_path(self):
        return os.path.dirname(self.game_mods_path) if self.game_mods_path else ""

    def open_folder(self, path):
        if path and os.path.exists(path):
            os.startfile(path)

    def renameProfile(self, event):
        dialog = RenameDialog(self, self.profile.text())
        if dialog.exec():
            new_name = dialog.getName().strip()
            if new_name:
                self.profile.setText(new_name)
                rename_profile(self.profile_id, new_name)

    def start_game(self):
        if not self.game_path:
            return

        smapi = os.path.join(self.game_path, "StardewModdingAPI.exe")
        normal = os.path.join(self.game_path, "Stardew Valley.exe")
        exe = smapi if os.path.exists(smapi) else normal
        if os.path.exists(exe):
            subprocess.Popen(exe, cwd=self.game_path)
