import re
import logging
import time
import random
import cloudscraper
from bs4 import BeautifulSoup

# Base URL for APKMirror
APKMIRROR_BASE = "https://www.apkmirror.com"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def create_scraper_session(proxy_url=None):
    """Create a cloudscraper session with browser-like headers and optional proxy."""
    scraper = cloudscraper.create_scraper()
    scraper.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.apkmirror.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    })
    if proxy_url:
        scraper.proxies = {"http": proxy_url, "https": proxy_url}
    return scraper

def map_architecture(arch_name):
    """Map architecture names to APKMirror-compatible strings."""
    mapping = {
        "arm64-v8a": "arm64-v8a",
        "armeabi-v7a": "armeabi-v7a",
        "universal": "universal"
    }
    return mapping.get(arch_name, "universal")

def fetch_latest_version(app_config, scraper=None):
    """Retrieve the latest stable version for the app, skipping alphas/betas."""
    if scraper is None:
        scraper = create_scraper_session()
    
    # Primary method: Main app page
    try:
        main_page_url = f"{APKMIRROR_BASE}/apk/{app_config['organization']}/{app_config['app_slug']}/"
        time.sleep(1 + random.random())
        response = scraper.get(main_page_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            version_span = soup.find("span", string=re.compile(r"\d+\.\d+"))
            if version_span:
                version_text = version_span.text.strip()
                version_match = re.search(r"(\d+(\.\d+)+)", version_text)
                if version_match:
                    return version_match.group(1)
    except Exception as e:
        logging.warning(f"Main page fetch failed: {e}")
    
    # Fallback: Uploads page
    uploads_url = f"{APKMIRROR_BASE}/uploads/?appcategory={app_config['app_slug']}"
    time.sleep(1 + random.random())
    response = scraper.get(uploads_url)
    if response.status_code != 200:
        logging.error(f"Uploads page returned {response.status_code}")
        return None
    
    logging.info(f"Fetched uploads page: {len(response.content)} bytes")
    soup = BeautifulSoup(response.content, "html.parser")
    app_entries = soup.find_all("div", class_="appRow")
    version_regex = re.compile(r"\d+(\.\d+)*(-[a-zA-Z0-9]+(\.\d+)*)*")
    
    for entry in app_entries:
        title_text = entry.find("h5", class_="appRowTitle").a.text.strip().lower()
        if "alpha" not in title_text and "beta" not in title_text:
            match = version_regex.search(title_text)
            if match:
                full_version = match.group()
                parts = full_version.split(".")
                base_parts = [part for part in parts if part.isdigit()]
                if base_parts:
                    return ".".join(base_parts)
    
    logging.error("No stable version found")
    return None

def fetch_apk_download_url(app_version, app_config, target_arch=None, scraper=None):
    """Fetch the direct download URL for the specified app version and architecture."""
    if scraper is None:
        scraper = create_scraper_session()
    
    arch = map_architecture(target_arch or app_config.get("arch", "universal"))
    match_criteria = [app_config.get("variant_type", "release"), arch, app_config.get("dpi_setting", "nodpi")]
    
    # Prepare version parts for URL building
    version_components = app_version.split(".")
    parsed_soup = None
    exact_match_found = False
    release_name = app_config.get("release_prefix", app_config["app_slug"])
    
    # Backward loop through version granularity
    for granularity in range(len(version_components), 0, -1):
        curr_version_str = "-".join(version_components[:granularity])
        
        # Generate unique URL candidates
        url_candidates = list(dict.fromkeys([
            f"{APKMIRROR_BASE}/apk/{app_config['organization']}/{app_config['app_slug']}/{release_name}-{curr_version_str}-release/",
            f"{APKMIRROR_BASE}/apk/{app_config['organization']}/{app_config['app_slug']}/{app_config['app_slug']}-{curr_version_str}-release/" if release_name != app_config["app_slug"] else None,
            f"{APKMIRROR_BASE}/apk/{app_config['organization']}/{app_config['app_slug']}/{release_name}-{curr_version_str}/",
            f"{APKMIRROR_BASE}/apk/{app_config['organization']}/{app_config['app_slug']}/{app_config['app_slug']}-{curr_version_str}/" if release_name != app_config["app_slug"] else None
        ]))
        url_candidates = [url for url in url_candidates if url]  # Remove None
        
        for candidate_url in url_candidates:
            logging.info(f"Checking URL: {candidate_url}")
            time.sleep(1 + random.random())
            
            try:
                response = scraper.get(candidate_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    page_content = soup.get_text()
                    
                    # Version format checks
                    version_formats = [
                        app_version,
                        app_version.replace(".", "-"),
                        curr_version_str,
                        ".".join(version_components[:granularity])
                    ]
                    
                    title = soup.find("title").get_text() if soup.find("title") else ""
                    headings = [h.get_text() for h in soup.find_all(["h1", "h2", "h3"])]
                    
                    # Flexible match across sources
                    is_valid_page = any(
                        any(fmt in source for fmt in [f for f in version_formats if f])
                        for source in [page_content, title] + headings
                    )
                    
                    if is_valid_page:
                        logging.info(f"Valid page found: {response.url}")
                        parsed_soup = soup
                        exact_match_found = True
                        break
                    else:
                        logging.warning(f"Page exists but version mismatch: {candidate_url}")
                        if parsed_soup is None:
                            parsed_soup = soup  # Fallback
                elif response.status_code == 404:
                    continue
                else:
                    logging.warning(f"Status {response.status_code} for {candidate_url}")
            except Exception as e:
                logging.warning(f"Error accessing {candidate_url}: {str(e)[:50]}")
        
        if exact_match_found:
            break
    
    if not parsed_soup:
        logging.error(f"No release page found for {app_config['app_slug']} {app_version}")
        return None
    
    if not exact_match_found and parsed_soup:
        logging.warning(f"Using fallback page for {app_config['app_slug']} {app_version}")
    
    # Parse variants
    variant_rows = parsed_soup.find_all("div", class_="table-row")[1:]  # Exclude header
    variant_url = None
    
    # Exact version priority
    for row in variant_rows:
        row_content = row.get_text()
        if app_version in row_content or app_version.replace(".", "-") in row_content:
            if all(crit in row_content for crit in match_criteria):
                link_elem = row.find("a", class_="accent_color")
                if link_elem:
                    variant_url = APKMIRROR_BASE + link_elem["href"]
                    break
    
    # Criteria fallback if no exact
    if not variant_url:
        for row in variant_rows:
            row_content = row.get_text()
            if all(crit in row_content for crit in match_criteria) and re.search(r"\d+(\.\d+)+", row_content):
                link_elem = row.find("a", class_="accent_color")
                if link_elem:
                    variant_url = APKMIRROR_BASE + link_elem["href"]
                    match = re.search(r"(\d+(\.\d+)+(\.\w+)*)", row_content)
                    if match:
                        logging.warning(f"Falling back to variant {match.group(1)}")
                    break
    
    if not variant_url:
        logging.error(f"No matching variant for criteria {match_criteria}")
        logging.debug(f"Total rows: {len(variant_rows)}")
        for i, row in enumerate(variant_rows[:5]):
            logging.debug(f"Row {i}: {row.get_text()[:100]}...")
        return None
    
    # Navigate to download
    try:
        time.sleep(1 + random.random())
        response = scraper.get(variant_url)
        response.raise_for_status()
        logging.info(f"Variant page fetched: {len(response.content)} bytes")
        soup = BeautifulSoup(response.content, "html.parser")
        download_btn = soup.find("a", class_="downloadButton")
        if download_btn:
            intermediate_url = APKMIRROR_BASE + download_btn["href"]
            time.sleep(1 + random.random())
            response = scraper.get(intermediate_url)
            response.raise_for_status()
            logging.info(f"Download page fetched: {len(response.content)} bytes")
            soup = BeautifulSoup(response.content, "html.parser")
            final_btn = soup.find("a", id="download-link") or soup.find("a", href=lambda h: h and "download/" in h and "forcebaseapk" in h)
            if final_btn:
                return APKMIRROR_BASE + final_btn["href"]
    except Exception as e:
        logging.error(f"Download navigation failed: {e}")
    
    return None
