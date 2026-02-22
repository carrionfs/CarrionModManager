import os
import sqlite3
from core.config.constants import ModStatus


class DatabaseManager:

    def __init__(self, db_path: str):
        self.db_path = db_path

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.initialize()

        print("[DB OPEN]", os.path.abspath(self.db_path))

    # =========================
    # 初始化 & 兼容旧数据库
    # =========================
    def initialize(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mods (
                unique_id TEXT PRIMARY KEY,
                name TEXT,
                version TEXT,
                author TEXT,
                description TEXT,
                folder_path TEXT,
                status TEXT,
                category TEXT DEFAULT '默认',
                category_order INTEGER DEFAULT 1,
                mod_order INTEGER DEFAULT 1,
                source_url TEXT DEFAULT '',
                image_url TEXT DEFAULT '',
                latest_version TEXT DEFAULT ''
            )
        """)
        self.conn.commit()

        # 兼容旧数据库：补 latest_version
        try:
            self.cursor.execute(
                "ALTER TABLE mods ADD COLUMN latest_version TEXT DEFAULT ''"
            )
            self.conn.commit()
            print("[DB] Added column: latest_version")
        except sqlite3.OperationalError:
            pass

    # =========================
    # 基础 CRUD
    # =========================
    def upsert_mod(self, mod):
        uid = mod.get("unique_id")
        category = mod.get("category", "默认")
        incoming_order = mod.get("mod_order", 9999)

        if incoming_order >= 9999:
            row = self.conn.execute(
                "SELECT MAX(mod_order) FROM mods WHERE category=?",
                (category,)
            ).fetchone()
            mod["mod_order"] = (row[0] or 0) + 1

        self.cursor.execute("""
            INSERT INTO mods (
                unique_id, name, version, author, description, folder_path, status,
                category, category_order, mod_order, source_url, image_url, latest_version
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(unique_id) DO UPDATE SET
                name=excluded.name,
                version=excluded.version,
                author=excluded.author,
                description=excluded.description,
                folder_path=excluded.folder_path,
                status=excluded.status,
                category=excluded.category,
                category_order=mods.category_order,
                mod_order=mods.mod_order,
                source_url=excluded.source_url,
                image_url=excluded.image_url
        """, (
            uid,
            mod.get("name"),
            mod.get("version"),
            mod.get("author"),
            mod.get("description"),
            mod.get("folder_path"),
            mod.get("status"),
            category,
            max(1, mod.get("category_order", 1)),
            max(1, mod.get("mod_order", 1)),
            mod.get("source_url", ""),
            mod.get("image_url", ""),
            mod.get("latest_version", "")
        ))
        self.conn.commit()

    # =========================
    # 更新检测相关
    # =========================
    def update_latest_version(self, uid, latest_version: str):
        self.cursor.execute(
            "UPDATE mods SET latest_version=? WHERE unique_id=?",
            (latest_version, uid)
        )
        self.conn.commit()

    def clear_latest_version(self, uid):
        self.cursor.execute(
            "UPDATE mods SET latest_version='' WHERE unique_id=?",
            (uid,)
        )
        self.conn.commit()

    # =========================
    # SyncManager / UI 明确依赖的方法
    # =========================
    def update_mod_path(self, uid, path):
        self.cursor.execute(
            "UPDATE mods SET folder_path=? WHERE unique_id=?",
            (path, uid)
        )
        self.conn.commit()

    def update_mod_order(self, uid, mod_order):
        self.cursor.execute(
            "UPDATE mods SET mod_order=? WHERE unique_id=?",
            (max(1, mod_order), uid)
        )
        self.conn.commit()

    def update_mod_category(self, uid, category, category_order=None):
        if category_order is not None:
            self.cursor.execute(
                "UPDATE mods SET category=?, category_order=? WHERE unique_id=?",
                (category, max(1, category_order), uid)
            )
        else:
            self.cursor.execute(
                "UPDATE mods SET category=? WHERE unique_id=?",
                (category, uid)
            )
        self.conn.commit()

    def set_mod_status(self, uid, status):
        self.cursor.execute(
            "UPDATE mods SET status=? WHERE unique_id=?",
            (status, uid)
        )
        self.conn.commit()

    def mark_missing(self, uid: str):
        self.cursor.execute(
            "UPDATE mods SET status=? WHERE unique_id=?",
            (ModStatus.MISSING, uid)
        )
        self.conn.commit()
    # =========================
    # 其它接口
    # =========================
    def get_all_mods(self):
        rows = self.conn.execute("SELECT * FROM mods").fetchall()
        return {row["unique_id"]: dict(row) for row in rows}

    def get_mod(self, uid):
        row = self.conn.execute(
            "SELECT * FROM mods WHERE unique_id=?",
            (uid,)
        ).fetchone()
        return dict(row) if row else None

    def update_mod_version(self, uid, version):
        self.cursor.execute(
            "UPDATE mods SET version=? WHERE unique_id=?",
            (version, uid)
        )
        self.conn.commit()

    def update_mod_source_url(self, uid, url):
        self.cursor.execute(
            "UPDATE mods SET source_url=? WHERE unique_id=?",
            (url, uid)
        )
        self.conn.commit()

    def update_mod_image(self, uid, image_url):
        self.cursor.execute(
            "UPDATE mods SET image_url=? WHERE unique_id=?",
            (image_url, uid)
        )
        self.conn.commit()

    def update_mod_description(self, uid, description):
        self.cursor.execute(
            "UPDATE mods SET description=? WHERE unique_id=?",
            (description, uid)
        )
        self.conn.commit()

    def update_mod_author(self, uid, author):
        self.cursor.execute(
            "UPDATE mods SET author=? WHERE unique_id=?",
            (author, uid)
        )
        self.conn.commit()

    def update_mod_name(self, uid, name):
        self.cursor.execute(
            "UPDATE mods SET name=? WHERE unique_id=?",
            (name, uid)
        )
        self.conn.commit()

    def delete_mod(self, uid):
        self.cursor.execute(
            "DELETE FROM mods WHERE unique_id=?",
            (uid,)
        )
        self.conn.commit()

    def get_all_categories(self):
        """
        返回当前 DB 中存在的所有分类名（去重）
        """
        rows = self.conn.execute(
            "SELECT DISTINCT category FROM mods"
        ).fetchall()
        return [r["category"] for r in rows]

    def get_mods_by_category(self, category: str):
        """
        获取指定分类下的所有 MOD
        """
        sql = """
            SELECT *
            FROM mods
            WHERE category = ?
            ORDER BY mod_order
        """
        self.cursor.execute(sql, (category,))
        return self.cursor.fetchall()

