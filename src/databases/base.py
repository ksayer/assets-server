from typing import Protocol, TypedDict, runtime_checkable


class RatePoint(TypedDict):
    assetId: int
    assetName: str
    time: int
    value: float


@runtime_checkable
class RateRepositoryProtocol(Protocol):
    async def init_db(self) -> None: ...

    async def get_assets_points(self, asset_id: int, period: int = ...) -> list[RatePoint]: ...

    async def insert_many(self, points: list[RatePoint]) -> None: ...
