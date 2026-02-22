from PyQt5 import QtCore

# =========================
# UI侧的分类控制器
# =========================

class CategoryUIManager:
    """
    职责：
    - 分类标题点击：折叠 / 展开（原有功能）
    - 普通 mod 行点击：交给 DetailPanel（原有功能）
    -  当分类结构发生变化（顺序 / 新建 / 重命名）时：
        - 通知 page 触发 DB → FS 的重排（不直接操作文件）
    """

    def __init__(self, parent):
        self.parent = parent
        self.table = parent.tableView
        self.db = parent.db

    def bind_events(self):
        self.table.cellClicked.connect(self._on_cell_clicked)

    def _on_cell_clicked(self, row, column):
        item = self.table.item(row, 2)
        if not item:
            return

        data = item.data(QtCore.Qt.UserRole)

        # =====================================================
        # 分类标题：折叠 / 展开
        # =====================================================
        if isinstance(data, dict) and data.get("type") == "category":
            category = data["category"]
            collapsed = data.get("collapsed", False)

            for r in self.parent.category_rows.get(category, []):
                self.table.setRowHidden(r, not collapsed)

            data["collapsed"] = not collapsed
            item.setData(QtCore.Qt.UserRole, data)
            return

        # =====================================================
        # 普通 mod 行：交给 DetailPanel
        # =====================================================
        uid = data
        mod = self.db.get_all_mods().get(uid)
        if mod:
            self.parent.detail_panel.update_right_panel(mod)

    # =====================================================
    # 当分类结构被修改后调用
    # 这个方法不会被 cellClicked 直接触发，
    # 而是给“分类编辑 / 拖拽 / 新建”等逻辑调用
    # =====================================================
    def commit_category_change(self):
        """
        分类结构发生变化后调用：
        - 分类顺序变化
        - 新建分类
        - 重命名分类
        """
        # 刷新 UI（让用户立刻看到 DB 状态）
        self.parent.refresh_mods()

        # 通知 page：DB 结构已变，需要重排物理文件
        if hasattr(self.parent, "commit_db_change"):
            self.parent.commit_db_change()
