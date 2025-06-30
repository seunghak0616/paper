#!/usr/bin/env python3
"""
Playwright MCP를 사용한 GUI 검토 및 테스트
"""

from playwright.sync_api import sync_playwright
import time
import json

def test_frontend_with_playwright():
    """Playwright를 사용한 프론트엔드 GUI 검토"""
    
    with sync_playwright() as p:
        # 브라우저 실행 (디버깅을 위해 headless=False)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        # Console 및 에러 수집
        console_messages = []
        errors = []
        
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))
        
        page.on("pageerror", lambda error: errors.append(str(error)))
        
        try:
            print("🚀 프론트엔드 GUI 검토 시작...")
            
            # 페이지 접속
            response = page.goto("http://localhost:3000", wait_until="networkidle")
            if response.status != 200:
                print(f"❌ 페이지 로드 실패. 상태 코드: {response.status}")
                return
            
            print("✅ 페이지 로드 성공")
            
            # 페이지 기본 정보 확인
            title = page.title()
            print(f"📄 페이지 제목: {title}")
            
            # 스크린샷 저장
            page.screenshot(path="gui_test_initial.png", full_page=True)
            print("📸 초기 스크린샷 저장: gui_test_initial.png")
            
            # 헤더 확인
            header = page.locator("h1").first
            if header.is_visible():
                header_text = header.text_content()
                print(f"📋 헤더 텍스트: {header_text}")
            else:
                print("❌ 헤더를 찾을 수 없음")
            
            # 검색 기능 테스트
            search_input = page.locator("#searchInput")
            search_btn = page.locator("#searchBtn")
            
            if search_input.is_visible() and search_btn.is_visible():
                print("✅ 검색 요소 발견")
                search_input.fill("AI")
                search_btn.click()
                page.wait_for_timeout(1000)
                print("✅ 검색 기능 테스트 완료")
            else:
                print("❌ 검색 요소를 찾을 수 없음")
            
            # 필터 기능 테스트
            status_filter = page.locator("#statusFilter")
            if status_filter.is_visible():
                print("✅ 상태 필터 발견")
                status_filter.select_option("success")
                page.wait_for_timeout(1000)
                print("✅ 필터 기능 테스트 완료")
            else:
                print("❌ 상태 필터를 찾을 수 없음")
            
            # 통계 카드 확인
            stat_cards = page.locator(".stat-card")
            stat_count = stat_cards.count()
            print(f"📊 발견된 통계 카드: {stat_count}개")
            
            # 논문 카드 확인
            paper_cards = page.locator(".paper-card")
            paper_count = paper_cards.count()
            print(f"📄 발견된 논문 카드: {paper_count}개")
            
            # 뷰 전환 테스트
            grid_view_btn = page.locator("#gridViewBtn")
            list_view_btn = page.locator("#listViewBtn")
            
            if grid_view_btn.is_visible() and list_view_btn.is_visible():
                print("✅ 뷰 전환 버튼 발견")
                
                # 리스트 뷰로 전환
                list_view_btn.click()
                page.wait_for_timeout(500)
                print("✅ 리스트 뷰 전환 완료")
                
                # 그리드 뷰로 다시 전환
                grid_view_btn.click()
                page.wait_for_timeout(500)
                print("✅ 그리드 뷰 전환 완료")
            else:
                print("❌ 뷰 전환 버튼을 찾을 수 없음")
            
            # 모달 테스트 (첫 번째 논문 카드 클릭)
            if paper_count > 0:
                first_paper = paper_cards.first
                first_paper.click()
                page.wait_for_timeout(1000)
                
                modal = page.locator("#paperModal")
                if modal.is_visible():
                    print("✅ 논문 상세 모달 열림")
                    
                    # 모달 내용 확인
                    modal_title = page.locator("#modalTitle")
                    if modal_title.is_visible():
                        modal_title_text = modal_title.text_content()
                        print(f"📄 모달 제목: {modal_title_text}")
                    
                    # 모달 닫기
                    close_btn = page.locator("#closeModal")
                    if close_btn.is_visible():
                        close_btn.click()
                        page.wait_for_timeout(500)
                        print("✅ 모달 닫기 완료")
                else:
                    print("❌ 모달이 열리지 않음")
            
            # 페이지네이션 확인
            pagination = page.locator(".pagination")
            if pagination.is_visible():
                print("✅ 페이지네이션 발견")
                
                # 다음 페이지 버튼 확인
                next_btn = page.locator("#nextBtn")
                if next_btn.is_visible() and not next_btn.is_disabled():
                    next_btn.click()
                    page.wait_for_timeout(1000)
                    print("✅ 다음 페이지 이동 완료")
                    
                    # 이전 페이지로 돌아가기
                    prev_btn = page.locator("#prevBtn")
                    if prev_btn.is_visible() and not prev_btn.is_disabled():
                        prev_btn.click()
                        page.wait_for_timeout(1000)
                        print("✅ 이전 페이지 이동 완료")
            
            # 최종 스크린샷
            page.screenshot(path="gui_test_final.png", full_page=True)
            print("📸 최종 스크린샷 저장: gui_test_final.png")
            
            # 에러 및 콘솔 메시지 검토
            if errors:
                print("\n❌ JavaScript 에러 발견:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print("\n✅ JavaScript 에러 없음")
            
            if console_messages:
                print("\n📋 Console 메시지:")
                for msg in console_messages:
                    if msg["type"] in ["error", "warning"]:
                        print(f"  {msg['type'].upper()}: {msg['text']}")
            
            print("\n🎉 GUI 검토 완료!")
            
            return {
                "success": True,
                "errors": errors,
                "console_messages": console_messages,
                "stat_count": stat_count,
                "paper_count": paper_count
            }
            
        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            # 브라우저 닫기 전에 잠시 대기
            page.wait_for_timeout(2000)
            browser.close()

if __name__ == "__main__":
    result = test_frontend_with_playwright()
    
    # 결과 저장
    with open("gui_test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 테스트 결과가 gui_test_result.json에 저장되었습니다.")