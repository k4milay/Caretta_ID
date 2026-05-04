from .base import SegmentationStrategy
from .body_strategy import BodySegmentationStrategy
from .carapace_strategy import CarapaceSegmentationStrategy
from .head_strategy import HeadSegmentationStrategy

_REGISTRY: dict[str, type[SegmentationStrategy]] = {
    "head": HeadSegmentationStrategy,
    "carapace": CarapaceSegmentationStrategy,
    "body": BodySegmentationStrategy,
}


def get_strategy(region: str = "body") -> SegmentationStrategy:
    cls = _REGISTRY.get(region)
    if cls is None:
        raise ValueError(f"Unknown segmentation region '{region}'. Available: {list(_REGISTRY)}")
    return cls()
