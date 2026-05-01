from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from abc import ABC, abstractmethod


@dataclass
class Product:
    marketplace: str
    marketplace_product_id: str
    title: str
    price: int
    url: str
    in_stock: bool
    raw: dict[str, Any]
    old_price: int | None = None
    rating: float | None = None
    reviews_count: int | None = None
    image_url: str | None = None
    delivery: str | None = None


@dataclass
class Review:
    marketplace: str
    product_id: str
    rating: int
    text: str
    author: str | None = None
    date: str | None = None
    pros: str | None = None
    cons: str | None = None
    helpful_count: int | None = None


@dataclass
class AdapterResult:
    marketplace: str
    products: list[Product]
    errors: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        return not self.errors


class BaseAdapter(ABC):
    """Abstract base for marketplace adapters."""

    name: str = ""

    @abstractmethod
    async def search(
        self,
        query: str,
        max_per: int = 30,
        city: str = "perm",
    ) -> AdapterResult:
        ...

    @abstractmethod
    async def product(self, product_id: str, city: str = "perm") -> Product | None:
        ...

    @abstractmethod
    async def reviews(self, product_id: str, limit: int = 50) -> list[Review]:
        ...

    @abstractmethod
    async def top_popular(
        self,
        category: str,
        limit: int = 30,
        city: str = "perm",
    ) -> AdapterResult:
        ...
