#!/usr/bin/env python3
"""
Dbpia 완전한 초록 및 원문 추출 시스템 - 프론트엔드 실행 스크립트
"""

import os
import time
import webbrowser
from pathlib import Path


def start_frontend():
    """프론트엔드 서버 시작"""

    print("🚀 Dbpia 완전한 초록 및 원문 추출 시스템")
    print("=" * 60)
    print("📋 시스템 초기화 중...")

    # 필요한 디렉토리 생성
    frontend_dir = Path(__file__).parent / 'frontend'
    downloads_dir = frontend_dir / 'downloads'
    downloads_dir.mkdir(exist_ok=True)

    print(f"📁 프론트엔드 디렉토리: {frontend_dir}")
    print(f"📁 다운로드 디렉토리: {downloads_dir}")

    # 현재 디렉토리를 frontend로 변경
    os.chdir(frontend_dir)

    print("🔧 Flask 서버 시작 중...")
    print("📍 URL: http://localhost:5000")
    print("⏰ 잠시 후 자동으로 브라우저가 열립니다...")
    print("=" * 60)

    # 잠시 후 브라우저 열기
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:5000')
        except:
            print("💡 브라우저를 수동으로 열어 http://localhost:5000 에 접속하세요.")

    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Flask 앱 실행
    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 서버를 종료합니다...")
    except Exception as e:
        print(f"\n❌ 서버 실행 오류: {e}")
        print("💡 문제 해결 방법:")
        print("   1. 포트 5000이 이미 사용 중인지 확인")
        print("   2. 필요한 패키지가 설치되었는지 확인: pip install flask flask-cors")
        print("   3. 수동으로 frontend 디렉토리에서 'python app.py' 실행")

if __name__ == "__main__":
    start_frontend()
