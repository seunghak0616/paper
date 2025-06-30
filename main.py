from __future__ import annotations

import typer
import uvicorn

from app.models import create_db_and_tables
from crawler.dbpia_crawler import main as crawl_main
from scripts.add_hnsw_index import main as add_index_main

app = typer.Typer(help="Papers 프로젝트 CLI")


@app.command(name="server", help="FastAPI 서버를 실행합니다.")
def run_server(
    host: str = typer.Option("0.0.0.0", help="Host 주소"),
    port: int = typer.Option(8000, help="Port 번호"),
    reload: bool = typer.Option(False, help="코드 변경 시 자동 재시작"),
):
    """
    DB 초기화 후 Uvicorn으로 FastAPI 서버를 실행합니다.
    """
    typer.echo("🚀 데이터베이스를 초기화합니다...")
    try:
        create_db_and_tables()
        typer.secho("✅ 데이터베이스 초기화 완료.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"🔥 데이터베이스 초기화 실패: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"🌍 FastAPI 서버를 http://{host}:{port} 에서 시작합니다.")
    uvicorn.run("app.server:app", host=host, port=port, reload=reload)


@app.command(name="crawl", help="DBpia 크롤러를 실행합니다.")
def run_crawler():
    """
    논문 데이터 수집을 위해 크롤러를 실행합니다.
    """
    typer.echo("🤖 DBpia 크롤러를 시작합니다...")
    try:
        crawl_main()
        typer.secho("✅ 크롤링 완료.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"🔥 크롤링 중 오류 발생: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command(name="init-db", help="데이터베이스 테이블을 초기화합니다.")
def init_db():
    """
    데이터베이스 연결을 확인하고 모든 테이블을 생성합니다.
    """
    typer.echo("🚀 데이터베이스를 초기화합니다...")
    try:
        create_db_and_tables()
        typer.secho("✅ 데이터베이스 초기화 완료.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"🔥 데이터베이스 초기화 실패: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command(name="add-index", help="벡터 검색을 위한 HNSW 인덱스를 생성합니다.")
def add_hnsw_index():
    """
    paper_chunks 테이블에 HNSW 인덱스를 추가하여 검색 속도를 향상시킵니다.
    """
    typer.echo("🚀 HNSW 인덱스를 생성합니다...")
    try:
        add_index_main()
        typer.secho("✅ HNSW 인덱스 생성 완료.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"🔥 인덱스 생성 실패: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
