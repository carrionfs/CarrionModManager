import os
import requests
from urllib.parse import urlparse
from typing import Optional

# =========================
#  用于缓存N网获取的image_URL
# =========================

def download_image(url: str, profile_root: str) -> Optional[str]:
    """
    下载 Nexus 图片并永久缓存到当前 profile 的 .cache/images 目录
    """
    if not url or not profile_root:
        return None

    cache_dir = os.path.join(profile_root, ".cache", "images")
    os.makedirs(cache_dir, exist_ok=True)

    filename = os.path.basename(urlparse(url).path)
    local_path = os.path.join(cache_dir, filename)

    # 已存在直接复用（永久缓存）
    if os.path.exists(local_path):
        return local_path

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(resp.content)
            print("[IMAGE] saved to", local_path)
            return local_path
    except Exception as e:
        print("[IMAGE] download failed:", e)

    return None
