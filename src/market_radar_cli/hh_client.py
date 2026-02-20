"""HeadHunter API client for fetching vacancies."""

import csv
import logging
import re
import time
from datetime import date
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HH_API_BASE = "https://api.hh.ru"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HH API client)"
}
MAX_RETRIES = 3
RETRY_DELAY = 1.0


class HHAPIError(Exception):
    """Exception raised for HH API errors."""
    pass


def fetch_vacancies_list(query: str, area: int, page: int, per_page: int) -> dict[str, Any]:
    """
    Fetch vacancies list from HH API.
    
    GET /vacancies with search parameters.
    
    Args:
        query: Search query text
        area: Area ID (113 for Russia)
        page: Page number (0-indexed)
        per_page: Items per page (max 100)
    
    Returns:
        JSON response with 'items' and 'pages' info
    """
    url = f"{HH_API_BASE}/vacancies"
    params = {
        "text": query,
        "area": area,
        "search_field": "name",
        "page": page,
        "per_page": per_page
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise HHAPIError(f"Failed to fetch vacancies list after {MAX_RETRIES} attempts: {e}")
            logger.warning(f"Request failed (attempt {attempt + 1}): {e}, retrying...")
            time.sleep(RETRY_DELAY * (attempt + 1))
    
    raise HHAPIError("Unexpected error in fetch_vacancies_list")


def fetch_vacancy_detail(vacancy_id: str) -> dict[str, Any]:
    """
    Fetch detailed vacancy information.
    
    GET /vacancies/{id}
    
    Args:
        vacancy_id: Vacancy ID
    
    Returns:
        Full vacancy object with name and description
    """
    url = f"{HH_API_BASE}/vacancies/{vacancy_id}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise HHAPIError(f"Failed to fetch vacancy {vacancy_id}: {e}")
            logger.warning(f"Request failed for vacancy {vacancy_id} (attempt {attempt + 1}): {e}, retrying...")
            time.sleep(RETRY_DELAY * (attempt + 1))
    
    raise HHAPIError("Unexpected error in fetch_vacancy_detail")


def clean_html(html_text: str | None) -> str:
    """
    Strip HTML tags from vacancy description.
    
    Args:
        html_text: HTML formatted text or None
    
    Returns:
        Plain text with newlines normalized
    """
    if not html_text:
        return ""
    
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Replace <br> and <p> with newlines
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.replace_with(f"\n{p.get_text()}\n")
    
    text = soup.get_text()
    
    # Normalize whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()
    
    return text


def fetch_all_vacancies(query: str, area: int, limit: int) -> list[dict[str, str]]:
    """
    Fetch vacancies with pagination up to the specified limit.
    
    Args:
        query: Search query text
        area: Area ID
        limit: Maximum number of vacancies to fetch
    
    Returns:
        List of vacancy dicts with id, title, description
    """
    vacancies = []
    page = 0
    per_page = min(limit, 100)  # HH API max per_page is 100
    
    logger.info(f"Starting to fetch {limit} vacancies for query: '{query}'")
    
    while len(vacancies) < limit:
        data = fetch_vacancies_list(query, area, page, per_page)
        items = data.get("items", [])
        
        if not items:
            logger.info("No more vacancies available")
            break
        
        for item in items:
            if len(vacancies) >= limit:
                break
            
            vacancy_id = item.get("id")
            if not vacancy_id:
                continue
            
            try:
                detail = fetch_vacancy_detail(vacancy_id)
                vacancy = {
                    "id": vacancy_id,
                    "title": detail.get("name", ""),
                    "description": clean_html(detail.get("description"))
                }
                vacancies.append(vacancy)
                logger.info(f"Fetched {len(vacancies)}/{limit} vacancies")
            except HHAPIError as e:
                logger.warning(f"Skipping vacancy {vacancy_id}: {e}")
        
        # Check if there are more pages
        # HH API returns 'pages' as integer (total pages count)
        total_pages = data.get("pages", 1)
        if isinstance(total_pages, dict):
            total_pages = total_pages.get("pages", 1)
        if page + 1 >= total_pages:
            break
        
        page += 1
        time.sleep(0.5)  # Rate limiting
    
    logger.info(f"Successfully fetched {len(vacancies)} vacancies")
    return vacancies


def save_to_csv(vacancies: list[dict[str, str]], query: str) -> str:
    """
    Save vacancies to CSV file.
    
    Args:
        vacancies: List of vacancy dicts
        query: Search query (for filename)
    
    Returns:
        Path to created CSV file
    """
    # Create slug from query for filename
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    date_str = date.today().isoformat()
    filename = f"vacancies_{date_str}_{slug}.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "description"], quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(vacancies)
    
    logger.info(f"Saved {len(vacancies)} vacancies to {filename}")
    return filename
