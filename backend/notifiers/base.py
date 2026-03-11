from abc import ABC, abstractmethod
from typing import Optional


class BaseNotifier(ABC):
    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        self.webhook_url = webhook_url
        self.secret = secret

    @abstractmethod
    async def send_text(self, content: str) -> bool:
        pass

    @abstractmethod
    async def send_markdown(self, title: str, content: str) -> bool:
        pass

    async def test_connection(self) -> tuple[bool, str]:
        try:
            result = await self.send_text("Notification channel test - connection successful")
            return result, "Connection successful" if result else "Connection failed"
        except Exception as e:
            return False, str(e)