from qfluentwidgets import RoundMenu
from PyQt5.QtWidgets import QAction
import webbrowser
from core.config.constants import ModStatus
from core.mod.update_actions import has_update, open_update_page, ignore_update

# =========================
# 右键菜单
# =========================

class ModContextMenu:
    def __init__(self, parent, moddata_page):
        self.parent = parent
        self.page = moddata_page

    def open(self, global_pos, mod):
        menu = RoundMenu(parent=self.parent)

        # ===== 从 DB 获取最新数据=====
        latest_mod = self.page.db.get_mod(mod["unique_id"])
        if not latest_mod:
            return

        # ===== 编辑 =====
        act_edit = QAction("编辑 MOD 信息", self.parent)
        act_edit.triggered.connect(
            lambda: self.page.open_edit_dialog(latest_mod)
        )
        menu.addAction(act_edit)

        # ===== 从 Nexus 获取信息 =====
        act_auto_fill = QAction("从 Nexus 获取信息", self.parent)
        act_auto_fill.triggered.connect(
            lambda: self.page.fetch_mod_info_from_nexus(latest_mod)
        )
        menu.addAction(act_auto_fill)

        # ===== 打开文件夹 =====
        act_open_folder = QAction("打开 MOD 文件夹", self.parent)
        act_open_folder.triggered.connect(
            lambda: self.page.open_mod_folder(latest_mod)
        )
        menu.addAction(act_open_folder)

        # ===== 启用 / 禁用 =====
        if latest_mod["status"] == ModStatus.ENABLED.value:
            act_toggle = QAction("禁用此 MOD", self.parent)
        else:
            act_toggle = QAction("启用此 MOD", self.parent)

        act_toggle.triggered.connect(
            lambda: self.page.toggle_mod_enabled(latest_mod)
        )
        menu.addAction(act_toggle)

        # ===== 打开 Nexus 页面 =====
        if latest_mod.get("source_url"):
            act_open_nexus = QAction("打开 Nexus 页面", self.parent)
            act_open_nexus.triggered.connect(
                lambda: webbrowser.open(latest_mod["source_url"])
            )
            menu.addAction(act_open_nexus)

        # ===== 删除 =====
        act_delete = QAction("删除此 MOD", self.parent)
        act_delete.triggered.connect(
            lambda: self.page.delete_mod(latest_mod)
        )
        menu.addAction(act_delete)

        # ===== 更新相关=====
        if has_update(latest_mod):
            act_update = QAction("下载更新", self.parent)
            act_update.triggered.connect(
                lambda: open_update_page(
                    latest_mod,
                    self.page.db,
                    on_finished=self.page.refresh_mods
                )
            )
            menu.addAction(act_update)

            act_ignore = QAction("忽略此更新", self.parent)
            act_ignore.triggered.connect(
                lambda: (
                    ignore_update(latest_mod, self.page.db),
                    self.page.refresh_mods()
                )
            )
            menu.addAction(act_ignore)

        menu.exec(global_pos)
