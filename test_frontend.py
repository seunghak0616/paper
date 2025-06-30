import asyncio

from playwright.async_api import async_playwright


async def test_frontend_functionality():
    """Playwright를 사용해서 프론트엔드 페이지 테스트"""

    print("🎭 Playwright를 사용해서 프론트엔드 테스트 시작")
    print("=" * 60)

    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(headless=False)  # headless=False로 브라우저 보이게
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. 페이지 로드 테스트
            print("🌐 1. 페이지 로드 테스트")
            await page.goto("http://localhost:5001")
            await page.wait_for_load_state('networkidle')

            # 페이지 제목 확인
            title = await page.title()
            print(f"   ✅ 페이지 제목: {title}")

            # 2. 기본 요소 존재 확인
            print("\n🔍 2. UI 요소 존재 확인")

            # 헤더 확인
            header = await page.query_selector('header')
            if header:
                print("   ✅ 헤더 요소 발견")
            else:
                print("   ❌ 헤더 요소 없음")

            # 검색 입력 필드 확인
            search_input = await page.query_selector('input[placeholder*="건축설계"]')
            if search_input:
                print("   ✅ 검색 입력 필드 발견")
            else:
                print("   ❌ 검색 입력 필드 없음")

            # 버튼 확인
            start_button = await page.query_selector('button:has-text("추출 시작")')
            demo_button = await page.query_selector('button:has-text("데모 데이터 로드")')

            if start_button:
                print("   ✅ 추출 시작 버튼 발견")
            else:
                print("   ❌ 추출 시작 버튼 없음")

            if demo_button:
                print("   ✅ 데모 데이터 버튼 발견")
            else:
                print("   ❌ 데모 데이터 버튼 없음")

            # 3. Vue.js 로드 확인
            print("\n🔧 3. JavaScript 프레임워크 로드 확인")

            # Vue.js 확인
            vue_loaded = await page.evaluate("() => typeof Vue !== 'undefined'")
            if vue_loaded:
                print("   ✅ Vue.js 로드됨")
            else:
                print("   ❌ Vue.js 로드 안됨")

            # Axios 확인
            axios_loaded = await page.evaluate("() => typeof axios !== 'undefined'")
            if axios_loaded:
                print("   ✅ Axios 로드됨")
            else:
                print("   ❌ Axios 로드 안됨")

            # 4. Vue 앱 마운트 확인
            print("\n⚙️ 4. Vue 앱 상태 확인")

            # Vue 앱이 마운트되었는지 확인
            app_data = await page.evaluate("""
                () => {
                    const app = document.querySelector('#app');
                    if (app && app.__vue_app__) {
                        return {
                            mounted: true,
                            hasData: true
                        };
                    }
                    return { mounted: false };
                }
            """)

            if app_data.get('mounted'):
                print("   ✅ Vue 앱 마운트됨")
            else:
                print("   ❌ Vue 앱 마운트 안됨")

            # 5. 데모 데이터 로드 테스트
            print("\n📊 5. 데모 데이터 로드 테스트")

            if demo_button:
                print("   🔄 데모 버튼 클릭 중...")
                await demo_button.click()
                await page.wait_for_timeout(2000)  # 2초 대기

                # 논문 카드가 나타났는지 확인
                paper_cards = await page.query_selector_all('.bg-white.rounded-xl.shadow-lg')
                print(f"   📄 논문 카드 발견: {len(paper_cards)}개")

                if len(paper_cards) > 0:
                    print("   ✅ 데모 데이터 로드 성공")

                    # 첫 번째 논문 제목 확인
                    first_title = await page.query_selector('h3.text-lg.font-semibold')
                    if first_title:
                        title_text = await first_title.inner_text()
                        print(f"   📖 첫 번째 논문: {title_text[:50]}...")
                else:
                    print("   ❌ 데모 데이터 로드 실패")

            # 6. 검색 기능 테스트
            print("\n🔍 6. 검색 기능 테스트")

            if search_input:
                print("   🔄 검색어 입력 중...")
                await search_input.fill("테스트 키워드")

                # 입력값 확인
                input_value = await search_input.input_value()
                print(f"   📝 입력된 값: {input_value}")

                if input_value == "테스트 키워드":
                    print("   ✅ 검색어 입력 성공")
                else:
                    print("   ❌ 검색어 입력 실패")

            # 7. API 엔드포인트 테스트
            print("\n🌐 7. API 엔드포인트 테스트")

            # 데모 API 호출
            try:
                response = await page.evaluate("""
                    async () => {
                        try {
                            const response = await fetch('/api/demo');
                            const data = await response.json();
                            return {
                                status: response.status,
                                success: response.ok,
                                paperCount: data.papers ? data.papers.length : 0
                            };
                        } catch (error) {
                            return {
                                status: 'error',
                                error: error.message
                            };
                        }
                    }
                """)

                if response.get('success'):
                    print(f"   ✅ API 호출 성공 (상태: {response['status']}, 논문: {response['paperCount']}개)")
                else:
                    print(f"   ❌ API 호출 실패: {response}")

            except Exception as e:
                print(f"   ❌ API 테스트 오류: {str(e)}")

            # 8. 콘솔 오류 확인
            print("\n🐛 8. 콘솔 오류 확인")

            # 페이지 콘솔 메시지 수집
            console_messages = []

            def handle_console(msg):
                if msg.type in ['error', 'warning']:
                    console_messages.append(f"{msg.type.upper()}: {msg.text}")

            page.on('console', handle_console)

            # 페이지 새로고침하여 초기 로드 오류 확인
            await page.reload()
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)

            if console_messages:
                print("   ⚠️ 발견된 콘솔 메시지:")
                for msg in console_messages[-5:]:  # 최근 5개만 표시
                    print(f"     {msg}")
            else:
                print("   ✅ 콘솔 오류 없음")

            # 9. 네트워크 요청 확인
            print("\n🌍 9. 네트워크 요청 확인")

            network_requests = []

            def handle_request(request):
                if request.url.startswith('http://localhost:5001'):
                    network_requests.append({
                        'url': request.url,
                        'method': request.method
                    })

            page.on('request', handle_request)

            # 데모 버튼 다시 클릭하여 네트워크 요청 확인
            if demo_button:
                await demo_button.click()
                await page.wait_for_timeout(1000)

            print(f"   📡 네트워크 요청 {len(network_requests)}개 발견")
            for req in network_requests[-3:]:  # 최근 3개만 표시
                print(f"     {req['method']} {req['url']}")

            # 10. 반응형 테스트
            print("\n📱 10. 반응형 디자인 테스트")

            # 모바일 크기로 변경
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.wait_for_timeout(1000)

            # 모바일에서 요소 확인
            mobile_search = await page.query_selector('input[placeholder*="건축설계"]')
            if mobile_search:
                is_visible = await mobile_search.is_visible()
                print(f"   📱 모바일에서 검색 필드 표시: {'✅' if is_visible else '❌'}")

            # 데스크톱 크기로 복원
            await page.set_viewport_size({"width": 1280, "height": 720})

            print("\n" + "=" * 60)
            print("🎯 테스트 완료!")

            # 스크린샷 저장
            await page.screenshot(path='frontend_test_screenshot.png')
            print("📸 스크린샷 저장: frontend_test_screenshot.png")

        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {str(e)}")

        finally:
            # 브라우저 종료 (5초 후)
            print("\n⏳ 5초 후 브라우저 종료...")
            await page.wait_for_timeout(5000)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_frontend_functionality())
