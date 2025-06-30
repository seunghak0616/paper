import argparse
import json
import os
import random
import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from time import sleep
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from loguru import logger
from playwright.sync_api import expect, sync_playwright
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Logger 설정 (loguru)
# ---------------------------------------------------------------------------

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logger.add(
    LOG_DIR / "crawler_{time}.log",
    rotation="10 MB",
    retention="10 days",
    backtrace=True,
    diagnose=True,
    level="INFO",
    encoding="utf-8",
)
logger.info(f"Logging initialized. Logs → {LOG_DIR}")

# ---------------------------------------------------------------------------
# Constants & Helpers
# ---------------------------------------------------------------------------
API_HOST_SEARCH = "https://api.dbpia.co.kr/v2/search/search.xml"
API_HOST_BEST = "https://www.dbpia.co.kr/main-tab-popular"
MAX_PAGE_SIZE = 100  # DBpia Open API 기준 최대값


def build_query(api_key: str, keyword: str, page: int, page_size: int, api_type: str = "search") -> str:
    """쿼리 URL 생성."""
    if api_type == "best":
        return API_HOST_BEST
    else: # search
        return f"{API_HOST_SEARCH}?{urlencode({'key': api_key, 'searchall': keyword, 'pagenumber': page, 'result': page_size, 'order': 'date', 'version': '2.1'})}"


def parse_response(response: requests.Response, api_type: str = "search") -> list[dict]:
    """API 응답을 파싱하여 논문 딕셔너리 리스트 반환."""
    if api_type == "best":
        items = []
        try:
            data = response.json()
            for item_data in data.get("nodeInfo", []):
                items.append({
                    "title": item_data.get("nodeTitle"),
                    "id": item_data.get("nodeId"),
                    "authors": None, # 인기논문 API는 저자 정보 미제공
                    "publisher": None,
                    "pdf_url": f"https://www.dbpia.co.kr/pdf/{item_data.get('nodeId')}_ko" # PDF URL 추정
                })
        except json.JSONDecodeError:
            logger.error("Best thesis API 응답이 JSON 형식이 아닙니다.")
        return items

    root = ElementTree.fromstring(response.content)
    items_el = root.findall(".//item")
    items = []
    for el in items_el:
        title = el.findtext("title") or "untitled"
        pdf_url = el.findtext("pdf") or el.findtext("link")  # Fallback
        items.append({
            "title": title.strip(),
            "authors": el.findtext("author"),
            "year": el.findtext("pubyear"),
            "publisher": el.findtext("publisher"),
            "pdf_url": pdf_url,
            "raw": ElementTree.tostring(el, encoding="unicode"),
        })
    return items


def search_papers(api_key: str, keyword: str, pages: int = 1, page_size: int = MAX_PAGE_SIZE, api_type: str = "search") -> list[dict]:
    """DBpia API 호출로 논문 리스트 반환."""
    results: list[dict] = []
    for page in tqdm(range(1, pages + 1), desc=f"{api_type} API 페이지"):
        url = build_query(api_key, keyword, page, page_size, api_type)
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"페이지 {page} 요청 실패: {resp.status_code}")
            continue
        items = parse_response(resp, api_type)
        if not items:
            logger.info(f"페이지 {page}에 결과 없음, 중단")
            break
        results.extend(items)
        sleep(0.2)  # API rate-limit 우회용
        time.sleep(random.uniform(1, 3))
    return results


def sanitize_filename(name: str) -> str:
    """파일시스템에 안전한 문자열로 변환."""
    import re

    name = re.sub(r"[\\/:*?\"<>|]", "_", name)  # Windows 금지 문자 치환
    name = re.sub(r"\s+", " ", name).strip()
    return name[:150]  # 너무 긴 파일명 방지


def download_pdf(item: dict, dest_dir: Path) -> bool:
    """단일 논문의 PDF 다운로드."""
    url = item.get("pdf_url")
    if not url:
        logger.debug(f"PDF URL 없음: {item['title']}")
        return False

    filename = sanitize_filename(item["title"]) + ".pdf"
    dest_path = dest_dir / filename
    if dest_path.exists():
        logger.debug(f"이미 존재: {dest_path.name}")
        return False

    try:
        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info(f"PDF 저장 완료: {dest_path.name}")
        return True
    except Exception as e:
        logger.warning(f"PDF 다운로드 실패 ({item['title']}): {e}")
        return False


# ---------------------------------------------------------------------------
# Checkpoint Helpers
# ---------------------------------------------------------------------------

def load_checkpoint(path: Path) -> set[str]:
    """체크포인트 파일에서 이미 다운로드한 PDF 파일명을 집합으로 반환."""
    if path.exists():
        try:
            data = json.loads(path.read_text("utf-8"))
            return set(data.get("downloaded", []))
        except Exception as e:
            logger.warning(f"체크포인트 로드 실패: {e}")
    return set()


