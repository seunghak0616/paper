#!/usr/bin/env python3
"""
Playwright를 사용한 GUI 테스트 및 검토
"""

from playwright.sync_api import sync_playwright
import time
import os

def test_frontend_gui():
    """프론트엔드 GUI 테스트 및 검토"""
    
    with sync_playwright() as p:
        # 브라우저 실행
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            print("🚀 프론트엔드 GUI 테스트 시작...")
            
            # 페이지 로드
            page.goto("http://localhost:3001")
            page.wait_for_load_state("networkidle")
            
            print("✅ 페이지 로드 완료")
            
            # 페이지 제목 확인
            title = page.title()
            print(f"📄 페이지 제목: {title}")
            
            # 헤더 확인
            header = page.locator("h1").first
            if header.is_visible():
                header_text = header.text_content()
                print(f"📋 헤더: {header_text}")
            
            # 검색 입력창 확인
            search_input = page.locator("#searchInput")
            if search_input.is_visible():
                print("✅ 검색 입력창 발견")
                # 검색 테스트
                search_input.fill("AI")
                page.locator("#searchBtn").click()
                page.wait_for_timeout(1000)
                print("✅ 검색 기능 테스트 완료")
            else:
                print("❌ 검색 입력창을 찾을 수 없음")
            
            # 필터 확인
            status_filter = page.locator("#statusFilter")
            if status_filter.is_visible():
                print("✅ 상태 필터 발견")
                status_filter.select_option("success")
                page.wait_for_timeout(1000)
                print("✅ 필터 기능 테스트 완료")
            
            # 통계 카드 확인
            stat_cards = page.locator(".stat-card")
            stat_count = stat_cards.count()
            print(f"📊 통계 카드 수: {stat_count}")
            
            # 논문 카드 확인
            paper_cards = page.locator(".paper-card")
            paper_count = paper_cards.count()
            print(f"📄 논문 카드 수: {paper_count}")
            
            # 뷰 전환 테스트
            list_view_btn = page.locator("#listViewBtn")
            if list_view_btn.is_visible():
                list_view_btn.click()
                page.wait_for_timeout(1000)
                print("✅ 리스트 뷰 전환 완료")
                
                grid_view_btn = page.locator("#gridViewBtn")
                grid_view_btn.click()
                page.wait_for_timeout(1000)
                print("✅ 그리드 뷰 전환 완료")
            
            # 첫 번째 논문 카드 클릭 (모달 테스트)
            if paper_count > 0:
                first_paper = paper_cards.first
                first_paper.click()
                page.wait_for_timeout(1000)
                
                # 모달 확인
                modal = page.locator("#paperModal")
                if modal.is_visible():
                    print("✅ 논문 상세 모달 열림")
                    
                    # 모달 닫기
                    close_btn = page.locator("#closeModal")
                    close_btn.click()
                    page.wait_for_timeout(500)
                    print("✅ 모달 닫기 완료")
                else:
                    print("❌ 모달이 열리지 않음")
            
            # 스크린샷 저장
            screenshot_path = "frontend_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"📸 스크린샷 저장: {screenshot_path}")
            
            # Console 에러 확인
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
            
            # JavaScript 에러 확인
            js_errors = []
            page.on("pageerror", lambda error: js_errors.append(str(error)))
            
            # 잠시 대기하여 에러 수집
            page.wait_for_timeout(2000)
            
            if js_errors:
                print("❌ JavaScript 에러 발견:")
                for error in js_errors:
                    print(f"  - {error}")
            else:
                print("✅ JavaScript 에러 없음")
            
            if console_errors:
                print("❌ Console 에러 발견:")
                for error in console_errors:
                    print(f"  - {error.text}")
            else:
                print("✅ Console 에러 없음")
            
            print("\n🎉 GUI 테스트 완료!")
            
        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_frontend_gui()