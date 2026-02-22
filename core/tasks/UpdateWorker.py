from PyQt5.QtCore import QObject, pyqtSignal

# =========================
#后台：从N网获取mod更新信息
# =========================
class UpdateWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db

    def run(self):
        try:
            from core.mod.update_checker import check_updates_from_nexus
            check_updates_from_nexus(self.db)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
