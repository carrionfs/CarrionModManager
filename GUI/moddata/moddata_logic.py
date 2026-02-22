from PyQt5.QtWidgets import QMainWindow,QApplication
from PyQt5.QtCore import Qt, QTimer,QThread



from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar,InfoBarPosition
import os
import subprocess
import shutil

from .moddata_UI import moddata_ui
from GUI.diaglogs.RenameDialog import RenameDialog
from GUI.table.table_builder import TableBuilder
from GUI.table.table_sorting import TableSorting
from GUI.table.table_category import CategoryUIManager
from GUI.panels.detail_panel import DetailPanel
from GUI.menus.context_menu import ModContextMenu
from GUI.diaglogs.ImportModDialog import ImportModDialog
from core.mod.importer import ModImporter
from core.mod.update_actions import has_update,open_update_page
from core.config.config_manager import load_mods_path
from core.config.path import get_xnbcli_path
from core.profile.profile_store import (
    get_profile_name,
    get_storage_dir,
    rename_profile
)
from core.tasks.UpdateWorker import UpdateWorker
from core.mod.scanner import ModScanner
from core.mod.sync_manager import SyncManager
from core.config.constants import ModStatus
from core.catagory.CategoryManager import CategoryManager
from core.mod.update_checker import check_updates_from_nexus

# =========================
# 屎山代码，mainwindow的一些逻辑
# =========================

