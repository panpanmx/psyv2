from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.orchestrator import AgentOrchestrator
from app.clinical.llm_signal_extractor import LLMSignalExtractor
from app.core.config import Settings
from app.llm.prompt_registry import PromptRegistry
from app.llm.provider_factory import create_llm_provider
from app.memory.profile_memory import ProfileMemory
from app.observability.audit import AuditLogger
from app.rag.knowledge_loader import KnowledgeLoader
from app.rag.retriever import KnowledgeRetriever


class AppServices:
    def __init__(
        self,
        settings: Settings,
        sessionmaker: async_sessionmaker[AsyncSession],
    ) -> None:
        self.sessionmaker = sessionmaker
        self.profile_memory = ProfileMemory()
        self.audit_logger = AuditLogger(settings.audit_log_path)
        self.llm_provider = create_llm_provider(settings)
        self.prompt_registry = PromptRegistry()
        self.llm_signal_extractor = (
            LLMSignalExtractor(
                provider=self.llm_provider,
                prompt_registry=self.prompt_registry,
            )
            if settings.llm_signal_extraction_enabled
            else None
        )
        self.retriever = KnowledgeRetriever(
            KnowledgeLoader(settings.knowledge_base_dir),
            top_k=settings.rag_top_k,
        )
        self.agent = AgentOrchestrator(
            profile_memory=self.profile_memory,
            retriever=self.retriever,
            audit_logger=self.audit_logger,
            sessionmaker=sessionmaker,
            llm_signal_extractor=self.llm_signal_extractor,
            llm_provider=self.llm_provider,
            prompt_registry=self.prompt_registry,
        )
