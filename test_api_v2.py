#!/usr/bin/env python3
"""
Enhanced test script with better error handling and multiple domain support
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json

class LxHentaiAPIEnhanced:
    """Enhanced API client with better error handling"""
    
    def __init__(self):
        # Try multiple possible domains
        self.possible_domains = [
            "https://lxmanga.help",
            "https://lxmanga.net", 
            "https://lxmanga.com",
            "https://lxhentai.com",
            "https://lxmanga.site",
            "https://lxmanga.me"
        ]
        
        self.base_url = None
        self.session = requests.Session()
        
        # More comprehensive headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Find working domain
        self.find_working_domain()
    
    def find_working_domain(self):
        """Test domains to find a working one"""
        print("Testing domains to find a working one...")
        
        for domain in self.possible_domains:
            try:
                print(f"Testing {domain}...")
                self.session.headers['Referer'] = domain
                response = self.session.get(domain, timeout=5, allow_redirects=True)
                
                # Check if we got a valid response
                if response.status_code == 200:
                    # Check if it's actually the manga site
                    if any(keyword in response.text.lower() for keyword in ['manga', 'truyen', 'chapter', 'chuong']):
                        self.base_url = domain
                        print(f"✓ Found working domain: {domain}")
                        
                        # Check if there's a redirect to a new domain
                        if response.url != domain:
                            self.base_url = response.url.rstrip('/')
                            print(f"  Redirected to: {self.base_url}")
                        
                        return
                    else:
                        print(f"  Response OK but doesn't look like manga site")
                else:
                    print(f"  Status code: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"  Timeout")
            except requests.exceptions.ConnectionError:
                print(f"  Connection error")
            except Exception as e:
                print(f"  Error: {e}")
            
            time.sleep(0.5)  # Be polite
        
        # If no domain works, use the first one as fallback
        if not self.base_url:
            self.base_url = self.possible_domains[0]
            print(f"✗ No working domain found, using fallback: {self.base_url}")
    
    def test_homepage(self):
        """Test if we can access the homepage"""
        if not self.base_url:
            return False
            
        try:
            print(f"\nTesting homepage at {self.base_url}...")
            response = self.session.get(self.base_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for manga elements
                print("Looking for manga elements on homepage...")
                
                # Try various selectors
                selectors_to_try = [
                    ("a[href*='/truyen/']", "manga links"),
                    ("div.manga-item", "manga items"),
                    ("div.comic-item", "comic items"),
                    ("article.manga", "manga articles"),
                    ("div.manga-vertical", "vertical manga cards"),
                    ("div.grid", "grid layout"),
                    ("img[alt*='manga'], img[alt*='truyen']", "manga images")
                ]
                
                found_elements = []
                for selector, description in selectors_to_try:
                    elements = soup.select(selector)
                    if elements:
                        print(f"  ✓ Found {len(elements)} {description}")
                        found_elements.append((selector, elements))
                
                # Extract some manga URLs for testing
                manga_urls = []
                for link in soup.select("a[href*='/truyen/']")[:5]:
                    url = link.get('href', '')
                    if url:
                        manga_urls.append(url)
                        title = link.text.strip() or link.get('title', '')
                        if title:
                            print(f"    - {title[:50]}")
                
                return len(found_elements) > 0
                
            else:
                print(f"✗ Homepage returned status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error accessing homepage: {e}")
            return False
    
    def test_search_page(self):
        """Test if search page is accessible"""
        if not self.base_url:
            return False
            
        search_urls = [
            "/tim-kiem",
            "/search",
            "/danh-sach",
            "/manga-list",
            "/truyen"
        ]
        
        for search_path in search_urls:
            try:
                url = urljoin(self.base_url, search_path)
                print(f"\nTesting search at {url}...")
                
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Check if it's a valid search/list page
                    if soup.select("a[href*='/truyen/']") or soup.select("div.manga-item"):
                        print(f"  ✓ Found working search page at {search_path}")
                        return search_path
                    else:
                        print(f"  Page exists but no manga found")
                elif response.status_code == 404:
                    print(f"  404 Not Found")
                else:
                    print(f"  Status code: {response.status_code}")
                    
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def analyze_page_structure(self, url):
        """Analyze the HTML structure of a page"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            analysis = {
                'title': soup.title.string if soup.title else 'No title',
                'forms': len(soup.select('form')),
                'links': len(soup.select('a')),
                'images': len(soup.select('img')),
                'scripts': len(soup.select('script')),
                'manga_links': len(soup.select("a[href*='/truyen/']")),
                'chapter_links': len(soup.select("a[href*='/chuong/'], a[href*='/chapter/']"))
            }
            
            # Find main content area
            main_selectors = ['main', 'div.content', 'div.main-content', 'div.container']
            for selector in main_selectors:
                if soup.select_one(selector):
                    analysis['main_content'] = selector
                    break
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing page: {e}")
            return None


def run_comprehensive_test():
    """Run comprehensive API tests"""
    print("=" * 70)
    print("COMPREHENSIVE LXHENTAI API TEST")
    print("=" * 70)
    
    api = LxHentaiAPIEnhanced()
    
    if api.base_url:
        print(f"\nUsing base URL: {api.base_url}")
        
        # Test 1: Homepage
        print("\n" + "=" * 50)
        print("TEST 1: Homepage Access")
        print("-" * 50)
        homepage_works = api.test_homepage()
        
        # Test 2: Search functionality
        print("\n" + "=" * 50)
        print("TEST 2: Search Page")
        print("-" * 50)
        search_path = api.test_search_page()
        
        # Test 3: Analyze structure
        print("\n" + "=" * 50)
        print("TEST 3: Page Structure Analysis")
        print("-" * 50)
        
        analysis = api.analyze_page_structure(api.base_url)
        if analysis:
            print("Homepage structure:")
            for key, value in analysis.items():
                print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    # Summary
    print("\nSUMMARY:")
    print(f"- Working domain: {api.base_url if api.base_url else 'None found'}")
    print(f"- Homepage accessible: {'Yes' if homepage_works else 'No'}")
    print(f"- Search page found: {search_path if search_path else 'No'}")


if __name__ == "__main__":
    run_comprehensive_test()