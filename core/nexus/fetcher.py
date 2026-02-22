import requests
from core.nexus.nexus_api import validate_api_key, NexusApiError
from core.config.config_manager import get_nexus_api_key

# =========================
#  用于在N网比对数据库内mod
# =========================

class NexusFetcher:
    BASE = "https://api.nexusmods.com/v1"

    def __init__(self):
        self.api_key = get_nexus_api_key()
        if not validate_api_key(self.api_key):
            raise NexusApiError("API Key 无效或未设置")

    def _get(self, url):
        resp = requests.get(
            url,
            headers={"apikey": self.api_key},
            timeout=8
        )
        if resp.status_code != 200:
            raise NexusApiError(f"Nexus API 错误: {resp.status_code}")
        return resp.json()

    def fetch_mod_info(self, mod_id: int):
        """根据 mod_id 获取完整信息"""
        url = f"{self.BASE}/games/stardewvalley/mods/{mod_id}.json"
        return self._get(url)

    def search_mod(self, keyword: str):
        """根据关键词搜索 mod（用于没有 source_url 的情况）"""
        url = f"{self.BASE}/games/stardewvalley/mods.json?terms={keyword}"
        return self._get(url)