def save_checkpoint(path: Path, downloaded: set[str]):
    """현재까지 다운로드된 파일명을 체크포인트 파일에 저장."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"downloaded": list(downloaded)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning(f"체크포인트 저장 실패: {e}")


def download_pdfs_with_playwright(metadata_path: Path, output_dir: Path, checkpoint_path: Path, headless: bool = True):
    """Playwright를 사용하여 로그인 후 PDF 다운로드."""
    # .env 파일 수동 로드
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    if key not in os.environ:
                         os.environ[key] = value

    dbpia_id = os.environ.get("DBPIA_ID")
    dbpia_pw = os.environ.get("DBPIA_PW")

    if not all([dbpia_id, dbpia_pw]):
        logger.warning("DBPIA_ID 또는 DBPIA_PW 환경 변수가 없어 PDF 다운로드를 건너뜁니다.")
        return

    if not metadata_path.exists():
        logger.warning(f"{metadata_path} 파일이 없어 PDF 다운로드를 건너뜁니다.")
        return

    papers = json.loads(metadata_path.read_text("utf-8"))
    downloaded_files = load_checkpoint(checkpoint_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        # 로그인 페이지로 이동 및 로그인 수행
        logger.info("DBpia에 로그인합니다...")
        page.goto("https://www.dbpia.co.kr/member/login/goLoginPage")
        page.fill("input[name='mem_id']", dbpia_id)
        page.fill("input[name='mem_pwd']", dbpia_pw)
        page.click("button.login_btn")

        # 로그인 성공 확인 (마이페이지 버튼 등이 보이는지)
        try:
            expect(page.get_by_role("link", name="마이페이지")).to_be_visible(timeout=10000)
            logger.info("로그인 성공.")
        except Exception:
            logger.error("로그인에 실패했습니다. ID/PW를 확인해주세요.")
            browser.close()
            return

        for item in tqdm(papers, desc="PDF 다운로드 (Playwright)"):
            node_id = item.get("id")
            title = sanitize_filename(item.get("title", f"unknown_{node_id}"))
            dest_path = output_dir / f"{title}.pdf"

            if dest_path.name in downloaded_files:
                logger.debug(f"이미 존재 (체크포인트): {dest_path.name}")
                continue

            if not node_id:
                continue

            detail_page_url = f"https://www.dbpia.co.kr/journal/articleDetail?nodeId={node_id}"

            try:
                page.goto(detail_page_url, wait_until="domcontentloaded")

                # "원문보기" 또는 "다운로드" 버튼 클릭
                # 다운로드 이벤트 리스너 설정
                with page.expect_download() as download_info:
                    # 실제 버튼 셀렉터는 다를 수 있음
                    page.get_by_role("link", name="원문보기").first.click()

                download = download_info.value
                download.save_as(dest_path)
                logger.info(f"다운로드 완료: {dest_path.name}")

                downloaded_files.add(dest_path.name)
                save_checkpoint(checkpoint_path, downloaded_files)

            except Exception as e:
                logger.warning(f"'{title}' 다운로드 실패: {e}")

            # 서버 부하 방지를 위해 요청 간 랜덤 딜레이 추가
            time.sleep(random.uniform(3, 7))

        browser.close()
        logger.info("Playwright PDF 다운로드 완료.")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    # .env 파일의 절대 경로를 찾아 명시적으로 로드
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
    else:
        load_dotenv() # Fallback
    parser = argparse.ArgumentParser(description="DBpia 논문 크롤러")
    parser.add_argument("--keyword", default="건축설계", help="검색 키워드")
    parser.add_argument("--pages", type=int, default=1, help="검색 페이지 수")
    parser.add_argument("--page-size", type=int, default=MAX_PAGE_SIZE, help="페이지당 결과 건수")
    parser.add_argument("--output-dir", default="data", help="결과 저장 디렉터리")
    parser.add_argument("--checkpoint-path", default="data/checkpoint.json", help="체크포인트 파일 경로")
    parser.add_argument("--api-type", default="search", choices=["search", "best"], help="사용할 API 종류")
    parser.add_argument("--headed", action="store_true", help="Playwright 브라우저를 보이게 실행합니다.")

    args = parser.parse_args()

    api_key = os.getenv("DBPIA_API_KEY")
    if not api_key:
        parser.error("환경 변수 DBPIA_API_KEY가 설정되지 않았습니다.")

    output_dir = Path(args.output_dir)
    checkpoint_path = Path(args.checkpoint_path)
    downloaded_set = load_checkpoint(checkpoint_path)
    if downloaded_set:
        logger.info(f"체크포인트 로드: {len(downloaded_set)}개 이미 다운로드됨")
    pdf_dir = output_dir / "pdfs"
    meta_path = output_dir / "metadata.json"

    # 검색 및 메타데이터 저장
    papers = search_papers(api_key, args.keyword, args.pages, args.page_size, args.api_type)
    logger.info(f"총 {len(papers)}편 검색 결과")

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as fp:
        json.dump(papers, fp, ensure_ascii=False, indent=2)
    logger.info(f"메타데이터 저장: {meta_path}")

    # Playwright로 PDF 다운로드 실행
    if papers:
        download_pdfs_with_playwright(meta_path, pdf_dir, checkpoint_path, headless=not args.headed)


if __name__ == "__main__":
    main()
