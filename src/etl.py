import os
import json
import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import pymupdf4llm
from io import StringIO
from .config import SEC_HEADERS, get_api_key

def clean_sec_html(html_content):
    """
    Parses SEC HTML, converts tables to Markdown using Pandas,
    and cleans the rest of the text.
    """
    print("   🧹 Cleaning SEC HTML with Pandas Table Extraction...")
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Remove XBRL and junk tags
    for tag in soup(['script', 'style', 'ix:header', 'xml', 'head', 'object']):
        tag.decompose()

    # 2. INTELLIGENT TABLE PARSING
    tables = soup.find_all('table')

    for table in tables:
        try:
            # Wrap in StringIO to avoid Pandas depreciation warning
            dfs = pd.read_html(StringIO(str(table)))
            if not dfs: continue

            df = dfs[0]

            # Drop empty spacer rows/cols
            df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')

            # Convert to Markdown Pipe Table
            # (Requires 'tabulate' installed)
            md_table = df.to_markdown(index=False)

            # Swap HTML table with Markdown Table
            new_node = soup.new_tag("p")
            new_node.string = f"\n\n{md_table}\n\n"
            table.replace_with(new_node)

        except Exception:
            # Fallback: leave table for markdownify
            continue

    # 3. Final Text Pass
    return md(str(soup), heading_style="ATX", strip=['a', 'img'])

def download_from_sec(ticker):
    print(f"\n🏛️  Checking SEC Database for {ticker}...")

    try:
        # 1. Get CIK
        r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS, timeout=10)
        data = r.json()
        cik = next((str(v['cik_str']).zfill(10) for v in data.values() if v['ticker'] == ticker), None)

        if not cik:
            print("   ❌ CIK not found.")
            return None

        # 2. Get Recent Filings
        r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=SEC_HEADERS, timeout=10)
        filings = r.json()['filings']['recent']

        doc_url = None
        for i, form in enumerate(filings['form']):
            # Prioritize 10-K, then 20-F (foreign issuers)
            if form in ['10-K', '20-F']:
                accession = filings['accessionNumber'][i].replace("-", "")
                primary_doc = filings['primaryDocument'][i]
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}"
                break

        if not doc_url:
            print("   ❌ No recent 10-K/20-F found.")
            return None

        print(f"   🔗 Found SEC Source: {doc_url}")

        # 3. Download
        r = requests.get(doc_url, headers=SEC_HEADERS, stream=True, timeout=20)
        if r.status_code == 200:
            if not os.path.exists("downloads"): os.makedirs("downloads")

            if doc_url.lower().endswith('.pdf'):
                print("   ⚠️  SEC file is PDF. Converting...")
                temp_pdf = f"downloads/{ticker}_temp.pdf"
                with open(temp_pdf, 'wb') as f: f.write(r.content)
                md_text = pymupdf4llm.to_markdown(temp_pdf)
                os.remove(temp_pdf)
            else:
                md_text = clean_sec_html(r.content)

            filename = f"downloads/{ticker}_10k.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(md_text)
            print(f"   ✅ SEC Conversion complete: {filename}")
            return filename

    except Exception as e:
        print(f"   ❌ SEC Error: {e}")
        return None
    return None

def download_from_google(ticker):
    print(f"\n🌍 SEC failed. Starting Web Search fallback for {ticker}...")

    # Quick helper to get name
    try:
        name = yf.Ticker(ticker).info.get('shortName', ticker)
    except:
        name = ticker

    api_key = get_api_key("SERPER_API_KEY")
    if not api_key:
        print("   ❌ No SERPER_API_KEY. Cannot fallback.")
        return None

    queries = [
        f"{name} ({ticker}) annual report 2024 filetype:pdf",
        f"{name} investor relations annual report 2024 pdf"
    ]

    pdf_url = None
    for q in queries:
        try:
            payload = json.dumps({"q": q, "num": 5})
            headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
            resp = requests.post("https://google.serper.dev/search", headers=headers, data=payload)
            results = resp.json().get('organic', [])

            for r in results:
                if r.get('link', '').lower().endswith('.pdf'):
                    pdf_url = r['link']
                    break
            if pdf_url: break
        except:
            continue

    if not pdf_url:
        print("   ❌ No PDF found via Google.")
        return None

    print(f"   🔗 Found Web PDF: {pdf_url}")

    try:
        temp_pdf = f"downloads/{ticker}_temp_web.pdf"
        if not os.path.exists("downloads"): os.makedirs("downloads")

        # Pretend to be a browser
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
        with open(temp_pdf, 'wb') as f:
            f.write(r.content)

        print("   ✨ Converting Web PDF to Markdown...")
        md_text = pymupdf4llm.to_markdown(temp_pdf)

        final_md = f"downloads/{ticker}_10k.md"
        with open(final_md, "w", encoding="utf-8") as f:
            f.write(md_text)

        os.remove(temp_pdf)
        print(f"   ✅ Web Conversion complete: {final_md}")
        return final_md

    except Exception as e:
        print(f"   ❌ Web Conversion Error: {e}")
        return None
