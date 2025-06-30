import asyncio
import sys

# ArchiDB 경로 추가
sys.path.append('/Users/seunghakwoo/Library/CloudStorage/GoogleDrive-caadwoo@gmail.com/내 드라이브/code/ArchiDB/backend')

from crawlers.ddpia_crawler import DDpiaCrawler


async def test_full_extraction():
    """Dbpia 완전한 초록 및 원문 추출 테스트"""
    api_key = '9fd0da6c4c2b3c75bb71611ed333566d'

    print('=== Dbpia 완전한 초록 및 원문 추출 테스트 ===\n')

    try:
        async with DDpiaCrawler(api_key) as crawler:
            # 먼저 API 연결 테스트
            print('🔍 API 연결 테스트 중...')
            basic_result = await crawler.search_papers(
                keyword='컴퓨터',  # 더 일반적인 키워드
                page_size=3
            )

            print(f'기본 검색 결과: {len(basic_result["papers"])}개')

            if len(basic_result["papers"]) == 0:
                print('⚠️  API에서 결과를 가져올 수 없습니다. 키워드를 바꿔서 다시 시도합니다.')

                # 카테고리 없이 시도
                result = await crawler.search_papers(
                    keyword='설계',
                    page_size=5,
                    enhance_abstracts=True,
                    extract_full_text=False
                )
            else:
                print('✅ API 연결 성공! 완전한 추출 테스트를 시작합니다.')

                # 소규모 테스트 (초록 및 원문)
                result = await crawler.search_papers(
                    keyword='컴퓨터',
                    page_size=2,  # 작은 수로 시작
                    enhance_abstracts=True,
                    extract_full_text=True
                )

            print(f'✅ 검색 완료: {len(result["papers"])}개 논문\n')

            for i, paper in enumerate(result['papers'], 1):
                print(f'{"="*60}')
                print(f'논문 {i}: {paper["title"]}')
                print(f'저자: {paper["authors"]}')
                print(f'발행: {paper["publication"]} ({paper.get("publication_year", "N/A")})')
                print(f'{"="*60}')

                # 초록 정보
                print('\n📄 초록 정보:')
                print(f'  - 초록 개선: {"✅" if paper.get("abstract_enhanced", False) else "❌"}')
                print(f'  - 초록 품질: {paper.get("abstract_quality_score", 0):.1f}/10')

                abstract = paper.get('abstract', '')
                if abstract:
                    print(f'  - 초록 길이: {len(abstract)}자')
                    print(f'  - 초록 내용: {abstract[:300]}...')
                else:
                    print('  - 초록: 없음')

                # 원문 정보
                print('\n📖 원문 정보:')
                extraction_status = paper.get('extraction_status', 'pending')
                status_icon = {'success': '✅', 'failed': '❌', 'pending': '⏳'}.get(extraction_status, '❓')
                print(f'  - 원문 추출: {status_icon} {extraction_status}')

                if paper.get('text_quality_score'):
                    print(f'  - 원문 품질: {paper["text_quality_score"]:.1f}/10')

                if paper.get('pdf_local_path'):
                    print(f'  - PDF 파일: {paper["pdf_local_path"]}')
                    print(f'  - 파일 크기: {paper.get("pdf_file_size", 0):,} bytes')

                full_text = paper.get('full_text', '')
                if full_text:
                    print(f'  - 원문 길이: {len(full_text):,}자')
                    print(f'  - 원문 미리보기: {full_text[:500]}...')
                else:
                    print('  - 원문: 추출되지 않음')

                print(f'\n{"="*60}\n')

            # 요약 통계
            total_papers = len(result['papers'])
            enhanced_abstracts = sum(1 for p in result['papers'] if p.get('abstract_enhanced', False))
            successful_extractions = sum(1 for p in result['papers'] if p.get('extraction_status') == 'success')

            print('📊 추출 결과 요약:')
            print(f'  - 총 논문 수: {total_papers}개')

            if total_papers > 0:
                print(f'  - 초록 개선: {enhanced_abstracts}/{total_papers}개 ({enhanced_abstracts/total_papers*100:.1f}%)')
                print(f'  - 원문 추출: {successful_extractions}/{total_papers}개 ({successful_extractions/total_papers*100:.1f}%)')

                avg_abstract_quality = sum(p.get('abstract_quality_score', 0) for p in result['papers']) / len(result['papers'])
                print(f'  - 평균 초록 품질: {avg_abstract_quality:.1f}/10')

                text_qualities = [p.get('text_quality_score', 0) for p in result['papers'] if p.get('text_quality_score')]
                if text_qualities:
                    avg_text_quality = sum(text_qualities) / len(text_qualities)
                    print(f'  - 평균 원문 품질: {avg_text_quality:.1f}/10')
            else:
                print('  - 검색 결과가 없습니다. 다른 키워드를 시도해보세요.')

    except Exception as e:
        print(f'❌ 오류 발생: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_extraction())
