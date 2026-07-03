from app.rag.chunker import MarkdownChunker


def test_chunker_splits_sections_with_metadata() -> None:
    text = "# 焦虑\n\n## 适用场景\n\n考试压力。\n\n## 干预\n\n呼吸练习。"

    chunks = MarkdownChunker(max_chars=40).chunk_document(
        doc_id="anxiety",
        title="焦虑",
        source_path="knowledge_base/anxiety.md",
        content=text,
    )

    assert len(chunks) >= 2
    assert chunks[0].doc_id == "anxiety"
    assert chunks[0].title == "焦虑"
    assert chunks[0].source_path == "knowledge_base/anxiety.md"
    assert chunks[0].section
    assert chunks[0].content
