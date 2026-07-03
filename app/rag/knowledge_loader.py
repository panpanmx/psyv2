from pathlib import Path


class KnowledgeLoader:
    def __init__(self, base_dir: str = "knowledge_base") -> None:
        self.base_dir = Path(base_dir)

    def load(self) -> list[dict[str, str]]:
        if not self.base_dir.exists():
            return []
        documents: list[dict[str, str]] = []
        for path in sorted(self.base_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            documents.append({"id": path.stem, "title": _title(text, path.stem), "content": text})
        return documents


def _title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback

