# core/tasks/auto_fill_worker.py

from PyQt5.QtCore import QThread, pyqtSignal
from core.database.database import DatabaseManager
from core.nexus.auto_fill import auto_fill_single_mod

# =========================
#后台：从N网获取mod信息
# =========================

class AutoFillWorker(QThread):
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, db_path, profile_root):
        super().__init__()
        self.db_path = db_path
        self.profile_root = profile_root

    def run(self):
        try:
            # ⭐ 用同一个数据库路径创建新连接
            db = DatabaseManager(self.db_path)

            mods = db.get_all_mods()
            total = len(mods)
            count = 0

            for uid, mod in mods.items():
                auto_fill_single_mod(
                    db,
                    self.profile_root,
                    uid,
                    mod
                )
                count += 1
                self.progress_signal.emit(count, total)

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))