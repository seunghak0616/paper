import asyncio
import os

import psycopg2
from dotenv import load_dotenv
from playwright.async_api import async_playwright


async def main():
    """
    Connects to the database, fetches the source_url for a given document ID,
    navigates to the URL, and saves the page as a PDF.
    """
    load_dotenv()

    # --- Database Connection ---
    db_name = "archidb"
    db_user = "archidb_user"
    db_pass = "archidb_password"
    db_host = "localhost"
    db_port = "5432"

    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()

    # --- Fetch URL from DB ---
    document_id = 1
    cursor.execute("SELECT title, source_url FROM documents WHERE id = %s;", (document_id,))
    result = cursor.fetchone()
    if not result:
        print(f"No document found with ID: {document_id}")
        return

    title, source_url = result
    print(f"Found document: '{title}'")
    print(f"Source URL: {source_url}")

    # Sanitize title for use as a filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    pdf_filename = f"{safe_title}.pdf"
    output_path = os.path.join("data", pdf_filename)

    # --- Crawl and Save PDF ---
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            print(f"Navigating to {source_url}...")
            await page.goto(source_url, wait_until="networkidle")

            # Handle potential cookie banners before printing
            await asyncio.sleep(2) # Give page time to load dynamic elements

            print(f"Saving page to '{output_path}'...")
            await page.pdf(path=output_path, format="A4", print_background=True)
            print("Successfully created PDF.")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await browser.close()
            cursor.close()
            conn.close()

if __name__ == "__main__":
    # Ensure data directory exists
    if not os.path.exists("data"):
        os.makedirs("data")

    asyncio.run(main())
