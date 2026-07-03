import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.db.session import create_engine, create_sessionmaker
from app.rag.embeddings import LocalHashEmbeddingProvider
from app.rag.ingestion import KnowledgeIngestionService


async def _ingest(path: Path) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    sessionmaker = create_sessionmaker(engine)
    try:
        async with sessionmaker() as session:
            service = KnowledgeIngestionService(
                repository=KnowledgeRepository(session),
                embedding_provider=LocalHashEmbeddingProvider(),
            )
            result = await service.ingest_directory(path)
            await session.commit()
            print(f"ingested documents={result.document_count} chunks={result.chunk_count}")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.rag.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--path", default="knowledge_base")
    args = parser.parse_args()

    if args.command == "ingest":
        asyncio.run(_ingest(Path(args.path)))


if __name__ == "__main__":
    main()
