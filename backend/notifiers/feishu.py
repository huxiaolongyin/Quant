import hashlib
import hmac
import time

import httpx

from backend.notifiers.base import BaseNotifier


class FeishuNotifier(BaseNotifier):
    async def _sign(self) -> str:
        if not self.secret:
            return ""
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            b"",
            digestmod=hashlib.sha256,
        ).digest()
        signature = hashlib.sha256(hmac_code).hexdigest()
        return timestamp

    async def send_text(self, content: str) -> bool:
        timestamp = await self._sign()
        payload = {
            "msg_type": "text",
            "content": {"text": content},
        }
        if timestamp and self.secret:
            payload["timestamp"] = timestamp
            payload["sign"] = self._generate_sign(timestamp)

        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload)
            result = response.json()
            return result.get("code") == 0

    async def send_markdown(self, title: str, content: str) -> bool:
        timestamp = await self._sign()
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": content,
                    }
                }
            },
        }
        if timestamp and self.secret:
            payload["timestamp"] = timestamp
            payload["sign"] = self._generate_sign(timestamp)

        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload)
            result = response.json()
            return result.get("code") == 0

    def _generate_sign(self, timestamp: str) -> str:
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            b"",
            digestmod=hashlib.sha256,
        ).digest()
        return hashlib.sha256(hmac_code).hexdigest()
