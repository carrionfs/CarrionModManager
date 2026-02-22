from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import PyQt5.QtCore as QtCore
from PyQt5 import QtWidgets, QtGui
from qfluentwidgets import CheckBox
import os

# =========================
# 根据db组建table
# =========================

class TableBuilder:
    def __init__(self, parent):
        self.parent = parent
        self.table = parent.tableView
        self.db = parent.db

        # category 折叠状态字典：category -> bool
        # 如果 parent 已经有这个字典就复用，否则新建
        if not hasattr(self.parent, "category_collapsed"):
            self.parent.category_collapsed = {}

        # 绑定点击事件（如果外部已有处理器，会优先使用外部）
        # 为避免重复连接，先断开再连（安全做法）
        try:
            try:
                self.table.cellClicked.disconnect()
            except Exception:
                pass
            self.table.cellClicked.connect(self._on_cell_clicked)
        except Exception:
            # 如果连接失败，不要阻塞程序
            pass

    def _on_cell_clicked(self, row, col):
        """
        内置的分类行点击处理：
        - 仅当点击的是分类标题列（col == 2）时切换 collapsed 状态并刷新表格
        - 兼容外部 table_category._on_cell_clicked（仍会尝试调用，但不依赖它）
        """
        # 先尝试调用外部处理器（兼容旧逻辑），但不要让外部异常阻塞
        if hasattr(self.parent, "table_category") and hasattr(self.parent.table_category, "_on_cell_clicked"):
            try:
                self.parent.table_category._on_cell_clicked(row, col)
            except Exception:
                # 忽略外部处理器异常，继续内部逻辑
                pass

        # 只有当点击的是“名称列 / 分类标题列”（索引 2）并且该行是分类行时，才切换折叠
        if col != 2:
            return

        if hasattr(self.parent, "category_order_map") and row in self.parent.category_order_map:
            cat = self.parent.category_order_map[row]
            cur = self.parent.category_collapsed.get(cat, False)
            self.parent.category_collapsed[cat] = not cur
            # 立即刷新表格（会使用新的 collapsed 状态）
            self.fill_table()

    def get_selected_mods(self):
        mods = []
        table = self.table

        for row in range(table.rowCount()):
            # 跳过分类行
            if row in getattr(self.parent, "category_order_map", {}):
                continue

            checkbox = table.cellWidget(row, 0)
            if not checkbox or not checkbox.isChecked():
                continue

            name_item = table.item(row, 2)
            if not name_item:
                continue

            uid = name_item.data(QtCore.Qt.UserRole)
            if not uid:
                continue

            mod = self.db.get_mod(uid)
            if mod:
                mods.append(mod)

        return mods

    def fill_table(self):
        print("\n=== FILL TABLE START ===")
        print("🔥 DB PATH IN UI  =", os.path.abspath(self.db.conn.execute("PRAGMA database_list").fetchone()[2]))

        rows = self.db.conn.execute("""
            SELECT category, category_order, COUNT(*) AS cnt
            FROM mods
            GROUP BY category, category_order
            ORDER BY category_order
        """).fetchall()

        print("DB STATE AT FILL_TABLE:")
        for r in rows:
            print(dict(r))

        print("ALL MODS:")
        for uid, mod in self.db.get_all_mods().items():
            print(uid, mod["status"])

        table = self.table
        table.blockSignals(True)
        try:
            # 清除跨列，否则会出现“下一行只剩名称列”的 bug
            table.clear()
            table.clearSpans()

            mods = self.db.get_all_mods()

            table.setColumnCount(7)
            table.setHorizontalHeaderLabels(
                ["", "顺序", "名称", "分类", "作者", "版本", "状态"]
            )

            # ===== 按分类分组 =====
            categories = {}
            for mod in mods.values():
                cat = mod.get("category", "默认")
                order = int(mod.get("category_order", 1) or 1)
                categories.setdefault(cat, {"order": order, "mods": []})
                categories[cat]["mods"].append(mod)

            # 确保 collapsed 字典有默认值
            for cat in categories.keys():
                if cat not in self.parent.category_collapsed:
                    self.parent.category_collapsed[cat] = False

            print("CATEGORIES FOR UI:")
            for cat, info in categories.items():
                print(cat, "order:", info["order"], "mods:", len(info["mods"]),
                      "collapsed:", self.parent.category_collapsed.get(cat, False))

            sorted_categories = sorted(
                categories.items(),
                key=lambda x: (x[1]["order"], x[0])
            )

            # 计算行数
            total_rows = 0
            for cat, info in sorted_categories:
                total_rows += 1
                if not self.parent.category_collapsed.get(cat, False):
                    total_rows += len(info["mods"])

            table.setRowCount(total_rows)

            self.parent.category_order_map = {}

            row = 0
            for category, info in sorted_categories:
                # ===== 分类行 =====
                order_item = QtWidgets.QTableWidgetItem(str(info["order"]))
                order_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                order_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 1, order_item)

                title_item = QtWidgets.QTableWidgetItem(category)
                title_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                title_item.setBackground(QtGui.QColor(240, 240, 240))
                title_item.setTextAlignment(Qt.AlignCenter)

                font = title_item.font()
                font.setBold(True)
                title_item.setFont(font)

                title_item.setData(QtCore.Qt.UserRole, {
                    "type": "category",
                    "category": category,
                    "collapsed": bool(self.parent.category_collapsed.get(category, False))
                })

                table.setItem(row, 2, title_item)
                table.setSpan(row, 2, 1, 5)

                self.parent.category_order_map[row] = category
                row += 1

                # ===== 折叠则跳过 mod 行 =====
                if self.parent.category_collapsed.get(category, False):
                    continue

                # ===== 分类内 mod 行 =====
                info["mods"].sort(key=lambda m: int(m.get("mod_order", 1) or 1))

                display_order = 1
                for mod in info["mods"]:
                    table.setCellWidget(row, 0, CheckBox())

                    order_item = QtWidgets.QTableWidgetItem(str(display_order))
                    order_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    order_item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(row, 1, order_item)
                    display_order += 1
                    cur = mod.get("version", "")
                    latest = mod.get("latest_version", "")

                    # ===== 名称列（⬆️ 提示）=====
                    name_text = mod.get("name", "")
                    if latest and latest != cur:
                        name_text = "⬆️ " + name_text

                    name_item = QtWidgets.QTableWidgetItem(name_text)
                    name_item.setData(QtCore.Qt.UserRole, mod.get("unique_id"))
                    name_item.setData(QtCore.Qt.UserRole + 1, category)
                    table.setItem(row, 2, name_item)

                    # ===== 版本列（1.0 → 1.1）=====
                    if latest and latest != cur:
                        version_text = f"{cur} → {latest}"
                        version_item = QtWidgets.QTableWidgetItem(version_text)
                        version_item.setForeground(QColor("#ff9800"))  # 橙色
                    else:
                        version_item = QtWidgets.QTableWidgetItem(cur)

                    table.setItem(row, 5, version_item)

                    table.setItem(row, 6, QtWidgets.QTableWidgetItem(mod.get("status", "")))

                    row += 1

            # ===== 列宽设置=====
            header = table.horizontalHeader()
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            header.resizeSection(1, 80)
            header.resizeSection(6, 80)

            table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)

        finally:
            table.blockSignals(False)

        print("=== FILL TABLE END ===")

