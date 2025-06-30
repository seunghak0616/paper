import asyncio
import xml.etree.ElementTree as ET

import aiohttp


async def test_api_direct():
    """Dbpia API 직접 테스트"""
    api_key = '9fd0da6c4c2b3c75bb71611ed333566d'
    base_url = "http://api.dbpia.co.kr/v2/search/search.xml"

    # 여러 테스트 케이스
    test_cases = [
        {"searchall": "컴퓨터", "target": "se", "pagecount": 3},
        {"searchall": "computer", "target": "se", "pagecount": 3},
        {"searchall": "데이터", "target": "se", "pagecount": 3},
        {"target": "rated_art", "category": "4"},  # 인기논문
    ]

    async with aiohttp.ClientSession() as session:
        for i, params in enumerate(test_cases, 1):
            print(f"\n=== 테스트 케이스 {i} ===")
            print(f"파라미터: {params}")

            # API 키 추가
            params["key"] = api_key

            try:
                async with session.get(base_url, params=params) as response:
                    print(f"HTTP 상태: {response.status}")

                    if response.status == 200:
                        content = await response.text()
                        print(f"응답 길이: {len(content)} 문자")

                        # XML 파싱
                        try:
                            root = ET.fromstring(content)

                            # 에러 확인
                            error_code = root.find('.//error_code')
                            if error_code is not None:
                                error_msg = root.find('.//error_message')
                                print(f"❌ API 에러: {error_code.text}")
                                if error_msg is not None:
                                    print(f"에러 메시지: {error_msg.text}")
                            else:
                                # 결과 확인
                                total_count = root.find('.//totalcount')
                                items = root.findall('.//item')

                                print(f"✅ 총 결과 수: {total_count.text if total_count is not None else '0'}")
                                print(f"✅ 반환된 항목 수: {len(items)}")

                                if items:
                                    first_item = items[0]
                                    title = first_item.find('title')
                                    authors = first_item.find('authors')
                                    print("첫 번째 논문:")
                                    print(f"  제목: {title.text if title is not None else 'N/A'}")
                                    print(f"  저자: {authors.text if authors is not None else 'N/A'}")

                            # 원본 XML 일부 출력
                            print("\n원본 XML (처음 500자):")
                            print(content[:500])

                        except ET.ParseError as e:
                            print(f"❌ XML 파싱 오류: {e}")
                            print(f"응답 내용: {content[:200]}...")
                    else:
                        print(f"❌ HTTP 오류: {response.status}")
                        content = await response.text()
                        print(f"응답: {content[:200]}...")

            except Exception as e:
                print(f"❌ 요청 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_direct())
