from PyQt5 import QtCore
from PyQt5.QtCore import Qt

# =========================
# UI侧表格排序逻辑
# =========================

class TableSorting:
    def __init__(self, parent):
        self.parent = parent
        self.table = parent.tableView
        self.db = parent.db
        self._refreshing = False

    #排序硬锁，防止 cellChanged 重入
        self._sorting_lock = False

    def bind_events(self):
        self.table.cellChanged.connect(self._on_cell_changed)

    def _on_cell_changed(self, row, col):
    # 硬锁：排序或刷新期间，彻底禁止进入
        if self._refreshing or self._sorting_lock:
            return

        item = self.table.item(row, col)
        if not item:
            return

    #===== 顺序列 =====
        if col == 1:
            try:
                new_order = int(item.text())
            except ValueError:
                self._refresh()
                return

            self._sorting_lock = True
            try:
            #==================================================
            #分类顺序变更
            #==================================================
                if row in self.parent.category_order_map:
                    category = self.parent.category_order_map[row]
                    print(f"\n=== CELL CHANGED: CATEGORY '{category}' -> {new_order} ===")
                    self._reorder_category(category, new_order)

                #通知 page：DB 结构已变，需要重排
                    self._commit_db_change()

            #==================================================
            #mod 顺序变更
            #==================================================
                else:
                    uid = self._get_uid_of_row(row)
                    category = self._get_category_of_row(row)
                    print(f"\n=== CELL CHANGED: MOD '{uid}' in '{category}' -> {new_order} ===")
                    if uid and category:
                        self._reorder_mod_in_category(uid, category, new_order)

                    #通知 page：DB 结构已变，需要重排
                        self._commit_db_change()

            finally:
                self._sorting_lock = False
                self._refresh()

    def _refresh(self):
        print("\n>>> REFRESH TABLE <<<")
        self._refreshing = True
        try:
            self.parent.table_builder.fill_table()
        finally:
            self._refreshing = False

# =========================
#分类排序
# =========================
    def _reorder_category(self, category, new_order):
        print("\n--- REORDER CATEGORY START ---")
        print("Target:", category, "New order:", new_order)

        mods = self.db.get_all_mods()

        category_order = {}
        for m in mods.values():
            cat = m.get("category", "默认")
            order = int(m.get("category_order", 1) or 1)
            if cat not in category_order:
                category_order[cat] = order
            else:
                category_order[cat] = min(category_order[cat], order)

        categories = sorted(category_order.keys(), key=lambda c: (category_order[c], c))

        if category not in categories:
            return

        old_index = categories.index(category) + 1
        new_order = max(1, min(len(categories), new_order))

        if old_index == new_order:
            return

        for cat, order in list(category_order.items()):
            if cat == category:
                continue
            if new_order < old_index:
                if new_order <= order < old_index:
                    category_order[cat] = order + 1
            else:
                if old_index < order <= new_order:
                    category_order[cat] = order - 1

        category_order[category] = new_order

        self.db.cursor.execute("BEGIN")
        try:
            for cat, order in category_order.items():
                self.db.cursor.execute(
                    "UPDATE mods SET category_order=? WHERE category=?",
                    (order, cat)
                )
            self.db.conn.commit()
        except Exception:
            self.db.conn.rollback()
            raise

        print("--- REORDER CATEGORY END ---")

# =========================
# mod 排序
# =========================
    def _reorder_mod_in_category(self, uid, category, new_order):
        mods = self.db.get_mods_by_category(category)
        ids = [m["unique_id"] for m in sorted(mods, key=lambda m: m["mod_order"])]

        if uid not in ids:
            return

        ids.remove(uid)
        ids.insert(max(0, min(len(ids), new_order - 1)), uid)

        for i, mid in enumerate(ids, start=1):
            self.db.update_mod_order(mid, i)

# =========================
#统一提交 DB 变更（不直接操作文件系统）
# =========================
    def _commit_db_change(self):
        """
        DB 中 category_order / mod_order 已变，
        通知 page 触发完整 Sync（防抖）
        """
        if hasattr(self.parent, "commit_db_change"):
            self.parent.commit_db_change()

# =========================
#工具函数
# =========================
    def _get_category_of_row(self, row):
        for r in range(row, -1, -1):
            item = self.table.item(r, 2)
            if not item:
                continue
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, dict) and data.get("type") == "category":
                return data["category"]
        return None

    def _get_uid_of_row(self, row):
        item = self.table.item(row, 2)
        if not item:
            return None
        data = item.data(QtCore.Qt.UserRole)
        return data if isinstance(data, str) else None
