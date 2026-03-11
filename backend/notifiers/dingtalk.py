import base64
import hashlib
import hmac
import time
import urllib.parse

import httpx

from backend.notifiers.base import BaseNotifier


class DingTalkNotifier(BaseNotifier):
    async def _sign(self) -> tuple[str, str]:
        if not self.secret:
            return "", ""
        timestamp = str(int(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))
        return timestamp, sign

    async def send_text(self, content: str) -> bool:
        timestamp, sign = await self._sign()
        url = self.webhook_url
        if timestamp and sign:
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        payload = {"msgtype": "text", "text": {"content": content}}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            result = response.json()
            return result.get("errcode") == 0

    async def send_markdown(self, title: str, content: str) -> bool:
        timestamp, sign = await self._sign()
        url = self.webhook_url
        if timestamp and sign:
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        payload = {"msgtype": "markdown", "markdown": {"title": title, "text": content}}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            result = response.json()
            return result.get("errcode") == 0
