import re
from hashlib import blake2b
from math import sqrt
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]:
        pass


class LocalHashEmbeddingProvider:
    def __init__(self, dimensions: int = 384) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        for token in _tokens(text):
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 6) for value in vector]


def _tokens(text: str) -> list[str]:
    parts = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text)
    return [part.lower() for part in parts if part.strip()]
