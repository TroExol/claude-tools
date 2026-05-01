import pytest
from bin.marketplaces.base import BaseAdapter, AdapterResult, Product
from bin.orchestrator import search_all


class FakeOK(BaseAdapter):
    name = "fake_ok"
    async def search(self, query, max_per=30, city="perm"):
        return AdapterResult(self.name, [Product(self.name, "1", "T", 100, "u", True, {})])
    async def product(self, *a, **k): return None
    async def reviews(self, *a, **k): return []
    async def top_popular(self, *a, **k): return await self.search("x")


class FakeFail(BaseAdapter):
    name = "fake_fail"
    async def search(self, query, max_per=30, city="perm"):
        raise RuntimeError("kaboom")
    async def product(self, *a, **k): return None
    async def reviews(self, *a, **k): return []
    async def top_popular(self, *a, **k): return await self.search("x")


@pytest.mark.asyncio
async def test_search_all_runs_in_parallel_and_isolates_failures():
    results = await search_all([FakeOK(), FakeFail()], "test")
    assert len(results) == 2
    ok = next(r for r in results if r.marketplace == "fake_ok")
    fail = next(r for r in results if r.marketplace == "fake_fail")
    assert ok.is_ok and len(ok.products) == 1
    assert not fail.is_ok and "kaboom" in fail.errors[0]
