import time
import re
import json
import urllib.parse
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import requests
from googleapiclient.discovery import build
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException, ElementClickInterceptedException
)

api_key = ""
cse_id = "a595ae02b0cab45d2"

SOCIAL_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
    "youtube.com", "tiktok.com", "snapchat.com", "whatsapp.com", "gmail.com"
}
NON_SOCIAL_TLDS = ['.com', '.org', '.net', '.edu', '.ai', '.co', '.io', '.me', '.store', '.biz', '.gh', '.com.gh']
SHORT_DOMAINS = {"bit.ly", "bitly.com", "tinyurl.com", "goo.gl", "t.co", "linktr.ee"}

_google_service = None  # Cache for Google API client

def get_google_service():
    global _google_service
    if _google_service is None:
        _google_service = build("customsearch", "v1", developerKey=api_key)
    return _google_service

def safe_click(driver, element, max_retries=3, delay=1):
    """Attempts to safely click an element with retries and scrolling."""
    for attempt in range(max_retries):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(delay)
            element.click()
            return True
        except (StaleElementReferenceException, ElementClickInterceptedException) as e:
            print(f"⚠️ Click attempt {attempt+1} failed: {e}")
            time.sleep(1)
    return False

def save_unique_businesses(businesses, output_file="businesses.json"):
    """Saves unique businesses to JSON, skipping duplicates."""
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    existing_names = {biz["name"] for biz in existing}
    new_entries = [biz for biz in businesses if biz["name"] not in existing_names]

    if new_entries:
        print(f"💾 Saving {len(new_entries)} new businesses...")
        existing.extend(new_entries)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=4, ensure_ascii=False)
    else:
        print("📭 No new businesses found to save.")

def extract_businesses(driver, max_results=3, output_file="businesses.json", live_callback=None, stop_flag_func=None):
    """Extracts business information from Google Maps results."""
    businesses = []
    seen_names = set()
    scroll_attempts = 0
    max_scroll_attempts = 2

    while len(businesses) < max_results and scroll_attempts < max_scroll_attempts:
        print(f"📦 Collecting business cards ({len(businesses)}/{max_results})...")

        cards = driver.find_elements(By.CLASS_NAME, "Nv2PK")
        new_found = False

        for i, card in enumerate(cards):
            try:
                link = card.find_element(By.CLASS_NAME, "hfpxzc")
                name = link.get_attribute("aria-label").strip()

                if not name or name in seen_names:
                    continue

                seen_names.add(name)
                new_found = True

                if not safe_click(driver, link):
                    print(f"❌ Could not click on {name}")
                    continue

                details_text = get_panel_details_text(driver)
                if details_text is None:
                    continue

                business = {
                    "name": name,
                    "details": details_text
                }

                cleaned_data = extract_business_info([business])

                if stop_flag_func and stop_flag_func():
                    break

                if live_callback:
                    for biz in cleaned_data:
                        live_callback(biz)

                print(f"✅ Collected: {name}\n")
                businesses.extend(cleaned_data)

                if len(businesses) >= max_results:
                    break

            except (StaleElementReferenceException, TimeoutException, ElementClickInterceptedException) as e:
                print(f"⛔ Skipped card due to error: {e}")
                continue

        if not new_found:
            scroll_attempts += 1
        else:
            scroll_attempts = 0

        try:
            scroll_area = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="main"]//div[contains(@aria-label, "Results")]'))
            )
            driver.execute_script("arguments[0].scrollBy(0, 1500)", scroll_area)
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Scroll failed: {e}")
            break

    save_unique_businesses(businesses, output_file)
    print(f"\n🎉 Done! Saved {len(businesses)} businesses to {output_file}")
    return businesses

