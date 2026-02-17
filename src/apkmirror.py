import re
import logging
import time
import random
import cloudscraper
from bs4 import BeautifulSoup

APKMIRROR_BASE = "https://www.apkmirror.com"

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

def create_scraper_session(proxy_url=None):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
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

def get_download_link(version: str, app_name: str, config: dict, arch: str = None, scraper=None) -> str:
    if scraper is None:
        scraper = create_scraper_session()

    target_arch = (arch or config.get('arch', 'universal')).lower()
    dpi = config.get('dpi', 'nodpi').lower()
    version_dash = version.replace('.', '-').lower()
    release_name = config.get('release_prefix', config['name'])

    # ===================================================================
    # 1. LOAD THE EXACT RELEASE PAGE (the one you manually open)
    # ===================================================================
    exact_release_url = f"{APKMIRROR_BASE}/apk/{config['org']}/{config['name']}/{release_name}-{version_dash}-release/"
    logging.info(f"Trying exact release page: {exact_release_url}")
    time.sleep(2 + random.random())

    found_soup = None
    try:
        response = scraper.get(exact_release_url)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find('title').get_text().lower() if soup.find('title') else ""
            if version.lower() in title or version_dash in title:
                logging.info(f"✓ Loaded exact release page: {exact_release_url}")
                found_soup = soup
    except Exception as e:
        logging.warning(f"Exact page load failed: {e}")

    if not found_soup:
        logging.error(f"Could not load release page for {app_name} {version}")
        return None

    # ===================================================================
    # 2. GENERATE VARIANT DOWNLOAD PAGE URL (your suggestion - rock solid)
    # ===================================================================
    # Known variant numbers for YouTube Music (and most Google apps on APKMirror)
    variant_map = {
        "armeabi-v7a": "4",
        "arm64-v8a":   "3",
        "x86":         "5",
        "x86_64":      "6",
    }
    variant_id = variant_map.get(target_arch, "3")   # default to arm64-v8a

    variant_page_url = f"{exact_release_url.rstrip('/')}/{release_name}-{version_dash}-{variant_id}-android-apk-download/"
    logging.info(f"Generated variant page URL for {target_arch}: {variant_page_url}")

    # ===================================================================
    # 3. GO TO VARIANT PAGE → FINAL APK DOWNLOAD BUTTON
    # ===================================================================
    try:
        time.sleep(2 + random.random())
        response = scraper.get(variant_page_url)
        response.encoding = 'utf-8'
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        # Current APKMirror button (forcebaseapk or downloadButton)
        btn = soup.find('a', href=lambda h: h and 'forcebaseapk=true' in h) or \
              soup.find('a', class_='downloadButton')
        
        if btn:
            final_url = APKMIRROR_BASE + btn['href']
            logging.info(f"Final APK download URL: {final_url}")
            return final_url
    except Exception as e:
        logging.error(f"Variant download flow failed: {e}")

    # Last resort fallback (full link scan)
    logging.warning("Generated variant failed - trying full link scan as backup")
    for a in found_soup.find_all('a', href=True):
        href = a['href'].lower()
        if version_dash in href and target_arch in href and 'apk-download' in href:
            variant_page_url = APKMIRROR_BASE + a['href']
            logging.info(f"Backup variant link found: {variant_page_url}")
            # repeat the download flow above...
            break

    return None

def get_architecture_criteria(arch: str) -> dict:
    return {"arm64-v8a": "arm64-v8a", "armeabi-v7a": "armeabi-v7a", "universal": "universal"}.get(arch, "universal")

def get_latest_version(app_name: str, config: dict, scraper=None) -> str:
    if scraper is None:
        scraper = create_scraper_session()
    url = f"{APKMIRROR_BASE}/uploads/?appcategory={config['name']}"
    time.sleep(2 + random.random())
    response = scraper.get(url)
    response.encoding = 'utf-8'
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for row in soup.find_all("div", class_="appRow"):
        txt = row.find("h5", class_="appRowTitle").a.text.strip()
        if "alpha" not in txt.lower() and "beta" not in txt.lower():
            m = re.search(r'\d+(\.\d+)+', txt)
            if m:
                return m.group()
    return None
