#!/usr/bin/env python3
"""
Test script for LxHentai API functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only the API class from our main file
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json

class LxHentaiAPI:
    """API client for LxHentai manga website"""
    
    def __init__(self, base_url="https://lxmanga.help"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': base_url
        })
        
        self.sort_options = [
            ("Mới cập nhật", "-updated_at"),
            ("Mới nhất", "-created_at"),
            ("Cũ nhất", "created_at"),
            ("Xem nhiều", "-views"),
            ("A-Z", "name"),
            ("Z-A", "-name")
        ]
    
    def search_manga(self, page=1, query="", sort_by="-views", status="1,2"):
        """Search for manga with filters"""
        params = {
            'page': str(page),
            'sort': sort_by,
            'filter[status]': status
        }
        
        if query:
            params['filter[name]'] = query
        
        url = f"{self.base_url}/tim-kiem"
        try:
            print(f"Requesting: {url}")
            print(f"Params: {params}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return self._parse_manga_list(response.text)
        except Exception as e:
            print(f"Error searching manga: {e}")
            return []
    
    def _parse_manga_list(self, html):
        """Parse manga list from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        manga_list = []
        
        # Debug: Check if we got HTML
        if not html or len(html) < 100:
            print("Warning: HTML response is too short or empty")
            return []
        
        # Try to find manga items
        items = soup.select("div.grid div.manga-vertical")
        print(f"Found {len(items)} manga items")
        
        if len(items) == 0:
            # Debug: Print what we actually got
            print("No manga items found. Checking page structure...")
            # Try alternative selectors
            items = soup.select("div.manga-item, div.comic-item, article.manga")
            print(f"Alternative selector found {len(items)} items")
        
        for item in items[:5]:  # Limit to 5 for testing
            try:
                link_elem = item.select_one("a[href*='/truyen/']")
                if not link_elem:
                    link_elem = item.select_one("div.p-2.truncate a")
                if not link_elem:
                    link_elem = item.select_one("a")
                    
                if not link_elem:
                    continue
                    
                manga = {
                    'url': link_elem.get('href', ''),
                    'title': link_elem.text.strip() or link_elem.get('title', ''),
                    'thumbnail': ''
                }
                
                # Extract thumbnail URL
                cover_elem = item.select_one("div.cover, img.cover, img")
                if cover_elem:
                    # Try different attributes
                    for attr in ['data-bg', 'data-src', 'src']:
                        if cover_elem.get(attr):
                            manga['thumbnail'] = urljoin(self.base_url, cover_elem[attr])
                            break
                
                if manga['title']:
                    manga_list.append(manga)
                    print(f"Found manga: {manga['title'][:50]}...")
            except Exception as e:
                print(f"Error parsing manga item: {e}")
                continue
        
        return manga_list
    
    def get_manga_details(self, manga_url):
        """Get detailed information about a manga"""
        full_url = urljoin(self.base_url, manga_url)
        try:
            print(f"Getting details from: {full_url}")
            response = self.session.get(full_url, timeout=10)
            response.raise_for_status()
            return self._parse_manga_details(response.text, full_url)
        except Exception as e:
            print(f"Error getting manga details: {e}")
            return None
    
    def _parse_manga_details(self, html, url):
        """Parse manga details from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        details = {'url': url}
        
        # Try multiple selectors for title
        title_selectors = [
            "div.mb-4 span",
            "h1.manga-title",
            "h1",
            "div.title"
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                details['title'] = title_elem.text.strip()
                print(f"Found title: {details['title']}")
                break
        
        # Try to find chapters
        chapter_selectors = [
            "ul.overflow-y-auto.overflow-x-hidden > a",
            "div.chapter-list a",
            "a[href*='/chuong/']",
            "a[href*='/chapter/']"
        ]
        
        chapters = []
        for selector in chapter_selectors:
            chapter_elems = soup.select(selector)
            if chapter_elems:
                print(f"Found {len(chapter_elems)} chapters with selector: {selector}")
                for elem in chapter_elems[:3]:  # Show first 3
                    chapters.append(elem.get('href', ''))
                break
        
        details['chapter_count'] = len(chapters)
        
        return details
    
    def get_chapter_images(self, chapter_url):
        """Get image URLs for a chapter"""
        full_url = urljoin(self.base_url, chapter_url)
        try:
            print(f"Getting images from: {full_url}")
            response = self.session.get(full_url, timeout=10)
            response.raise_for_status()
            return self._parse_chapter_images(response.text)
        except Exception as e:
            print(f"Error getting chapter images: {e}")
            return []
    
    def _parse_chapter_images(self, html):
        """Parse image URLs from chapter HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        
        # Try multiple selectors for images
        image_selectors = [
            "div.text-center div.lazy",
            "div.reading-content img",
            "img.page-img",
            "div.page-chapter img"
        ]
        
        for selector in image_selectors:
            img_elems = soup.select(selector)
            if img_elems:
                print(f"Found {len(img_elems)} images with selector: {selector}")
                for img_elem in img_elems[:3]:  # Show first 3
                    # Try different attributes
                    for attr in ['data-src', 'data-original', 'src']:
                        img_url = img_elem.get(attr, '')
                        if img_url and (img_url.startswith('http') or img_url.startswith('/')):
                            images.append(urljoin(self.base_url, img_url))
                            break
                break
        
        return images


def test_api():
    """Test the API functionality"""
    print("=" * 60)
    print("Testing LxHentai API")
    print("=" * 60)
    
    api = LxHentaiAPI()
    
    # Test 1: Search for popular manga
    print("\n1. Testing popular manga search...")
    print("-" * 40)
    manga_list = api.search_manga(page=1, sort_by="-views")
    
    if manga_list:
        print(f"✓ Found {len(manga_list)} manga")
        for i, manga in enumerate(manga_list[:3], 1):
            print(f"  {i}. {manga['title']}")
            print(f"     URL: {manga['url']}")
            print(f"     Thumbnail: {manga['thumbnail'][:50]}..." if manga['thumbnail'] else "     No thumbnail")
    else:
        print("✗ No manga found")
    
    # Test 2: Get manga details
    if manga_list:
        print("\n2. Testing manga details...")
        print("-" * 40)
        first_manga = manga_list[0]
        details = api.get_manga_details(first_manga['url'])
        
        if details:
            print(f"✓ Got details for: {details.get('title', 'Unknown')}")
            print(f"  Chapters found: {details.get('chapter_count', 0)}")
        else:
            print("✗ Failed to get manga details")
    
    # Test 3: Search with query
    print("\n3. Testing search with query...")
    print("-" * 40)
    search_results = api.search_manga(query="one piece")
    
    if search_results:
        print(f"✓ Found {len(search_results)} results for 'one piece'")
        for i, manga in enumerate(search_results[:3], 1):
            print(f"  {i}. {manga['title']}")
    else:
        print("✗ No search results found")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_api()