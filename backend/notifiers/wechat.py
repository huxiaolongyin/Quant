import httpx

from backend.notifiers.base import BaseNotifier


class WeChatNotifier(BaseNotifier):
    async def send_text(self, content: str) -> bool:
        payload = {"msgtype": "text", "text": {"content": content}}

        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload)
            result = response.json()
            return result.get("errcode") == 0

    async def send_markdown(self, title: str, content: str) -> bool:
        payload = {"msgtype": "markdown", "markdown": {"content": content}}

        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload)
            result = response.json()
            return result.get("errcode") == 0