def get_panel_details_text(driver) -> Optional[List[str]]:
    """Extracts visible details text from the business side panel."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.WNBkOb.XiKgde[role="main"]'))
        )
        time.sleep(3)
        panel_elements = driver.find_elements(By.CSS_SELECTOR, 'div.m6QErb.XiKgde[role="region"]')
        time.sleep(3)
        if len(panel_elements) < 2:
            raise Exception("Panel element not found or structure changed.")

        panel_html = panel_elements[1].get_attribute("innerHTML")
        time.sleep(2)
        soup = BeautifulSoup(panel_html, "html.parser")

        text_classes = [
            "fontBodyMedium", "fontBodySmall", "HlvSq", "UsdlK", "rogA2c"
        ]
        seen_texts = set()
        extracted_texts = []

        for class_name in text_classes:
            for div in soup.find_all("div", class_=class_name):
                text = div.get_text(separator=' ', strip=True)
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    extracted_texts.append(text)

        for span in soup.find_all("span"):
            text = span.get_text(strip=True)
            if text and text not in seen_texts:
                seen_texts.add(text)
                extracted_texts.append(text)

        return extracted_texts if extracted_texts else ["N/A"]
    except Exception as e:
        print(f"❌ Error extracting panel details: {e}")
        return ["N/A"]

def extract_business_info(business_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extracts structured info (phone, email, address, website, socials) from business details."""
    def extract_phones(texts):
        phones = []
        phone_regex = re.compile(r'(\+233|0)[235][0-9][ -]?\d{3}[ -]?\d{4}|\+?\d{10,15}')
        for text in texts:
            found = phone_regex.findall(text)
            if found:
                phones.extend([f[0] if isinstance(f, tuple) else f for f in found])
        return list(set(phones))

    def extract_emails(texts):
        emails = []
        email_regex = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
        for text in texts:
            found = email_regex.findall(text)
            if found:
                emails.extend(found)
        return list(set(emails))

    def extract_websites(texts):
        urls = []
        url_regex = re.compile(
            r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(?:com|org|net|gh|co|io|ai|me|store|biz|edu)(/[^\s]*)?)"
        )
        for text in texts:
            found = url_regex.findall(text)
            for url in found:
                url = url[0] if isinstance(url, tuple) else url
                if not is_social_media_link(url) and is_non_social_website(url):
                    urls.append(url if url.startswith("http") else "https://" + url)
        return list(set(urls))

    def extract_address(texts):
        for text in texts:
            if re.search(r'\b(Street|St|Ave|Rd|Junction|Accra|Tema|Kumasi|Plot|No\.|Close|Crescent)\b', text, re.I) or \
               re.search(r'[A-Z0-9]{4,}\+[A-Z0-9]{2,}', text):
                return text
        return None

    cleaned_data = []
    for biz in business_list:
        name = biz.get("name", "")
        details = biz.get("details", [])

        phones = extract_phones(details)
        emails = extract_emails(details)
        websites = extract_websites(details)
        address = extract_address(details)

        socials = search_social_media_links(name)

        cleaned_data.append({
            "name": name,
            "address": address or "N/A",
            "phone": phones[0] if phones else "N/A",
            "email": emails[0] if emails else "N/A",
            "website": websites[0] if websites else "N/A",
            "social_links": socials or {},
        })

    return cleaned_data

def is_social_media_link(text: str) -> bool:
    if not text or not isinstance(text, str):
        return False
    return any(domain in text.lower() for domain in SOCIAL_DOMAINS)

def is_non_social_website(text: str) -> bool:
    if not text or not isinstance(text, str):
        return False
    if ' ' in text or is_social_media_link(text):
        return False
    return any(tld in text.lower() for tld in NON_SOCIAL_TLDS)

def has_non_social_website(texts: List[str]) -> bool:
    if not isinstance(texts, list):
        return False
    for text in texts:
        if is_non_social_website(text):
            return True
    return False

def search_social_media_links(business_name: str, max_results: int = 4) -> Dict[str, str]:
    """
    Searches for a business's social media links using Google Custom Search API.
    Returns a dict with one link per platform (Facebook, Instagram, Twitter/X, LinkedIn).
    """
    social_domains = {
        "facebook": "facebook.com",
        "instagram": "instagram.com",
        "twitter": ["x.com", "twitter.com"],
        "linkedin": "linkedin.com",
        "youtube": "youtube.com",
        "tiktok": "tiktok.com"
    }
    query = f"{business_name} site:facebook.com OR site:instagram.com OR site:twitter.com OR site:linkedin.com OR site:youtube.com OR site:tiktok.com"
    try:
        service = get_google_service()
        res = service.cse().list(q=query, cx=cse_id, num=8).execute()
        social_links = {}
        if 'items' in res:
            for item in res['items']:
                link = item.get('link', '').lower()
                for platform, domain in social_domains.items():
                    if isinstance(domain, list):
                        match = any(d in link for d in domain)
                    else:
                        match = domain in link
                    if match and platform not in social_links:
                        social_links[platform] = link
                if len(social_links) >= max_results:
                    break
        return social_links
    except Exception as e:
        print(f"❌ Error searching social media for '{business_name}': {e}")
        return {}