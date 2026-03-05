from typing import Any
import httpx


class LeakRadarClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def search_email(self, email: str, page: int = 1, page_size: int = 100, auto_unlock: bool = False) -> dict[str, Any]:
        payload = {"email": email, "page": page, "page_size": page_size, "auto_unlock": auto_unlock}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.post("/search/email", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def search_domain(
        self,
        domain: str,
        category: str,
        page: int = 1,
        page_size: int = 100,
        auto_unlock: bool = False,
    ) -> dict[str, Any]:
        params = {"page": page, "page_size": page_size, "auto_unlock": str(auto_unlock).lower()}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.get(f"/search/domain/{domain}/{category}", params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

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
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.post("/search/dark-web", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()
