import os
import json
import re
import requests
from urllib.parse import urlparse

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'pdfs')
PDF_PATTERN = re.compile(r"https?://[^\s\"']+\.pdf", re.IGNORECASE)


def find_json_files(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json'):
                yield os.path.join(root, file)

def extract_pdf_links_from_json(json_path):
    links = set()
    try:
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
        # Only extract lang_to_source_url['si'] if present and is a PDF link
        if isinstance(data, dict):
            lang_urls = data.get('lang_to_source_url', {})
            if isinstance(lang_urls, dict):
                si_url = lang_urls.get('si')
                if isinstance(si_url, str) and PDF_PATTERN.match(si_url):
                    links.add(si_url)
    except Exception as e:
        print(f'Error reading {json_path}: {e}')
    return links

def download_pdf(url, output_dir):
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    out_path = os.path.join(output_dir, filename)
    if os.path.exists(out_path):
        print(f'Skipping {filename}, already exists.')
        return True
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f'Downloading {url}... (Attempt {attempt})')
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            with open(out_path, 'wb') as f:
                f.write(r.content)
            return True
        except Exception as e:
            print(f'Failed to download {url} (Attempt {attempt}): {e}')
            if attempt == max_retries:
                print(f'Giving up on {url} after {max_retries} attempts.')
                return False
    return False

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_links = set()
    for json_file in find_json_files(DATA_DIR):
        links = extract_pdf_links_from_json(json_file)
        all_links.update(links)
    print(f'Found {len(all_links)} unique PDF links.')
    for url in sorted(all_links):
        download_pdf(url, OUTPUT_DIR)

if __name__ == '__main__':
    main()
