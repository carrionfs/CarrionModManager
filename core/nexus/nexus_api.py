import requests

# =========================
# 用于验证N网API有效性
# =========================

class NexusApiError(Exception):
    """Nexus API 相关错误"""
    pass


def validate_api_key(api_key: str, timeout: int = 5) -> dict:
    """
    验证 NexusMods API Key 是否有效，并返回用户信息和下载额度

    :param api_key: 用户输入的 API Key
    :param timeout: 请求超时时间（秒）
    :return: dict，包含验证状态和用户信息
    :raises NexusApiError: 网络或服务异常
    """
    if not api_key:
        return {"valid": False}

    headers = {
        "apikey": api_key,
        "Accept": "application/json"
    }

    try:
        # resp = requests.get(
        #     "https://api.nexusmods.com/v1/users/me.json",
        #     headers=headers,
        #     timeout=timeout
        # )
        resp = requests.get(
            "https://api.nexusmods.com/v1/users/validate.json",
            headers=headers,
            timeout=timeout
        )
        print("验证响应内容：", resp.status_code, resp.text)

        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "user": data,
                "daily_limit": data.get("daily_limit"),
                "daily_left": data.get("daily_left")
            }

        if resp.status_code in (401, 403):
            return {"valid": False}

        raise NexusApiError(f"NexusMods 返回异常状态码: {resp.status_code}")

    except requests.RequestException as e:
        raise NexusApiError("无法连接 NexusMods") from e