class moddata(QMainWindow, moddata_ui):
    def __init__(self, parent=None, profile_id="profile1", db=None):
        super().__init__(parent)
        self.setupUi(self)

        # ===== 基本信息 =====
        self.db = db
        self.profile_id = profile_id
        self.profile_name = get_profile_name(profile_id)
        self.profile_storage_path = get_storage_dir(profile_id)

        # ===== 是否更新？ =====
        self.Refreshbutton.setIcon(FIF.SYNC)
        self.Refreshbutton.clicked.connect(self.refresh_update_status)

        # ===== 游戏路径 & SyncManager =====
        self.game_mods_path = load_mods_path()
        self.game_path = self.get_game_path()
        self.xnbcil_path = get_xnbcli_path()
        if self.game_mods_path:
            self.sync_manager = SyncManager(
                ModScanner(self.game_mods_path),
                ModScanner(self.profile_storage_path),
                self.db,
                self.profile_storage_path
            )
        else:
            self.sync_manager = None

        # ===== 标题 & 重命名 =====
        self.profile.setText(self.profile_name)
        self.profile.mouseDoubleClickEvent = self.renameProfile

        # ===== 按钮绑定 =====
        self.opengamefolder.clicked.connect(
            lambda: self.open_folder(self.game_path)
        )
        self.openprofilefolder.clicked.connect(
            lambda: self.open_folder(self.profile_storage_path)
        )
        self.openxnbcil.clicked.connect( lambda: self.open_folder(self.xnbcil_path))
        self.opengame.clicked.connect(self.start_game)
        self.import_2.clicked.connect(self.open_import_dialog)
        self.allactandbanned.clicked.connect(self.toggle_selected_mods)
        self.allrenew.clicked.connect(self.update_all_mods)

        # ===== 搜索栏功能 =====
        self.searchline.textChanged.connect(self._on_search_text_changed)

        # ===== 右侧图片居中 =====
        self.image.setAlignment(Qt.AlignCenter)

        # ===== 右键菜单 =====
        self.context_menu = ModContextMenu(self.tableView, self)

        # ===== 子模块 =====
        self.category_rows = {}
        self.table_builder = TableBuilder(self)
        self.table_sorting = TableSorting(self)
        self.category_manager = CategoryUIManager(self)
        self.detail_panel = DetailPanel(self)

        # 让旧代码仍然可以调用 page.open_edit_dialog
        self.open_edit_dialog = self.detail_panel.open_edit_dialog

        # ===== 初始化表格 =====
        self.table_builder.fill_table()

        # ===== 绑定事件 =====
        self.table_sorting.bind_events()
        self.category_manager.bind_events()
        self.detail_panel.bind_events()

        # =========================================================
        # Sync 防抖（UI 连续编辑时只 Sync 一次）
        # =========================================================
        self._sync_debounce_timer = QTimer(self)
        self._sync_debounce_timer.setSingleShot(True)
        self._sync_debounce_timer.timeout.connect(self._run_sync_now)

        # =========================================================
        # 给子模块一个“提交后触发重排”的回调入口
        # =========================================================
        self.request_sync_relayout = self.request_sync_relayout

    # ================== 拖拽事件转发 ==================
    #已弃用，使用顺序编辑来进行mod排序
    def dragEnterEvent(self, event):
        self.table_sorting.dragEnterEvent(event)

    def dropEvent(self, event):
        self.table_sorting.dropEvent(event)

    # ================= 其它工具方法 =================
    def get_game_path(self):
        return os.path.dirname(self.game_mods_path) if self.game_mods_path else ""

    def open_folder(self, path):
        if path and os.path.exists(path):
            os.startfile(path)

    def fetch_mod_info_from_nexus(self, mod):
        from core.nexus.auto_fill import auto_fill_single_mod
        from core.profile.profile_store import get_profile_root
        from qfluentwidgets import InfoBar, InfoBarPosition

        try:
            profile_root = get_profile_root(self.profile_id)
            auto_fill_single_mod(self.db, profile_root, mod["unique_id"], mod)
            self.refresh_mods()

            InfoBar.success(
                "成功",
                f"已从 Nexus 补全 {mod['name']} 的信息",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )
        except Exception as e:
            InfoBar.error(
                "失败",
                f"补全失败：{str(e)}",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT
            )

    def renameProfile(self, event):
        dialog = RenameDialog(self, self.profile.text())
        if dialog.exec():
            new_name = dialog.getName().strip()
            if new_name:
                self.profile.setText(new_name)
                rename_profile(self.profile_id, new_name)

                # 更新导航栏标题
                parent = self.parent()
                if hasattr(parent, "navigationInterface"):
                    parent.navigationInterface.setItemText(self, new_name)
                self.CreateSuccessInforBar_renameProfile()

    # =========================================================
    # 请求一次“按 DB 重建物理结构”的 Sync（防抖）
    # =========================================================
    def request_sync_relayout(self, delay_ms: int = 250):
        if not self.sync_manager:
            return
        # 防抖：短时间多次调用只会触发一次 sync
        self._sync_debounce_timer.start(delay_ms)

    # =========================================================
    #立即执行 Sync（由防抖 timer 触发）
    # =========================================================
    def _run_sync_now(self):
        if not self.sync_manager:
            return

        try:
            print("[UI] Sync relayout start...")
            self.sync_manager.sync()
            print("[UI] Sync relayout done.")
        finally:
            # 无论成功失败，都刷新 UI（至少让用户看到最新 DB 状态）
            self.refresh_mods()

    # =========================================================
    # 强制立即 Sync（不防抖，用于导入/启用切换等）
    # =========================================================
    def sync_relayout_now(self):
        if not self.sync_manager:
            return
        self._sync_debounce_timer.stop()
        self._run_sync_now()

    #======================导入mod=======================
    def open_import_dialog(self):
        """打开导入 Mod 对话框"""

        dialog = ImportModDialog(self)
        if not dialog.exec():
            return

        data = dialog.get_data()
        if not data.get("mod_path"):
            return

        try:
            uid = ModImporter.import_mod(
                data=data,
                db=self.db,
                profile_id=self.profile_id
            )
            print(f"[IMPORT] 新增 Mod: {uid}")

            # 导入后 Sync，让分类目录/顺序/命名立刻按 DB 投影
            self.sync_relayout_now()

        except Exception as e:
            import traceback
            traceback.print_exc()
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "导入失败",
                f"导入 Mod 时发生错误：\n{e}"
            )

    def refresh_mods(self):
        self.table_builder.fill_table()

    #右键菜单用法：

    def toggle_mod_enabled(self, mod):
        uid = mod["unique_id"]

        #永远从 DB 取最新状态
        fresh = self.db.get_mod(uid)
        if not fresh:
            return

        cur_status = fresh["status"]
        cur_path = fresh["folder_path"]

        if cur_status == ModStatus.ENABLED.value:
            new_status = ModStatus.DISABLED.value
            target_root = self.profile_storage_path
        else:
            new_status = ModStatus.ENABLED.value
            target_root = self.game_mods_path

        category = fresh.get("category", "默认")
        category_order = int(fresh.get("category_order", 1) or 1)
        category_dir = f"{category_order:02d}_{category}"

        target_category_path = os.path.join(target_root, category_dir)
        os.makedirs(target_category_path, exist_ok=True)

        target_path = os.path.join(
            target_category_path,
            os.path.basename(cur_path)
        )

        #  UI 直接执行物理移动
        if os.path.exists(cur_path) and cur_path != target_path:
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.move(cur_path, target_path)

        #  UI 直接更新 DB
        self.db.set_mod_status(uid, new_status)
        self.db.update_mod_path(uid, target_path)

        # 所有 Mod 处理完后，只 Sync 一次
        self.sync_relayout_now()

    #批量修改
    def toggle_selected_mods(self):
        selected_mods = self.table_builder.get_selected_mods()
        if not selected_mods:
            return

        for mod in selected_mods:
            uid = mod["unique_id"]
            cur_status = mod["status"]
            cur_path = mod["folder_path"]

            if cur_status == ModStatus.ENABLED.value:
                new_status = ModStatus.DISABLED.value
                target_root = self.profile_storage_path
            else:
                new_status = ModStatus.ENABLED.value
                target_root = self.game_mods_path

            category = mod.get("category", "默认")
            category_order = int(mod.get("category_order", 1) or 1)
            category_dir = f"{category_order:02d}_{category}"

            target_root = (
                self.game_mods_path
                if new_status == ModStatus.ENABLED.value
                else self.profile_storage_path
            )

            target_category_path = os.path.join(target_root, category_dir)
            os.makedirs(target_category_path, exist_ok=True)

            target_path = os.path.join(
                target_category_path,
                os.path.basename(cur_path)
            )

            # 移动物理文件夹
            if os.path.exists(cur_path) and cur_path != target_path:
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.move(cur_path, target_path)

            # 更新数据库
            self.db.set_mod_status(uid, new_status)
            self.db.update_mod_path(uid, target_path)

        # 所有 Mod 处理完后，只 Sync 一次
        self.sync_relayout_now()

    def open_mod_folder(self, mod):
        path = mod.get("folder_path")
        if path and os.path.exists(path):
            os.startfile(path)

    def _on_search_text_changed(self, text: str):
        """
        根据搜索框内容过滤 tableView 中的 mod 行，
        并自动隐藏没有匹配 mod 的分类行
        """
        keyword = text.strip().lower()
        table = self.tableView

        # 初始化：所有分类默认“没有可见 mod”
        category_has_visible_mod = {
            cat: False for cat in self.category_order_map.values()
        }

        for row in range(table.rowCount()):
            # 分类行：先跳过，最后统一处理
            if row in self.category_order_map:
                continue

            name_item = table.item(row, 2)
            if not name_item:
                table.setRowHidden(row, True)
                continue

            mod_name = name_item.text().lower()
            category = name_item.data(Qt.UserRole + 1)

            match = keyword in mod_name if keyword else True
            table.setRowHidden(row, not match)

            if match and category:
                category_has_visible_mod[category] = True

        # 最后处理分类行：没有可见 mod 的分类直接隐藏
        for cat_row, category in self.category_order_map.items():
            table.setRowHidden(cat_row, not category_has_visible_mod.get(category, False))
    #更新实现
    def refresh_update_status(self):
        self.progressBar.setVisible(True)
        QApplication.processEvents()

        self.update_thread = QThread()
        self.update_worker = UpdateWorker(self.db)
        self.update_worker.moveToThread(self.update_thread)

        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.on_update_finished)
        self.update_worker.error.connect(self.on_update_error)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)

        self.update_thread.start()

    #=========异步调用=========
    def on_update_finished(self):
        self.refresh_mods()
        self.progressBar.setVisible(False)

    def on_update_error(self, message):
        InfoBar.error(
            title="更新失败",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT
        )
        self.progressBar.setVisible(False)

    def delete_mod(self, mod):
        uid = mod["unique_id"]
        path = mod.get("folder_path")

        # 1️⃣ 先删物理文件
        if path and os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"[DELETE] Failed to remove folder: {path}", e)

        # 2️⃣ 再删 DB
        self.db.delete_mod(uid)

        # 3️⃣ Sync
        self.sync_relayout_now()
    #========一键更新=============
    def update_all_mods(self):
        """
        一键更新所有有更新的 MOD（串行）
        """
        # get_all_mods() 很可能返回 uid 列表
        mod_ids = self.db.get_all_mods()

        mods = []
        for uid in mod_ids:
            mod = self.db.get_mod(uid)
            if mod:
                mods.append(mod)

        mods_to_update = [m for m in mods if has_update(m)]

        if not mods_to_update:
            print("[UPDATE] No mods need update")
            return

        print(f"[UPDATE] Updating {len(mods_to_update)} mods")

        def update_next(index=0):
            if index >= len(mods_to_update):
                print("[UPDATE] All updates finished")
                self.refresh_mods()
                return

            mod = mods_to_update[index]
            print(f"[UPDATE] Updating: {mod.get('name')}")

            open_update_page(
                mod,
                self.db,
                on_finished=lambda: update_next(index + 1)
            )

        update_next()

    def start_game(self):
        if not self.game_path:
            return

        smapi = os.path.join(self.game_path, "StardewModdingAPI.exe")
        normal = os.path.join(self.game_path, "Stardew Valley.exe")
        exe = smapi if os.path.exists(smapi) else normal
        if os.path.exists(exe):
            subprocess.Popen(exe, cwd=self.game_path)



    # =========================================================
    # 给子模块调用的“提交后刷新 + 触发 Sync”的统一入口
    # =========================================================
    def commit_db_change(self, debounce_ms: int = 250):
        """
        用于：分类变更、分类顺序变更、mod 顺序变更、拖拽完成等
        """
        self.refresh_mods()
        self.request_sync_relayout(debounce_ms)
