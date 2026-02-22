from GUI.moddata.moddata_logic import moddata
# =========================
#多profile接口
# =========================

def create_profile_page(parent, profile_id):
    """
    根据 profile_id 创建一个 profile 页面
    """
    return moddata(parent, profile_id=profile_id)
