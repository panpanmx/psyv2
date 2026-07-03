from pydantic import BaseModel


class KnowledgeChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    source_path: str
    section: str
    content: str
    ordinal: int


class MarkdownChunker:
    def __init__(self, max_chars: int = 1200) -> None:
        self.max_chars = max_chars

    def chunk_document(
        self,
        *,
        doc_id: str,
        title: str,
        source_path: str,
        content: str,
    ) -> list[KnowledgeChunk]:
        sections = _split_sections(content, fallback_section=title)
        chunks: list[KnowledgeChunk] = []
        ordinal = 0
        for section, section_text in sections:
            for body in self._split_long_section(section_text):
                stripped = body.strip()
                if not stripped:
                    continue
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{doc_id}:{ordinal}",
                        doc_id=doc_id,
                        title=title,
                        source_path=source_path,
                        section=section,
                        content=stripped,
                        ordinal=ordinal,
                    )
                )
                ordinal += 1
        return chunks

    def _split_long_section(self, text: str) -> list[str]:
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        if not paragraphs:
            return []
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if not current:
                current = paragraph
                continue
            candidate = f"{current}\n\n{paragraph}"
            if len(candidate) <= self.max_chars:
                current = candidate
            else:
                chunks.append(current)
                current = paragraph
        if current:
            chunks.append(current)
        return chunks


def _split_sections(content: str, *, fallback_section: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_section = fallback_section
    current_lines: list[str] = []
    for line in content.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_section, current_lines))
            current_section = line[3:].strip() or fallback_section
            current_lines = []
            continue
        if line.startswith("# "):
            continue
        current_lines.append(line)
    if current_lines:
        sections.append((current_section, current_lines))
    return [(section, "\n".join(lines)) for section, lines in sections]
