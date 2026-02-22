from enum import Enum
# =========================
#  mod的启用状态
# =========================
class ModStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    MISSING = "missing"