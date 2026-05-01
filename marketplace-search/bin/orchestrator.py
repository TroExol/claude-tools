from __future__ import annotations
import asyncio
from bin.marketplaces.base import BaseAdapter, AdapterResult


async def _safe_search(adapter: BaseAdapter, query: str, max_per: int, city: str, timeout: int) -> AdapterResult:
    try:
        return await asyncio.wait_for(
            adapter.search(query, max_per=max_per, city=city),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        return AdapterResult(adapter.name, [], [f"{adapter.name} timeout >{timeout}s"])
    except Exception as e:
        return AdapterResult(adapter.name, [], [f"{adapter.name} error: {e}"])


async def search_all(
    adapters: list[BaseAdapter],
    query: str,
    max_per: int = 30,
    city: str = "perm",
    timeout: int = 60,
) -> list[AdapterResult]:
    """Fan out search across adapters in parallel. Errors isolated per-adapter."""
    tasks = [_safe_search(a, query, max_per, city, timeout) for a in adapters]
    return await asyncio.gather(*tasks)


async def top_popular_all(
    adapters: list[BaseAdapter],
    category: str,
    limit: int = 30,
    city: str = "perm",
    timeout: int = 60,
) -> list[AdapterResult]:
    async def _one(a: BaseAdapter) -> AdapterResult:
        try:
            return await asyncio.wait_for(
                a.top_popular(category, limit=limit, city=city),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return AdapterResult(a.name, [], [f"{a.name} timeout >{timeout}s"])
        except Exception as e:
            return AdapterResult(a.name, [], [f"{a.name} top_popular error: {e}"])
    return await asyncio.gather(*[_one(a) for a in adapters])
