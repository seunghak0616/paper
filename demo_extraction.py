import asyncio
import sys

# ArchiDB 경로 추가
sys.path.append('/Users/seunghakwoo/Library/CloudStorage/GoogleDrive-caadwoo@gmail.com/내 드라이브/code/ArchiDB/backend')


async def demo_extraction_capabilities():
    """초록 및 원문 추출 기능 시연 (데모 데이터)"""

    print('=== Dbpia 완전한 초록 및 원문 추출 기능 시연 ===\n')

    # 데모 논문 데이터
    demo_papers = [
        {
            "title": "스마트 건축 설계를 위한 IoT 기반 환경 모니터링 시스템",
            "authors": "김건축, 박설계, 이스마트",
            "publisher": "한국건축학회",
            "publication": "대한건축학회논문집",
            "dbpia_id": "NODE02345678",
            "abstract": "본 연구는 스마트 건축 환경에서...",  # 기본 API 초록 (짧음)
            "detail_url": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE02345678",
            "publication_year": 2023
        },
        {
            "title": "지속가능한 도시설계를 위한 녹색 인프라 계획 방법론",
            "authors": "정도시, 김녹색, 박지속",
            "publisher": "한국도시설계학회",
            "publication": "도시설계학회지",
            "dbpia_id": "NODE02345679",
            "abstract": "도시의 지속가능성을 위해...",  # 기본 API 초록 (짧음)
            "detail_url": "https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE02345679",
            "publication_year": 2023
        }
    ]

    print('📚 데모 논문 데이터:')
    for i, paper in enumerate(demo_papers, 1):
        print(f'  {i}. {paper["title"]}')
    print()

    # 초록 품질 평가 함수 시연
    def demo_validate_abstract_quality(abstract: str) -> float:
        """초록 품질 점수 계산 데모"""
        if not abstract:
            return 0.0

        score = 0.0

        # 길이 점수 (3점)
        length = len(abstract)
        if length >= 200:
            score += 3.0
        elif length >= 100:
            score += 2.0
        elif length >= 50:
            score += 1.0

        # 구조 점수 (3점)
        sentences = abstract.split('.')
        if len(sentences) >= 3:
            score += 3.0
        elif len(sentences) >= 2:
            score += 2.0
        elif len(sentences) >= 1:
            score += 1.0

        # 학술 키워드 점수 (4점)
        keywords = ['연구', '분석', '결과', '결론', '방법', '목적', '설계', '건축']
        found_keywords = sum(1 for keyword in keywords if keyword in abstract)
        score += min(4.0, found_keywords * 0.5)

        return min(10.0, score)

    # 완전한 초록 데모 데이터
    enhanced_abstracts = {
        "NODE02345678": """본 연구는 스마트 건축 환경에서 실시간 환경 모니터링을 통한 에너지 효율성 향상 방안을 제시한다. 
        IoT(Internet of Things) 센서 네트워크를 활용하여 건물 내 온도, 습도, 조도, 공기질 등을 실시간으로 모니터링하고, 
        이를 기반으로 한 자동화된 환경 제어 시스템을 구축하였다. 
        실험 결과, 기존 건물 대비 에너지 소비량이 25% 감소하였으며, 거주자의 만족도가 30% 향상되었다. 
        본 시스템은 향후 스마트 시티 건설에 중요한 기반 기술로 활용될 수 있을 것으로 기대된다.""",

        "NODE02345679": """급속한 도시화와 기후변화로 인해 도시의 지속가능성 확보가 중요한 과제로 대두되고 있다. 
        본 연구는 녹색 인프라를 활용한 지속가능한 도시설계 방법론을 제시한다. 
        도시 공원, 녹색 지붕, 빗물 정원, 투수성 포장 등의 녹색 인프라 요소들을 체계적으로 계획하고 배치하는 방법을 연구하였다. 
        시뮬레이션 분석 결과, 제안된 방법론을 적용한 지역에서 도시 열섬 현상이 3-5°C 완화되었고, 
        연간 우수 유출량이 40% 감소하는 효과를 확인하였다. 
        이러한 결과는 녹색 인프라가 도시의 환경적 지속가능성 향상에 크게 기여할 수 있음을 보여준다."""
    }

    # 텍스트 추출 품질 평가 함수
    def demo_calculate_extraction_quality(text: str) -> float:
        """텍스트 추출 품질 점수 계산 데모"""
        if not text:
            return 0.0

        score = 0.0

        # 길이 점수 (3점)
        length = len(text)
        if length >= 5000:
            score += 3.0
        elif length >= 2000:
            score += 2.0
        elif length >= 500:
            score += 1.0

        # 한글/영문 비율 점수 (2점)
        import re
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = korean_chars + english_chars

        if total_chars > 0:
            if korean_chars / total_chars > 0.3 or english_chars / total_chars > 0.3:
                score += 2.0
            else:
                score += 1.0

        # 구조 점수 (3점)
        paragraphs = text.split('\n\n')
        if len(paragraphs) >= 10:
            score += 3.0
        elif len(paragraphs) >= 5:
            score += 2.0
        elif len(paragraphs) >= 2:
            score += 1.0

        # 학술 키워드 점수 (2점)
        academic_keywords = ['연구', '분석', '결과', '결론', '방법', '이론', 'research', 'analysis']
        found_keywords = sum(1 for keyword in academic_keywords if keyword.lower() in text.lower())
        score += min(2.0, found_keywords * 0.25)

        return min(10.0, score)

    # 원문 데모 데이터
    full_text_samples = {
        "NODE02345678": """1. 서론
        
        스마트 건축은 정보통신기술(ICT)과 건축 기술의 융합을 통해 에너지 효율성과 거주 편의성을 극대화하는 건축 패러다임이다.
        특히 IoT 기술의 발전과 함께 건물 내 다양한 환경 요소들을 실시간으로 모니터링하고 제어할 수 있는 스마트 시스템의 구축이 가능해졌다.
        
        2. 연구 방법
        
        본 연구에서는 다음과 같은 IoT 센서들을 활용하였다:
        - 온도/습도 센서 (DHT22)
        - 조도 센서 (TSL2561)
        - 공기질 센서 (MQ-135)
        - 동작 감지 센서 (PIR)
        
        3. 시스템 구축
        
        센서 네트워크는 Zigbee 프로토콜을 통해 구성되었으며, 중앙 제어 시스템은 Raspberry Pi 4를 기반으로 개발되었다.
        데이터베이스는 MySQL을 사용하였고, 웹 인터페이스는 React.js로 구현되었다.
        
        4. 실험 결과
        
        6개월간의 실험 기간 동안 다음과 같은 결과를 얻었다:
        - 에너지 소비량 25% 감소
        - 거주자 만족도 30% 향상
        - 실내 공기질 개선 40%
        
        5. 결론
        
        IoT 기반 환경 모니터링 시스템이 스마트 건축의 핵심 기술로서 큰 잠재력을 가지고 있음을 확인하였다.""",

        "NODE02345679": """Abstract
        
        This study proposes a systematic methodology for sustainable urban design using green infrastructure.
        
        1. 연구 배경
        
        도시화 진행에 따른 환경 문제들이 심각해지고 있다. 특히 도시 열섬 현상, 대기 오염, 홍수 위험 증가 등이 
        도시 거주민들의 삶의 질을 크게 저하시키고 있다.
        
        2. 녹색 인프라의 개념
        
        녹색 인프라(Green Infrastructure)는 자연 생태계의 기능을 활용하여 도시 환경 문제를 해결하는 
        지속가능한 접근 방법이다. 주요 구성 요소는 다음과 같다:
        
        2.1 도시 공원
        - 대규모 중앙공원
        - 근린공원
        - 소규모 포켓파크
        
        2.2 녹색 지붕 시스템
        - 집약형 녹색 지붕
        - 광범위형 녹색 지붕
        - 생활형 녹색 지붕
        
        2.3 빗물 관리 시설
        - 빗물 정원 (Rain Garden)
        - 투수성 포장
        - 생태 도랑
        
        3. 계획 방법론
        
        본 연구에서 제안하는 계획 방법론은 다음 5단계로 구성된다:
        1단계: 현황 분석 및 문제점 도출
        2단계: 녹색 인프라 요소 선정
        3단계: 공간 배치 계획
        4단계: 시뮬레이션 분석
        5단계: 효과 검증 및 피드백
        
        4. 사례 연구
        
        서울시 마포구 상암동을 대상으로 제안된 방법론을 적용한 결과:
        - 도시 열섬 완화: 평균 4.2°C 감소
        - 우수 유출량 감소: 42% 저감
        - 대기질 개선: PM2.5 농도 15% 감소
        - 생물 다양성: 조류 종 수 35% 증가
        
        5. 결론 및 제언
        
        녹색 인프라를 활용한 지속가능한 도시설계 방법론이 도시 환경 문제 해결에 효과적임을 확인하였다.
        향후 정책적 지원과 시민 참여를 통해 더욱 확대 적용될 필요가 있다."""
    }

    # 처리 결과 시연
    enhanced_papers = []

    for paper in demo_papers:
        print(f'{"="*80}')
        print(f'📄 논문: {paper["title"]}')
        print(f'👥 저자: {paper["authors"]}')
        print(f'📖 출판: {paper["publication"]} ({paper["publication_year"]})')
        print(f'🔗 ID: {paper["dbpia_id"]}')
        print(f'{"="*80}')

        # 1. 초록 처리
        original_abstract = paper["abstract"]
        enhanced_abstract = enhanced_abstracts.get(paper["dbpia_id"], original_abstract)

        original_quality = demo_validate_abstract_quality(original_abstract)
        enhanced_quality = demo_validate_abstract_quality(enhanced_abstract)

        print('\n📄 초록 처리 결과:')
        print(f'  🔸 원본 초록 길이: {len(original_abstract)}자 (품질: {original_quality:.1f}/10)')
        print(f'  🔸 개선 초록 길이: {len(enhanced_abstract)}자 (품질: {enhanced_quality:.1f}/10)')
        print(f'  🔸 초록 개선율: {((enhanced_quality - original_quality) / original_quality * 100) if original_quality > 0 else 0:.1f}%')

        print('\n  📝 개선된 초록:')
        print(f'     {enhanced_abstract[:300]}...')

        # 2. 원문 처리
        full_text = full_text_samples.get(paper["dbpia_id"], "")
        text_quality = demo_calculate_extraction_quality(full_text) if full_text else 0

        print('\n📖 원문 처리 결과:')
        if full_text:
            print(f'  🔸 원문 길이: {len(full_text):,}자')
            print(f'  🔸 원문 품질: {text_quality:.1f}/10')
            print('  🔸 추출 방법: pdfplumber (데모)')
            print('  🔸 추출 상태: ✅ success')

            print('\n  📝 원문 미리보기:')
            print(f'     {full_text[:500]}...')
        else:
            print('  🔸 원문 상태: ❌ PDF 접근 불가 (데모)')

        # 논문 데이터 업데이트
        enhanced_paper = paper.copy()
        enhanced_paper.update({
            'original_abstract': original_abstract,
            'abstract': enhanced_abstract,
            'abstract_enhanced': True,
            'abstract_quality_score': enhanced_quality,
            'full_text': full_text,
            'text_quality_score': text_quality,
            'extraction_status': 'success' if full_text else 'failed'
        })
        enhanced_papers.append(enhanced_paper)

        print(f'\n{"="*80}\n')

    # 전체 요약
    total_papers = len(enhanced_papers)
    enhanced_abstracts_count = sum(1 for p in enhanced_papers if p.get('abstract_enhanced', False))
    successful_extractions = sum(1 for p in enhanced_papers if p.get('extraction_status') == 'success')

    print('📊 처리 결과 요약:')
    print(f'  🔸 총 처리 논문: {total_papers}개')
    print(f'  🔸 초록 개선: {enhanced_abstracts_count}/{total_papers}개 ({enhanced_abstracts_count/total_papers*100:.1f}%)')
    print(f'  🔸 원문 추출: {successful_extractions}/{total_papers}개 ({successful_extractions/total_papers*100:.1f}%)')

    avg_abstract_quality = sum(p.get('abstract_quality_score', 0) for p in enhanced_papers) / len(enhanced_papers)
    print(f'  🔸 평균 초록 품질: {avg_abstract_quality:.1f}/10')

    text_qualities = [p.get('text_quality_score', 0) for p in enhanced_papers if p.get('text_quality_score')]
    if text_qualities:
        avg_text_quality = sum(text_qualities) / len(text_qualities)
        print(f'  🔸 평균 원문 품질: {avg_text_quality:.1f}/10')

    print('\n🎯 주요 개선사항:')
    print('  ✅ API 기본 초록 → 상세 페이지 완전 초록 추출')
    print('  ✅ PDF 다운로드 → 텍스트 추출 → 품질 평가')
    print('  ✅ 다중 추출 방법 지원 (pdfplumber, PyPDF2)')
    print('  ✅ 자동 품질 점수 계산 및 검증')
    print('  ✅ 파일 관리 및 중복 방지')

if __name__ == "__main__":
    asyncio.run(demo_extraction_capabilities())
