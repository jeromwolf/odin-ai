"""
통합 문서 처리 서비스
Docker 컨테이너 내의 HWP/PDF 서비스와 연동
"""

import os
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
from datetime import datetime
import logging

from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class IntegratedDocumentProcessor(DocumentProcessor):
    """Docker 서비스와 통합된 문서 처리기"""

    def __init__(self):
        super().__init__()

        # Docker 서비스 URL (환경변수에서 읽어옴)
        self.hwp_service_url = os.getenv("HWP_SERVICE_URL", "http://localhost:8002")
        self.pdf_service_url = os.getenv("PDF_SERVICE_URL", "http://localhost:8003")

        # 타임아웃 설정
        self.timeout = aiohttp.ClientTimeout(total=60)

    async def process_hwp_with_service(self, file_path: Path) -> Optional[str]:
        """HWP 서비스를 통한 문서 처리"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # 파일 업로드
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=file_path.name)

                    # HWP 서비스로 전송
                    async with session.post(
                        f"{self.hwp_service_url}/extract",
                        data=data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            text = result.get('text', '')

                            logger.info(f"HWP 서비스 처리 성공: {file_path.name}")
                            return text
                        else:
                            logger.error(f"HWP 서비스 오류: {response.status}")
                            # 폴백: 로컬 hwp5txt 사용
                            return await self.process_hwp(file_path)

        except aiohttp.ClientError as e:
            logger.warning(f"HWP 서비스 연결 실패: {e}")
            # 폴백: 로컬 처리
            return await self.process_hwp(file_path)
        except Exception as e:
            logger.error(f"HWP 처리 중 오류: {e}")
            return None

    async def process_pdf_with_service(self, file_path: Path) -> Optional[str]:
        """PDF 서비스를 통한 문서 처리"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # 파일 업로드
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=file_path.name)

                    # PDF 서비스로 전송
                    async with session.post(
                        f"{self.pdf_service_url}/extract",
                        data=data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            text = result.get('text', '')

                            # 테이블 데이터가 있으면 추가
                            tables = result.get('tables', [])
                            if tables:
                                text += "\n\n## 추출된 표 데이터\n"
                                for i, table in enumerate(tables, 1):
                                    text += f"\n### 표 {i}\n"
                                    text += str(table)

                            logger.info(f"PDF 서비스 처리 성공: {file_path.name}")
                            return text
                        else:
                            logger.error(f"PDF 서비스 오류: {response.status}")
                            # 폴백: 로컬 처리
                            return await self.process_pdf(file_path)

        except aiohttp.ClientError as e:
            logger.warning(f"PDF 서비스 연결 실패: {e}")
            # 폴백: 로컬 처리
            return await self.process_pdf(file_path)
        except Exception as e:
            logger.error(f"PDF 처리 중 오류: {e}")
            return None

    async def process_document_enhanced(
        self,
        file_path: Path,
        use_docker_service: bool = True
    ) -> Dict[str, Any]:
        """향상된 문서 처리 (Docker 서비스 우선 사용)"""

        file_type = self.get_file_type(file_path.name)
        result = {
            "success": False,
            "file_path": str(file_path),
            "file_type": file_type,
            "text": None,
            "markdown_file": None,
            "processed_by": None,
            "processing_time": None
        }

        start_time = datetime.now()

        try:
            # Docker 서비스 사용 여부
            if use_docker_service:
                if file_type == "hwp":
                    text = await self.process_hwp_with_service(file_path)
                    result["processed_by"] = "docker_hwp_service"
                elif file_type == "pdf":
                    text = await self.process_pdf_with_service(file_path)
                    result["processed_by"] = "docker_pdf_service"
                else:
                    # 로컬 처리
                    text = await self.process_document(file_path)
                    result["processed_by"] = "local"
            else:
                # 로컬 처리만 사용
                text = await self.process_document(file_path)
                result["processed_by"] = "local"

            if text:
                # 마크다운 변환
                markdown_content = self._convert_text_to_markdown(
                    text,
                    file_path.name
                )

                # 마크다운 파일 저장
                markdown_file = Path(f"storage/processed/{file_type}") / \
                               f"{file_path.stem}.md"
                markdown_file.parent.mkdir(parents=True, exist_ok=True)

                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                result.update({
                    "success": True,
                    "text": text,
                    "markdown_file": str(markdown_file),
                    "text_length": len(text),
                    "processing_time": (datetime.now() - start_time).total_seconds()
                })

                logger.info(
                    f"문서 처리 완료: {file_path.name} "
                    f"({result['processed_by']}, {result['processing_time']:.2f}초)"
                )
            else:
                result["error"] = "텍스트 추출 실패"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"문서 처리 실패 - {file_path.name}: {e}")

        return result

    async def batch_process_with_docker(
        self,
        file_paths: list[Path],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Docker 서비스를 활용한 일괄 처리"""

        results = {
            "total": len(file_paths),
            "successful": 0,
            "failed": 0,
            "docker_processed": 0,
            "local_processed": 0,
            "results": []
        }

        # 동시 처리 제한
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_limit(file_path: Path):
            async with semaphore:
                return await self.process_document_enhanced(file_path)

        # 병렬 처리
        tasks = [process_with_limit(fp) for fp in file_paths]
        processed_results = await asyncio.gather(*tasks)

        # 결과 집계
        for result in processed_results:
            results["results"].append(result)

            if result["success"]:
                results["successful"] += 1

                if "docker" in result.get("processed_by", ""):
                    results["docker_processed"] += 1
                else:
                    results["local_processed"] += 1
            else:
                results["failed"] += 1

        # 처리 통계
        results["statistics"] = {
            "success_rate": (results["successful"] / results["total"] * 100)
                           if results["total"] > 0 else 0,
            "avg_processing_time": sum(
                r.get("processing_time", 0) for r in results["results"]
            ) / len(results["results"]) if results["results"] else 0,
            "docker_service_rate": (results["docker_processed"] / results["successful"] * 100)
                                  if results["successful"] > 0 else 0
        }

        logger.info(
            f"일괄 처리 완료: "
            f"성공 {results['successful']}/{results['total']}, "
            f"Docker {results['docker_processed']}, "
            f"로컬 {results['local_processed']}"
        )

        return results

    async def health_check(self) -> Dict[str, Any]:
        """Docker 서비스 상태 확인"""
        status = {
            "hwp_service": False,
            "pdf_service": False,
            "local_processor": True,
            "timestamp": datetime.now().isoformat()
        }

        # HWP 서비스 체크
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.hwp_service_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    status["hwp_service"] = response.status == 200
        except:
            pass

        # PDF 서비스 체크
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.pdf_service_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    status["pdf_service"] = response.status == 200
        except:
            pass

        # 전체 상태
        status["all_services_healthy"] = all([
            status["hwp_service"],
            status["pdf_service"],
            status["local_processor"]
        ])

        return status


# 사용 예제
async def main():
    """통합 문서 처리기 테스트"""

    processor = IntegratedDocumentProcessor()

    # 서비스 상태 확인
    health = await processor.health_check()
    print(f"서비스 상태: {health}")

    # 테스트 파일 처리
    test_files = [
        Path("storage/downloads/hwp/sample.hwp"),
        Path("storage/downloads/pdf/sample.pdf"),
    ]

    # Docker 서비스를 활용한 일괄 처리
    results = await processor.batch_process_with_docker(test_files)

    print(f"\n처리 결과:")
    print(f"- 성공: {results['successful']}/{results['total']}")
    print(f"- Docker 처리: {results['docker_processed']}")
    print(f"- 로컬 처리: {results['local_processed']}")
    print(f"- 평균 처리 시간: {results['statistics']['avg_processing_time']:.2f}초")


if __name__ == "__main__":
    asyncio.run(main())