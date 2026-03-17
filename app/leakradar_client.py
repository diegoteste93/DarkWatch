import logging
from typing import Any
import httpx

from app.exceptions import ProviderUnavailableError

logger = logging.getLogger(__name__)


class LeakRadarClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.request(method, path, headers=self.headers, **kwargs)
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException as exc:
            logger.warning("LeakRadar timeout path=%s", path)
            raise ProviderUnavailableError("Provider timeout") from exc
        except httpx.HTTPError as exc:
            logger.warning("LeakRadar http error path=%s", path)
            raise ProviderUnavailableError("Provider unavailable") from exc

    async def search_email(self, email: str, page: int = 1, page_size: int = 100, auto_unlock: bool = False) -> dict[str, Any]:
        payload = {"email": email, "page": page, "page_size": page_size, "auto_unlock": auto_unlock}
        return await self._request("POST", "/search/email", json=payload)

    async def search_domain(
        self,
        domain: str,
        category: str,
        page: int = 1,
        page_size: int = 100,
        auto_unlock: bool = False,
    ) -> dict[str, Any]:
        params = {"page": page, "page_size": page_size, "auto_unlock": str(auto_unlock).lower()}
        return await self._request("GET", f"/search/domain/{domain}/{category}", params=params)

    async def search_dark_web(
        self,
        query: str,
        page: int = 1,
        page_size: int = 25,
        sources: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query, "page": page, "page_size": page_size}
        if sources is not None:
            payload["sources"] = sources
        if date_from:
            payload["date_from"] = date_from
        if date_to:
            payload["date_to"] = date_to
        return await self._request("POST", "/search/dark-web", json=payload)
