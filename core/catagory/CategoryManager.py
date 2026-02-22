from pathlib import Path
from core.database.database import DatabaseManager

class CategoryManager:
    def __init__(self, page):
        """
        page: moddata 实例（用于 commit_db_change）
        """
        self.page = page
        self.db: DatabaseManager = page.db

    def move_mod(self, mod_id: str, new_category: str):
        """
        UI 层分类变更入口:更新 DB
        """
        mods = self.db.get_all_mods()
        if mod_id not in mods:
            return

        mod = mods[mod_id]
        old_category = mod.get("category", "默认")

        if old_category == new_category:
            return

        #  更新分类（不碰顺序）
        self.db.update_mod_category(mod_id, new_category)

        #  提交 DB 变更，交给 SyncManager 收口
        self.page.commit_db_change()
