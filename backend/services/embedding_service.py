"""
RAG 임베딩 서비스
벡터 임베딩 생성 및 관리
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)

# OpenAI client - graceful import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai 패키지 미설치 - 임베딩 서비스 비활성화")


class EmbeddingProvider(ABC):
    """임베딩 제공자 인터페이스"""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """텍스트 목록을 임베딩 벡터로 변환"""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """검색 쿼리를 임베딩 벡터로 변환"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """임베딩 벡터 차원"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """모델 이름"""
        pass


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI text-embedding-3-small 기반 임베딩"""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다")
        if not OPENAI_AVAILABLE:
            raise ImportError("openai 패키지가 설치되지 않았습니다: pip install openai")

        self._client = OpenAI(api_key=self._api_key)
        self._model = model
        self._dimension = 1536  # text-embedding-3-small default

        logger.info(f"OpenAI 임베딩 서비스 초기화: model={model}, dim={self._dimension}")

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    def embed_texts(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """텍스트 목록을 배치로 임베딩 생성

        Args:
            texts: 임베딩할 텍스트 목록
            batch_size: API 호출당 텍스트 수 (OpenAI 최대 2048)

        Returns:
            임베딩 벡터 목록 (각 벡터는 float 리스트)
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Clean texts (remove empty, truncate long ones)
            cleaned = [t[:8000] if t else " " for t in batch]

            try:
                response = self._client.embeddings.create(
                    input=cleaned,
                    model=self._model
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                if i + batch_size < len(texts):
                    time.sleep(0.1)  # Rate limit safety

            except Exception as e:
                logger.error(f"임베딩 생성 실패 (batch {i//batch_size}): {e}")
                # Fill with None for failed batch
                all_embeddings.extend([None] * len(batch))

        return all_embeddings

    def embed_query(self, query: str) -> Optional[List[float]]:
        """검색 쿼리 임베딩 (단일 텍스트, 빠른 응답)"""
        try:
            response = self._client.embeddings.create(
                input=[query[:8000]],
                model=self._model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"쿼리 임베딩 실패: {e}")
            return None


# Singleton instance
_embedding_provider: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> Optional[EmbeddingProvider]:
    """임베딩 제공자 싱글턴 인스턴스 반환"""
    global _embedding_provider

    if _embedding_provider is not None:
        return _embedding_provider

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY 미설정 - 임베딩 서비스 비활성화")
        return None

    if not OPENAI_AVAILABLE:
        logger.warning("openai 패키지 미설치 - 임베딩 서비스 비활성화")
        return None

    try:
        _embedding_provider = OpenAIEmbedding(api_key=api_key)
        return _embedding_provider
    except Exception as e:
        logger.error(f"임베딩 서비스 초기화 실패: {e}")
        return None
