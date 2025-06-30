#!/usr/bin/env python3
"""
간단한 HTTP 서버 - 프론트엔드 정적 파일 서빙용
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    # 현재 디렉토리를 frontend 디렉토리로 변경
    frontend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(frontend_dir)
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 프론트엔드 서버가 시작되었습니다!")
            print(f"📍 URL: http://localhost:{PORT}")
            print(f"📁 디렉토리: {frontend_dir}")
            print("=" * 60)
            print("서버를 중지하려면 Ctrl+C를 누르세요.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 서버가 중지되었습니다.")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 포트 {PORT}이 이미 사용 중입니다.")
            print(f"다른 포트를 사용하거나 기존 서버를 중지하세요.")
        else:
            print(f"❌ 서버 시작 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()