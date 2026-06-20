import httpx


PUSHPLUS_SEND_URL = "https://www.pushplus.plus/send"


async def send_pushplus(token: str, title: str, content: str) -> bool:
    """
    发送 pushplus 微信推送。

    发送异常不向外抛出，避免影响任务执行。
    """
    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(PUSHPLUS_SEND_URL, json=payload)
            data = response.json()
    except Exception as exc:
        print(f"pushplus 推送失败：{exc}")
        return False

    if data.get("code") != 200:
        print(f"pushplus 推送失败：{data.get('msg') or data}")
        return False

    print("pushplus 推送成功")
    return True
