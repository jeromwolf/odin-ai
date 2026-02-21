#!/usr/bin/env python
"""
Phase 6: 데이터 품질 분석 시스템
추출 정확도, 데이터 완성도, 비즈니스 활용성 분석
"""

import sys
from pathlib import Path
import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path.cwd() / 'src'))

from sqlalchemy import create_engine, text, func, or_
from sqlalchemy.orm import sessionmaker
from src.database.models import BidAnnouncement, BidExtractedInfo, BidDocument

class DataQualityAnalyzer:
    """데이터 품질 분석기"""

    def __init__(self, database_url: str = "postgresql://blockmeta@localhost:5432/odin_db"):
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def analyze_extraction_accuracy(self) -> Dict:
        """추출 정확도 분석"""

        print("🎯 추출 정확도 분석")
        print("-" * 60)

        start_time = time.time()

        # 1. 카테고리별 추출 현황
        category_stats = self.session.query(
            BidExtractedInfo.info_category,
            func.count(BidExtractedInfo.info_id).label('total_count'),
            func.avg(BidExtractedInfo.confidence_score).label('avg_confidence'),
            func.count(BidExtractedInfo.info_id).filter(
                BidExtractedInfo.confidence_score >= 0.8
            ).label('high_confidence_count')
        ).group_by(BidExtractedInfo.info_category).all()

        print("📊 카테고리별 추출 현황:")
        category_analysis = {}
        for stat in category_stats:
            category = stat.info_category
            total = stat.total_count
            avg_conf = float(stat.avg_confidence) if stat.avg_confidence else 0.0
            high_conf = stat.high_confidence_count

            accuracy_rate = (high_conf / total * 100) if total > 0 else 0

            category_analysis[category] = {
                'total_extractions': total,
                'average_confidence': round(avg_conf, 3),
                'high_confidence_count': high_conf,
                'accuracy_rate': round(accuracy_rate, 1)
            }

            print(f"  • {category}: {total}개 추출, 평균 신뢰도 {avg_conf:.2f}, 정확도 {accuracy_rate:.1f}%")

        # 2. 추출 방법별 성능
        method_stats = self.session.query(
            BidExtractedInfo.extraction_method,
            func.count(BidExtractedInfo.info_id).label('count'),
            func.avg(BidExtractedInfo.confidence_score).label('avg_confidence')
        ).group_by(BidExtractedInfo.extraction_method).all()

        print("\n🔧 추출 방법별 성능:")
        method_analysis = {}
        for stat in method_stats:
            method = stat.extraction_method or 'unknown'
            count = stat.count
            avg_conf = float(stat.avg_confidence) if stat.avg_confidence else 0.0

            method_analysis[method] = {
                'count': count,
                'average_confidence': round(avg_conf, 3)
            }

            print(f"  • {method}: {count}개, 평균 신뢰도 {avg_conf:.2f}")

        # 3. 필드별 상세 분석
        field_stats = self.session.query(
            BidExtractedInfo.info_category,
            BidExtractedInfo.field_name,
            func.count(BidExtractedInfo.info_id).label('count'),
            func.avg(BidExtractedInfo.confidence_score).label('avg_confidence')
        ).group_by(
            BidExtractedInfo.info_category,
            BidExtractedInfo.field_name
        ).order_by(
            BidExtractedInfo.info_category,
            func.count(BidExtractedInfo.info_id).desc()
        ).all()

        print("\n📋 필드별 상세 현황:")
        field_analysis = {}
        current_category = None
        for stat in field_stats:
            category = stat.info_category
            field = stat.field_name
            count = stat.count
            avg_conf = float(stat.avg_confidence) if stat.avg_confidence else 0.0

            if category != current_category:
                current_category = category
                print(f"\n  [{category.upper()}]")
                field_analysis[category] = {}

            field_analysis[category][field] = {
                'count': count,
                'average_confidence': round(avg_conf, 3)
            }

            print(f"    - {field}: {count}개 (신뢰도 {avg_conf:.2f})")

        processing_time = time.time() - start_time

        return {
            'category_analysis': category_analysis,
            'method_analysis': method_analysis,
            'field_analysis': field_analysis,
            'processing_time': processing_time
        }

    def analyze_data_completeness(self) -> Dict:
        """데이터 완성도 분석"""

        print("\n📊 데이터 완성도 분석")
        print("-" * 60)

        start_time = time.time()

        # 1. 공고별 필수 필드 채움율
        total_announcements = self.session.query(BidAnnouncement).count()

        essential_fields = {
            'title': '공고명',
            'organization_name': '발주기관',
            'estimated_price': '추정가격',
            'announcement_date': '공고일',
            'bid_end_date': '입찰마감일',
            'opening_date': '개찰일'
        }

        field_completeness = {}
        print("📋 필수 필드 완성도:")

        for field, korean_name in essential_fields.items():
            count = self.session.query(BidAnnouncement).filter(
                getattr(BidAnnouncement, field).isnot(None)
            ).count()

            completeness_rate = (count / total_announcements * 100) if total_announcements > 0 else 0

            field_completeness[field] = {
                'korean_name': korean_name,
                'filled_count': count,
                'total_count': total_announcements,
                'completeness_rate': round(completeness_rate, 1)
            }

            icon = "✅" if completeness_rate >= 90 else "⚠️" if completeness_rate >= 70 else "❌"
            print(f"  {icon} {korean_name}: {completeness_rate:.1f}% ({count}/{total_announcements})")

        # 2. 문서 처리 완성도
        document_stats = self.session.query(
            BidDocument.processing_status,
            func.count(BidDocument.document_id).label('count')
        ).group_by(BidDocument.processing_status).all()

        print("\n📄 문서 처리 완성도:")
        document_completeness = {}
        total_docs = sum(stat.count for stat in document_stats)

        for stat in document_stats:
            status = stat.processing_status or 'unknown'
            count = stat.count
            rate = (count / total_docs * 100) if total_docs > 0 else 0

            document_completeness[status] = {
                'count': count,
                'rate': round(rate, 1)
            }

            icon = "✅" if status == 'completed' else "❌" if status == 'failed' else "⏳"
            print(f"  {icon} {status}: {rate:.1f}% ({count}/{total_docs})")

        # 3. 추출 정보 커버리지
        announcements_with_extractions = self.session.query(
            func.count(func.distinct(BidExtractedInfo.bid_notice_no))
        ).scalar()

        extraction_coverage = (announcements_with_extractions / total_announcements * 100) if total_announcements > 0 else 0

        print(f"\n🎯 추출 정보 커버리지:")
        print(f"  추출 완료: {extraction_coverage:.1f}% ({announcements_with_extractions}/{total_announcements})")

        # 4. 빈 데이터 분석
        empty_data_analysis = {}

        # 추출된 정보 중 빈 값 비율
        total_extractions = self.session.query(BidExtractedInfo).count()
        empty_extractions = self.session.query(BidExtractedInfo).filter(
            or_(
                BidExtractedInfo.field_value.is_(None),
                BidExtractedInfo.field_value == '',
                BidExtractedInfo.field_value == 'N/A'
            )
        ).count()

        empty_rate = (empty_extractions / total_extractions * 100) if total_extractions > 0 else 0

        empty_data_analysis = {
            'total_extractions': total_extractions,
            'empty_extractions': empty_extractions,
            'empty_rate': round(empty_rate, 1)
        }

        print(f"\n🗃️ 빈 데이터 분석:")
        print(f"  빈 값 비율: {empty_rate:.1f}% ({empty_extractions}/{total_extractions})")

        processing_time = time.time() - start_time

        return {
            'field_completeness': field_completeness,
            'document_completeness': document_completeness,
            'extraction_coverage': round(extraction_coverage, 1),
            'empty_data_analysis': empty_data_analysis,
            'processing_time': processing_time
        }

    def analyze_business_usability(self) -> Dict:
        """비즈니스 활용성 분석"""

        print("\n💼 비즈니스 활용성 분석")
        print("-" * 60)

        start_time = time.time()

        # 1. 실제 검색 시나리오 테스트
        search_scenarios = [
            {
                'name': '고액 공사 (1억원 이상)',
                'condition': 'estimated_price >= 100000000',
                'description': '대형 건설업체 타겟팅'
            },
            {
                'name': '중소기업 적합 (1천만원~5천만원)',
                'condition': 'estimated_price BETWEEN 10000000 AND 50000000',
                'description': '중소기업 입찰 기회'
            },
            {
                'name': 'IT 관련 공고',
                'condition': "title ILIKE '%정보%' OR title ILIKE '%시스템%' OR title ILIKE '%프로그램%'",
                'description': 'IT 기업 타겟팅'
            },
            {
                'name': '건설 관련 공고',
                'condition': "title ILIKE '%공사%' OR title ILIKE '%건축%' OR title ILIKE '%토목%'",
                'description': '건설업체 타겟팅'
            }
        ]

        scenario_results = {}
        print("🎯 검색 시나리오 테스트:")

        for scenario in search_scenarios:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) FROM bid_announcements
                    WHERE {scenario['condition']}
                """)).scalar()

            scenario_results[scenario['name']] = {
                'count': result,
                'description': scenario['description'],
                'usability': 'high' if result >= 10 else 'medium' if result >= 5 else 'low'
            }

            usability_icon = "🟢" if result >= 10 else "🟡" if result >= 5 else "🔴"
            print(f"  {usability_icon} {scenario['name']}: {result}개 ({scenario['description']})")

        # 2. 핵심 비즈니스 정보 품질
        business_info_quality = {}

        # 가격 정보 품질
        price_info = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == 'prices'
        ).count()

        price_quality = {
            'extracted_count': price_info,
            'quality_score': min(price_info / 10 * 100, 100),  # 10개 이상이면 100점
            'business_value': 'critical'
        }

        # 일정 정보 품질
        schedule_info = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == 'dates'
        ).count()

        schedule_quality = {
            'extracted_count': schedule_info,
            'quality_score': min(schedule_info / 20 * 100, 100),  # 20개 이상이면 100점
            'business_value': 'high'
        }

        # 계약 정보 품질
        contract_info = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == 'contract_details'
        ).count()

        contract_quality = {
            'extracted_count': contract_info,
            'quality_score': min(contract_info / 15 * 100, 100),  # 15개 이상이면 100점
            'business_value': 'medium'
        }

        business_info_quality = {
            'prices': price_quality,
            'dates': schedule_quality,
            'contract_details': contract_quality
        }

        print(f"\n💰 핵심 비즈니스 정보 품질:")
        for category, quality in business_info_quality.items():
            score = quality['quality_score']
            value = quality['business_value']
            count = quality['extracted_count']

            score_icon = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            print(f"  {score_icon} {category}: {score:.1f}점 ({count}개 추출, {value} 가치)")

        # 3. 사용자 관점 데이터 품질 평가
        user_perspective = {
            'searchability': self._evaluate_searchability(),
            'readability': self._evaluate_readability(),
            'actionability': self._evaluate_actionability()
        }

        print(f"\n👤 사용자 관점 품질 평가:")
        for aspect, score in user_perspective.items():
            score_icon = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            aspect_korean = {
                'searchability': '검색성',
                'readability': '가독성',
                'actionability': '실행성'
            }[aspect]
            print(f"  {score_icon} {aspect_korean}: {score:.1f}점")

        # 4. 개선 우선순위 도출
        improvement_priorities = self._calculate_improvement_priorities(
            business_info_quality, user_perspective, scenario_results
        )

        print(f"\n🎯 개선 우선순위:")
        for i, priority in enumerate(improvement_priorities, 1):
            urgency_icon = "🔥" if priority['urgency'] == 'high' else "⚠️" if priority['urgency'] == 'medium' else "📋"
            print(f"  {urgency_icon} {i}. {priority['area']}: {priority['issue']} (영향: {priority['impact']})")

        processing_time = time.time() - start_time

        return {
            'scenario_results': scenario_results,
            'business_info_quality': business_info_quality,
            'user_perspective': user_perspective,
            'improvement_priorities': improvement_priorities,
            'processing_time': processing_time
        }

    def _evaluate_searchability(self) -> float:
        """검색성 평가"""
        # 인덱스 유무, 검색 가능한 필드 수, 검색 응답속도 등을 종합 평가
        with self.engine.connect() as conn:
            # 인덱스 존재 여부 확인
            indexes = conn.execute(text("""
                SELECT count(*) FROM pg_indexes
                WHERE tablename IN ('bid_announcements', 'bid_extracted_info')
            """)).scalar()

            # 검색 가능한 텍스트 필드 비율
            text_fields_with_data = conn.execute(text("""
                SELECT
                    (COUNT(CASE WHEN title IS NOT NULL THEN 1 END) +
                     COUNT(CASE WHEN organization_name IS NOT NULL THEN 1 END)) * 50.0 /
                    (COUNT(*) * 2) as text_completeness
                FROM bid_announcements
            """)).scalar()

            # Convert to float if Decimal
            if text_fields_with_data:
                text_fields_with_data = float(text_fields_with_data)

        searchability_score = min(
            (indexes / 5 * 30) +  # 인덱스 점수 (최대 30점)
            (text_fields_with_data or 0) +  # 텍스트 완성도 (최대 50점)
            20,  # 기본 구조 점수 (20점)
            100
        )

        return round(searchability_score, 1)

    def _evaluate_readability(self) -> float:
        """가독성 평가"""
        # 추출된 정보의 구조화 정도, 한글 처리, 데이터 형식 일관성 등

        total_extractions = self.session.query(BidExtractedInfo).count()
        if total_extractions == 0:
            return 0.0

        # 구조화된 정보 비율
        structured_info = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category.in_(['prices', 'dates', 'contract_details'])
        ).count()

        structure_score = (structured_info / total_extractions * 60) if total_extractions > 0 else 0

        # 신뢰도 점수
        high_confidence = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.confidence_score >= 0.7
        ).count()

        confidence_score = (high_confidence / total_extractions * 40) if total_extractions > 0 else 0

        readability_score = min(structure_score + confidence_score, 100)
        return round(readability_score, 1)

    def _evaluate_actionability(self) -> float:
        """실행성 평가"""
        # 비즈니스 의사결정에 필요한 핵심 정보 추출 정도

        # 핵심 정보 카테고리별 점수
        prices_count = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == 'prices'
        ).count()

        dates_count = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == 'dates'
        ).count()

        contracts_count = self.session.query(BidExtractedInfo).filter(
            BidExtractedInfo.info_category == 'contract_details'
        ).count()

        # 각 카테고리 점수 (최대 100점 기준으로 비례 계산)
        price_score = min(prices_count / 5 * 40, 40)  # 가격 정보 40점
        date_score = min(dates_count / 10 * 35, 35)   # 일정 정보 35점
        contract_score = min(contracts_count / 8 * 25, 25)  # 계약 정보 25점

        actionability_score = price_score + date_score + contract_score
        return round(actionability_score, 1)

    def _calculate_improvement_priorities(self, business_quality, user_perspective, scenarios) -> List[Dict]:
        """개선 우선순위 계산"""

        priorities = []

        # 비즈니스 정보 품질 기반 우선순위
        for category, quality in business_quality.items():
            if quality['quality_score'] < 70:
                urgency = 'high' if quality['business_value'] == 'critical' else 'medium'
                priorities.append({
                    'area': f'{category} 정보 추출',
                    'issue': f'품질 점수 {quality["quality_score"]:.1f}점으로 낮음',
                    'impact': quality['business_value'],
                    'urgency': urgency
                })

        # 사용자 관점 품질 기반 우선순위
        for aspect, score in user_perspective.items():
            if score < 70:
                priorities.append({
                    'area': f'시스템 {aspect}',
                    'issue': f'{score:.1f}점으로 개선 필요',
                    'impact': 'high' if aspect == 'searchability' else 'medium',
                    'urgency': 'medium'
                })

        # 검색 시나리오 기반 우선순위
        low_usability_scenarios = [name for name, result in scenarios.items()
                                 if result['usability'] == 'low']

        if low_usability_scenarios:
            priorities.append({
                'area': '비즈니스 시나리오 커버리지',
                'issue': f'{len(low_usability_scenarios)}개 시나리오에서 데이터 부족',
                'impact': 'medium',
                'urgency': 'medium'
            })

        # 우선순위 정렬 (urgency > impact 순)
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        impact_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

        priorities.sort(key=lambda x: (
            priority_order.get(x['urgency'], 0),
            impact_order.get(x['impact'], 0)
        ), reverse=True)

        return priorities[:5]  # 상위 5개만 반환

    def generate_quality_report(self) -> Dict:
        """전체 품질 리포트 생성"""

        print("📋 데이터 품질 종합 리포트 생성")
        print("=" * 80)

        start_time = time.time()

        # 각 분석 실행
        accuracy_results = self.analyze_extraction_accuracy()
        completeness_results = self.analyze_data_completeness()
        usability_results = self.analyze_business_usability()

        # 종합 점수 계산
        overall_score = self._calculate_overall_score(
            accuracy_results, completeness_results, usability_results
        )

        total_time = time.time() - start_time

        # 최종 리포트
        report = {
            'generation_time': datetime.now().isoformat(),
            'overall_score': overall_score,
            'accuracy_analysis': accuracy_results,
            'completeness_analysis': completeness_results,
            'usability_analysis': usability_results,
            'total_processing_time': round(total_time, 3)
        }

        print(f"\n📊 종합 품질 점수: {overall_score:.1f}/100")
        score_grade = (
            "A" if overall_score >= 90 else
            "B" if overall_score >= 80 else
            "C" if overall_score >= 70 else
            "D" if overall_score >= 60 else "F"
        )
        print(f"🏆 등급: {score_grade}")

        return report

    def _calculate_overall_score(self, accuracy, completeness, usability) -> float:
        """종합 점수 계산"""

        # 정확도 점수 (30%)
        avg_accuracy = sum(
            cat['accuracy_rate'] for cat in accuracy['category_analysis'].values()
        ) / len(accuracy['category_analysis']) if accuracy['category_analysis'] else 0

        accuracy_score = avg_accuracy * 0.3

        # 완성도 점수 (35%)
        completion_rate = completeness['extraction_coverage']
        completeness_score = completion_rate * 0.35

        # 활용성 점수 (35%)
        usability_scores = list(usability['user_perspective'].values())
        avg_usability = sum(usability_scores) / len(usability_scores) if usability_scores else 0
        usability_score = avg_usability * 0.35

        overall = accuracy_score + completeness_score + usability_score
        return round(min(overall, 100), 1)

    def close(self):
        """세션 종료"""
        self.session.close()


def main():
    """데이터 품질 분석 실행"""

    analyzer = DataQualityAnalyzer()

    try:
        # 전체 품질 리포트 생성
        report = analyzer.generate_quality_report()

        # 리포트 파일 저장
        report_file = Path("data_quality_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n💾 상세 리포트 저장: {report_file}")
        print(f"⏱️ 총 분석 시간: {report['total_processing_time']:.3f}초")

        # 성공 여부 판정
        overall_score = report['overall_score']
        if overall_score >= 80:
            print(f"\n🎉 Phase 6: 데이터 품질 분석 성공! (점수: {overall_score})")
            return True
        else:
            print(f"\n⚠️ Phase 6: 데이터 품질 개선 필요 (점수: {overall_score})")
            return False

    except Exception as e:
        print(f"❌ 데이터 품질 분석 실패: {e}")
        return False

    finally:
        analyzer.close()


if __name__ == "__main__":
    success = main()