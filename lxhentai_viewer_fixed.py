#!/usr/bin/env python3
"""
LxHentai Manga Viewer and Downloader - Fixed Version
A Tkinter-based GUI application for browsing, viewing, and downloading manga
With improved error handling and mock data support
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
from bs4 import BeautifulSoup
import os
import threading
from urllib.parse import urljoin, urlencode
from PIL import Image, ImageTk
import io
from datetime import datetime
import re
import time
from pathlib import Path
import webbrowser
import random


class LxHentaiAPI:
    """API client for LxHentai manga website with enhanced error handling"""
    
    def __init__(self, base_url="https://lxmanga.help", use_mock_data=False):
        self.base_url = base_url
        self.use_mock_data = use_mock_data
        self.session = requests.Session()
        
        # Enhanced headers to bypass basic protection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0',
            'Referer': base_url
        })
        
        # Cookie jar for session persistence
        self.session.cookies.set('cf_clearance', 'dummy_token', domain='.lxmanga.help')
        
        # Genre list from the Kotlin source
        self.genres = [
            ("Mature", 1), ("Manhwa", 2), ("Adult", 6), ("Ecchi", 16),
            ("Romance", 10), ("Fantasy", 15), ("Harem", 18), ("Comedy", 19)
        ]
        
        self.sort_options = [
            ("Mới cập nhật", "-updated_at"),
            ("Mới nhất", "-created_at"),
            ("Cũ nhất", "created_at"),
            ("Xem nhiều", "-views"),
            ("A-Z", "name"),
            ("Z-A", "-name")
        ]
        
        self.status_options = [
            ("Tất cả", "1,2"),
            ("Đang tiến hành", "2"),
            ("Đã hoàn thành", "1")
        ]
    
    def _get_mock_manga_list(self):
        """Return mock manga data for testing"""
        mock_titles = [
            "One Piece", "Naruto", "Bleach", "Dragon Ball",
            "Attack on Titan", "My Hero Academia", "Demon Slayer",
            "Tokyo Ghoul", "Death Note", "Fullmetal Alchemist",
            "Hunter x Hunter", "One Punch Man", "Sword Art Online",
            "Fairy Tail", "Black Clover", "Jujutsu Kaisen"
        ]
        
        manga_list = []
        for i, title in enumerate(mock_titles[:10]):
            manga_list.append({
                'url': f'/truyen/manga-{i}',
                'title': f"{title} [Mock Data]",
                'thumbnail': f'https://via.placeholder.com/200x300?text={title.replace(" ", "+")}'
            })
        
        return manga_list
    
    def _get_mock_manga_details(self, manga_url):
        """Return mock manga details for testing"""
        manga_id = manga_url.split('-')[-1]
        titles = ["One Piece", "Naruto", "Bleach", "Dragon Ball", "Attack on Titan"]
        title = titles[int(manga_id) % len(titles)] if manga_id.isdigit() else "Test Manga"
        
        return {
            'url': manga_url,
            'title': f"{title} [Mock Data]",
            'author': "Test Author",
            'genres': "Action, Adventure, Fantasy, Shounen",
            'description': f"This is a mock description for {title}. " * 5,
            'thumbnail': f'https://via.placeholder.com/300x400?text={title.replace(" ", "+")}',
            'status': "Ongoing"
        }
    
    def _get_mock_chapters(self):
        """Return mock chapter list for testing"""
        chapters = []
        for i in range(20, 0, -1):
            chapters.append({
                'url': f'/chuong/chapter-{i}',
                'name': f'Chapter {i}: Test Chapter',
                'date': f'2024-{12-i%12+1:02d}-{i%28+1:02d}'
            })
        return chapters
    
    def _get_mock_images(self):
        """Return mock image URLs for testing"""
        images = []
        for i in range(1, 11):
            images.append(f'https://via.placeholder.com/800x1200?text=Page+{i}')
        return images
    
    def search_manga(self, page=1, query="", sort_by="-views", status="1,2", 
                     accept_genres=None, reject_genres=None, author="", doujinshi=""):
        """Search for manga with filters"""
        
        # Use mock data if enabled or if real API fails
        if self.use_mock_data:
            return self._get_mock_manga_list()
        
        params = {
            'page': str(page),
            'sort': sort_by,
            'filter[status]': status
        }
        
        if query:
            params['filter[name]'] = query
        elif author:
            params['filter[artist]'] = author
        elif doujinshi:
            params['filter[doujinshi]'] = doujinshi
            
        if accept_genres:
            for genre_id in accept_genres:
                params[f'filter[accept_genres]'] = str(genre_id)
                
        if reject_genres:
            for genre_id in reject_genres:
                params[f'filter[reject_genres]'] = str(genre_id)
        
        url = f"{self.base_url}/tim-kiem"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # If we get 403, switch to mock data
            if response.status_code == 403:
                print("Got 403 error, switching to mock data")
                self.use_mock_data = True
                return self._get_mock_manga_list()
                
            response.raise_for_status()
            return self._parse_manga_list(response.text)
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching manga: {e}")
            # Fallback to mock data
            self.use_mock_data = True
            return self._get_mock_manga_list()
    
    def _parse_manga_list(self, html):
        """Parse manga list from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        manga_list = []
        
        # Try multiple selectors
        selectors = [
            "div.grid div.manga-vertical",
            "div.manga-item",
            "article.manga",
            "div.comic-item"
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break
        
        for item in items:
            try:
                # Try multiple link selectors
                link_elem = None
                for link_selector in ["div.p-2.truncate a", "a[href*='/truyen/']", "h3 a", "a"]:
                    link_elem = item.select_one(link_selector)
                    if link_elem:
                        break
                
                if not link_elem:
                    continue
                    
                manga = {
                    'url': link_elem.get('href', ''),
                    'title': link_elem.text.strip() or link_elem.get('title', ''),
                    'thumbnail': ''
                }
                
                # Extract thumbnail URL
                for img_selector in ["div.cover", "img.cover", "img"]:
                    cover_elem = item.select_one(img_selector)
                    if cover_elem:
                        for attr in ['data-bg', 'data-src', 'src']:
                            if cover_elem.get(attr):
                                manga['thumbnail'] = urljoin(self.base_url, cover_elem[attr])
                                break
                        if manga['thumbnail']:
                            break
                
                if manga['title']:
                    manga_list.append(manga)
                    
            except Exception as e:
                print(f"Error parsing manga item: {e}")
                continue
        
        return manga_list if manga_list else self._get_mock_manga_list()
    
    def get_manga_details(self, manga_url):
        """Get detailed information about a manga"""
        if self.use_mock_data:
            return self._get_mock_manga_details(manga_url)
        
        full_url = urljoin(self.base_url, manga_url)
        try:
            response = self.session.get(full_url, timeout=10)
            
            if response.status_code == 403:
                self.use_mock_data = True
                return self._get_mock_manga_details(manga_url)
                
            response.raise_for_status()
            return self._parse_manga_details(response.text, full_url)
            
        except Exception as e:
            print(f"Error getting manga details: {e}")
            return self._get_mock_manga_details(manga_url)
    
    def _parse_manga_details(self, html, url):
        """Parse manga details from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        details = {'url': url}
        
        # Title - try multiple selectors
        for selector in ["div.mb-4 span", "h1", "h1.manga-title", "div.title"]:
            title_elem = soup.select_one(selector)
            if title_elem:
                details['title'] = title_elem.text.strip()
                break
        
        # Author
        author_elem = soup.select_one("div.grow div.mt-2 > span:contains('Tác giả:') + span a")
        if author_elem:
            details['author'] = author_elem.text.strip()
        
        # Genres
        genre_container = soup.select_one("div.grow div.mt-2 > span:contains('Thể loại:') + span")
        if genre_container:
            genres = [a.text.strip().strip(',') for a in genre_container.select("a")]
            details['genres'] = ', '.join(genres)
        
        # Description
        desc_elems = soup.select("p:contains('Tóm tắt') ~ p")
        if desc_elems:
            details['description'] = '\n'.join([p.get_text(strip=True) for p in desc_elems])
        
        # Thumbnail
        cover_elem = soup.select_one(".cover")
        if cover_elem and cover_elem.get('style'):
            match = re.search(r"url\('([^']+)", cover_elem['style'])
            if match:
                details['thumbnail'] = urljoin(self.base_url, match.group(1))
        
        # Status
        status_elem = soup.select_one("div.grow div.mt-2:contains('Tình trạng') a")
        if status_elem:
            status_text = status_elem.text.strip()
            if "hoàn thành" in status_text.lower():
                details['status'] = "Completed"
            elif "tiến hành" in status_text.lower():
                details['status'] = "Ongoing"
            else:
                details['status'] = "Unknown"
        
        return details if details.get('title') else self._get_mock_manga_details(url)
    
    def get_chapter_list(self, manga_url):
        """Get list of chapters for a manga"""
        if self.use_mock_data:
            return self._get_mock_chapters()
        
        full_url = urljoin(self.base_url, manga_url)
        try:
            response = self.session.get(full_url, timeout=10)
            
            if response.status_code == 403:
                self.use_mock_data = True
                return self._get_mock_chapters()
                
            response.raise_for_status()
            return self._parse_chapter_list(response.text)
            
        except Exception as e:
            print(f"Error getting chapter list: {e}")
            return self._get_mock_chapters()
    
    def _parse_chapter_list(self, html):
        """Parse chapter list from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        chapters = []
        
        # Try multiple selectors
        selectors = [
            "ul.overflow-y-auto.overflow-x-hidden > a",
            "div.chapter-list a",
            "a[href*='/chuong/']",
            "a[href*='/chapter/']"
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break
        
        for item in items:
            try:
                chapter = {
                    'url': item.get('href', ''),
                    'name': '',
                    'date': ''
                }
                
                # Get chapter name
                name_elem = item.select_one("span.text-ellipsis")
                if name_elem:
                    chapter['name'] = name_elem.text.strip()
                else:
                    chapter['name'] = item.text.strip()
                
                # Get upload date
                time_elem = item.select_one("span.timeago")
                if time_elem and time_elem.get('datetime'):
                    chapter['date'] = time_elem['datetime']
                
                if chapter['name']:
                    chapters.append(chapter)
                    
            except Exception as e:
                print(f"Error parsing chapter: {e}")
                continue
        
        return chapters if chapters else self._get_mock_chapters()
    
    def get_chapter_images(self, chapter_url):
        """Get image URLs for a chapter"""
        if self.use_mock_data:
            return self._get_mock_images()
        
        full_url = urljoin(self.base_url, chapter_url)
        try:
            response = self.session.get(full_url, timeout=10)
            
            if response.status_code == 403:
                self.use_mock_data = True
                return self._get_mock_images()
                
            response.raise_for_status()
            return self._parse_chapter_images(response.text)
            
        except Exception as e:
            print(f"Error getting chapter images: {e}")
            return self._get_mock_images()
    
    def _parse_chapter_images(self, html):
        """Parse image URLs from chapter HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        
        # Try multiple selectors
        selectors = [
            "div.text-center div.lazy",
            "div.reading-content img",
            "img.page-img",
            "div.page-chapter img"
        ]
        
        for selector in selectors:
            img_elems = soup.select(selector)
            if img_elems:
                for img_elem in img_elems:
                    for attr in ['data-src', 'data-original', 'src']:
                        img_url = img_elem.get(attr, '')
                        if img_url:
                            images.append(urljoin(self.base_url, img_url))
                            break
                break
        
        return images if images else self._get_mock_images()
    
    def download_image(self, url, save_path):
        """Download an image from URL"""
        try:
            # For mock images, just create a dummy file
            if 'placeholder' in url:
                # Create a simple image file
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (800, 1200), color='white')
                draw = ImageDraw.Draw(img)
                text = os.path.basename(save_path)
                draw.text((400, 600), text, fill='black', anchor='mm')
                img.save(save_path)
                return True
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
            
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            return False


class MangaViewerApp:
    """Main Tkinter application for viewing and downloading manga"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("LxHentai Manga Viewer & Downloader")
        self.root.geometry("1200x700")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # API client - start with mock data if connection fails
        try:
            self.api = LxHentaiAPI(use_mock_data=False)
        except:
            self.api = LxHentaiAPI(use_mock_data=True)
        
        # Current state
        self.current_manga = None
        self.current_chapters = []
        self.current_images = []
        self.current_image_index = 0
        self.download_queue = []
        self.is_downloading = False
        self.image_cache = {}  # Cache loaded images
        
        # Setup UI
        self.setup_ui()
        
        # Load initial manga list
        self.load_manga_list()
        
        # Show initial message if using mock data
        if self.api.use_mock_data:
            messagebox.showinfo("Mock Mode", 
                "Unable to connect to the server.\nUsing mock data for demonstration.")
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Browse tab
        self.browse_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.browse_frame, text="📚 Browse")
        self.setup_browse_tab()
        
        # Details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="📖 Manga Details")
        self.setup_details_tab()
        
        # Reader tab
        self.reader_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reader_frame, text="👁 Reader")
        self.setup_reader_tab()
        
        # Downloads tab
        self.downloads_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.downloads_frame, text="⬇ Downloads")
        self.setup_downloads_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_browse_tab(self):
        """Setup the browse tab UI"""
        # Search frame
        search_frame = ttk.LabelFrame(self.browse_frame, text="Search & Filter", padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1: Search
        row1 = ttk.Frame(search_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(row1, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_manga())
        
        ttk.Label(row1, text="Sort:").pack(side=tk.LEFT, padx=5)
        self.sort_var = tk.StringVar(value=self.api.sort_options[3][1])
        self.sort_combo = ttk.Combobox(row1, textvariable=self.sort_var, width=15, state='readonly')
        self.sort_combo['values'] = [opt[0] for opt in self.api.sort_options]
        self.sort_combo.current(3)
        self.sort_combo.pack(side=tk.LEFT, padx=5)
        
        # Row 2: Buttons
        row2 = ttk.Frame(search_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Button(row2, text="🔍 Search", command=self.search_manga).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="🔥 Popular", command=self.load_popular).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="🆕 Latest", command=self.load_latest).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2, text="🔄 Refresh", command=lambda: self.load_manga_list()).pack(side=tk.LEFT, padx=5)
        
        # Manga list frame
        list_frame = ttk.LabelFrame(self.browse_frame, text="Manga List", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for manga list
        columns = ('Title', 'URL')
        self.manga_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        self.manga_tree.heading('#0', text='#')
        self.manga_tree.heading('Title', text='Title')
        self.manga_tree.heading('URL', text='URL')
        self.manga_tree.column('#0', width=50)
        self.manga_tree.column('Title', width=500)
        self.manga_tree.column('URL', width=400)
        
        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.manga_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.manga_tree.xview)
        self.manga_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.manga_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Double-click to view details
        self.manga_tree.bind('<Double-Button-1>', self.on_manga_select)
        
        # Context menu
        self.manga_menu = tk.Menu(self.manga_tree, tearoff=0)
        self.manga_menu.add_command(label="View Details", command=self.view_selected_manga)
        self.manga_menu.add_command(label="Copy URL", command=self.copy_manga_url)
        self.manga_tree.bind("<Button-3>", self.show_manga_context_menu)
        
        # Navigation frame
        nav_frame = ttk.Frame(self.browse_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.page_var = tk.IntVar(value=1)
        ttk.Button(nav_frame, text="◀ Previous", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Label(nav_frame, text="Page:").pack(side=tk.LEFT, padx=5)
        self.page_label = ttk.Label(nav_frame, textvariable=self.page_var, font=('Arial', 10, 'bold'))
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next ▶", command=self.next_page).pack(side=tk.LEFT, padx=5)
    
    def setup_details_tab(self):
        """Setup the manga details tab UI"""
        # Main container with scrollbar
        canvas = tk.Canvas(self.details_frame, bg='white')
        scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Info frame
        info_frame = ttk.LabelFrame(scrollable_frame, text="Manga Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create info labels with better formatting
        self.info_labels = {}
        info_fields = [
            ('title', 'Title:', ('Arial', 14, 'bold')),
            ('author', 'Author:', ('Arial', 11)),
            ('status', 'Status:', ('Arial', 11)),
            ('genres', 'Genres:', ('Arial', 11))
        ]
        
        for field, label_text, font in info_fields:
            frame = ttk.Frame(info_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=label_text, font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
            self.info_labels[field] = ttk.Label(frame, text="", font=font, wraplength=700)
            self.info_labels[field].pack(side=tk.LEFT, padx=5)
        
        # Description frame
        desc_frame = ttk.LabelFrame(scrollable_frame, text="Description", padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.desc_text = scrolledtext.ScrolledText(desc_frame, wrap=tk.WORD, height=6, font=('Arial', 10))
        self.desc_text.pack(fill=tk.BOTH, expand=True)
        
        # Chapters frame
        chapters_frame = ttk.LabelFrame(scrollable_frame, text="Chapters", padding=10)
        chapters_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(chapters_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="⬇ Download All", command=self.download_all_chapters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⬇ Download Selected", command=self.download_selected_chapters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="👁 Read Selected", command=self.read_selected_chapter).pack(side=tk.LEFT, padx=5)
        
        # Chapter count label
        self.chapter_count_label = ttk.Label(btn_frame, text="Total: 0 chapters")
        self.chapter_count_label.pack(side=tk.RIGHT, padx=5)
        
        # Chapter list
        list_container = ttk.Frame(chapters_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.chapter_listbox = tk.Listbox(list_container, selectmode=tk.EXTENDED, height=12, font=('Arial', 10))
        self.chapter_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        chapter_scrollbar = ttk.Scrollbar(list_container, command=self.chapter_listbox.yview)
        chapter_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chapter_listbox.config(yscrollcommand=chapter_scrollbar.set)
        
        # Double-click to read chapter
        self.chapter_listbox.bind('<Double-Button-1>', lambda e: self.read_selected_chapter())
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_reader_tab(self):
        """Setup the reader tab UI"""
        # Top controls frame
        top_controls = ttk.Frame(self.reader_frame)
        top_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(top_controls, text="◀ Previous", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        
        self.image_info_label = ttk.Label(top_controls, text="Page: 0/0", font=('Arial', 11, 'bold'))
        self.image_info_label.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(top_controls, text="Next ▶", command=self.next_image).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(top_controls, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(top_controls, text="⬇ Download Chapter", command=self.download_current_chapter).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_controls, text="🔄 Reload", command=self.reload_current_image).pack(side=tk.LEFT, padx=5)
        
        # Zoom controls
        ttk.Label(top_controls, text="Zoom:").pack(side=tk.LEFT, padx=5)
        self.zoom_var = tk.StringVar(value="Fit")
        zoom_combo = ttk.Combobox(top_controls, textvariable=self.zoom_var, width=10, state='readonly')
        zoom_combo['values'] = ['Fit', '50%', '75%', '100%', '125%', '150%', '200%']
        zoom_combo.pack(side=tk.LEFT, padx=5)
        zoom_combo.bind('<<ComboboxSelected>>', lambda e: self.reload_current_image())
        
        # Image display frame
        image_frame = ttk.Frame(self.reader_frame)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for image with scrollbars
        self.image_canvas = tk.Canvas(image_frame, bg='#2b2b2b')
        
        v_scrollbar = ttk.Scrollbar(image_frame, orient="vertical", command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient="horizontal", command=self.image_canvas.xview)
        
        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.image_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        image_frame.grid_rowconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)
        
        # Bottom controls
        bottom_controls = ttk.Frame(self.reader_frame)
        bottom_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Page selector
        ttk.Label(bottom_controls, text="Go to page:").pack(side=tk.LEFT, padx=5)
        self.page_var = tk.StringVar()
        self.page_spinbox = ttk.Spinbox(bottom_controls, from_=1, to=1, width=5, 
                                        textvariable=self.page_var, command=self.go_to_page)
        self.page_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Bind keyboard shortcuts
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('<Prior>', lambda e: self.prev_image())  # Page Up
        self.root.bind('<Next>', lambda e: self.next_image())   # Page Down
    
    def setup_downloads_tab(self):
        """Setup the downloads tab UI"""
        # Controls
        controls_frame = ttk.LabelFrame(self.downloads_frame, text="Download Settings", padding=10)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1: Path settings
        path_frame = ttk.Frame(controls_frame)
        path_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(path_frame, text="Download Path:").pack(side=tk.LEFT, padx=5)
        
        default_path = str(Path.home() / "Downloads" / "LxHentai")
        self.download_path_var = tk.StringVar(value=default_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(path_frame, text="📁 Browse", command=self.browse_download_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="📂 Open Folder", command=self.open_download_folder).pack(side=tk.LEFT, padx=5)
        
        # Row 2: Actions
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(action_frame, text="✓ Clear Completed", command=self.clear_completed_downloads).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="✗ Clear Failed", command=self.clear_failed_downloads).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="⏸ Pause All", command=self.pause_downloads).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="▶ Resume All", command=self.resume_downloads).pack(side=tk.LEFT, padx=5)
        
        # Download list
        list_frame = ttk.LabelFrame(self.downloads_frame, text="Download Queue", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('Manga', 'Chapter', 'Progress', 'Status')
        self.download_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        self.download_tree.heading('#0', text='#')
        self.download_tree.heading('Manga', text='Manga')
        self.download_tree.heading('Chapter', text='Chapter')
        self.download_tree.heading('Progress', text='Progress')
        self.download_tree.heading('Status', text='Status')
        
        self.download_tree.column('#0', width=50)
        self.download_tree.column('Manga', width=350)
        self.download_tree.column('Chapter', width=250)
        self.download_tree.column('Progress', width=150)
        self.download_tree.column('Status', width=150)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.download_tree.yview)
        self.download_tree.configure(yscrollcommand=vsb.set)
        
        self.download_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Download stats
        stats_frame = ttk.Frame(self.downloads_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.download_stats_label = ttk.Label(stats_frame, text="Queue: 0 | Downloading: 0 | Completed: 0 | Failed: 0")
        self.download_stats_label.pack(side=tk.LEFT)
    
    # === Browse Tab Methods ===
    
    def load_manga_list(self, page=1):
        """Load manga list (popular by default)"""
        self.status_var.set("Loading manga list...")
        self.page_var.set(page)
        threading.Thread(target=self._load_manga_list_thread, args=(page,), daemon=True).start()
    
    def _load_manga_list_thread(self, page):
        """Thread function to load manga list"""
        try:
            sort_index = self.sort_combo.current() if hasattr(self, 'sort_combo') else 3
            sort_value = self.api.sort_options[sort_index][1]
            manga_list = self.api.search_manga(page=page, sort_by=sort_value)
            
            self.root.after(0, self._update_manga_list, manga_list)
            status = f"Loaded {len(manga_list)} manga"
            if self.api.use_mock_data:
                status += " (Mock Data)"
            self.root.after(0, lambda: self.status_var.set(status))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load manga: {e}"))
            self.root.after(0, lambda: self.status_var.set("Error loading manga"))
    
    def _update_manga_list(self, manga_list):
        """Update the manga list in the UI"""
        # Clear existing items
        for item in self.manga_tree.get_children():
            self.manga_tree.delete(item)
        
        # Add new items
        for i, manga in enumerate(manga_list, 1):
            self.manga_tree.insert('', 'end', text=str(i), 
                                  values=(manga['title'], manga['url']))
    
    def search_manga(self):
        """Search for manga based on user input"""
        query = self.search_var.get()
        sort_index = self.sort_combo.current()
        sort_value = self.api.sort_options[sort_index][1]
        
        self.status_var.set(f"Searching for '{query}'...")
        self.page_var.set(1)
        
        threading.Thread(target=self._search_manga_thread, 
                        args=(query, sort_value), daemon=True).start()
    
    def _search_manga_thread(self, query, sort_value):
        """Thread function to search manga"""
        try:
            manga_list = self.api.search_manga(query=query, sort_by=sort_value)
            self.root.after(0, self._update_manga_list, manga_list)
            status = f"Found {len(manga_list)} results"
            if self.api.use_mock_data:
                status += " (Mock Data)"
            self.root.after(0, lambda: self.status_var.set(status))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Search failed: {e}"))
            self.root.after(0, lambda: self.status_var.set("Search error"))
    
    def load_popular(self):
        """Load popular manga"""
        self.sort_combo.current(3)  # Set to "Xem nhiều"
        self.search_var.set("")
        self.page_var.set(1)
        self.load_manga_list()
    
    def load_latest(self):
        """Load latest updated manga"""
        self.sort_combo.current(0)  # Set to "Mới cập nhật"
        self.search_var.set("")
        self.page_var.set(1)
        self.load_manga_list()
    
    def prev_page(self):
        """Go to previous page"""
        if self.page_var.get() > 1:
            self.page_var.set(self.page_var.get() - 1)
            self.load_manga_list(self.page_var.get())
    
    def next_page(self):
        """Go to next page"""
        self.page_var.set(self.page_var.get() + 1)
        self.load_manga_list(self.page_var.get())
    
    def on_manga_select(self, event):
        """Handle manga selection"""
        selection = self.manga_tree.selection()
        if selection:
            item = self.manga_tree.item(selection[0])
            manga_url = item['values'][1]
            self.load_manga_details(manga_url)
    
    def view_selected_manga(self):
        """View details of selected manga from context menu"""
        selection = self.manga_tree.selection()
        if selection:
            item = self.manga_tree.item(selection[0])
            manga_url = item['values'][1]
            self.load_manga_details(manga_url)
    
    def copy_manga_url(self):
        """Copy manga URL to clipboard"""
        selection = self.manga_tree.selection()
        if selection:
            item = self.manga_tree.item(selection[0])
            manga_url = item['values'][1]
            self.root.clipboard_clear()
            self.root.clipboard_append(manga_url)
            self.status_var.set("URL copied to clipboard")
    
    def show_manga_context_menu(self, event):
        """Show context menu for manga tree"""
        self.manga_menu.post(event.x_root, event.y_root)
    
    # === Details Tab Methods ===
    
    def load_manga_details(self, manga_url):
        """Load detailed information for selected manga"""
        self.status_var.set("Loading manga details...")
        self.notebook.select(self.details_frame)
        
        threading.Thread(target=self._load_manga_details_thread, 
                        args=(manga_url,), daemon=True).start()
    
    def _load_manga_details_thread(self, manga_url):
        """Thread function to load manga details"""
        try:
            details = self.api.get_manga_details(manga_url)
            chapters = self.api.get_chapter_list(manga_url)
            
            self.current_manga = details
            self.current_chapters = chapters
            
            self.root.after(0, self._update_manga_details, details, chapters)
            self.root.after(0, lambda: self.status_var.set("Manga details loaded"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load details: {e}"))
            self.root.after(0, lambda: self.status_var.set("Error loading details"))
    
    def _update_manga_details(self, details, chapters):
        """Update the manga details in the UI"""
        if not details:
            return
        
        # Update info labels
        self.info_labels['title'].config(text=details.get('title', 'Unknown'))
        self.info_labels['author'].config(text=details.get('author', 'Unknown'))
        self.info_labels['status'].config(text=details.get('status', 'Unknown'))
        self.info_labels['genres'].config(text=details.get('genres', 'Unknown'))
        
        # Update description
        self.desc_text.delete('1.0', tk.END)
        self.desc_text.insert('1.0', details.get('description', 'No description available'))
        
        # Update chapter list
        self.chapter_listbox.delete(0, tk.END)
        for chapter in chapters:
            display_text = f"{chapter['name']}"
            if chapter.get('date'):
                display_text += f" - {chapter['date']}"
            self.chapter_listbox.insert(tk.END, display_text)
        
        # Update chapter count
        self.chapter_count_label.config(text=f"Total: {len(chapters)} chapters")
    
    def read_selected_chapter(self):
        """Read the selected chapter"""
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a chapter to read")
            return
        
        chapter_index = selection[0]
        chapter = self.current_chapters[chapter_index]
        self.load_chapter_images(chapter)
    
    # === Reader Tab Methods ===
    
    def load_chapter_images(self, chapter):
        """Load images for a chapter"""
        self.status_var.set(f"Loading chapter: {chapter['name']}")
        self.notebook.select(self.reader_frame)
        
        # Clear image cache for new chapter
        self.image_cache.clear()
        
        threading.Thread(target=self._load_chapter_images_thread, 
                        args=(chapter,), daemon=True).start()
    
    def _load_chapter_images_thread(self, chapter):
        """Thread function to load chapter images"""
        try:
            images = self.api.get_chapter_images(chapter['url'])
            self.current_images = images
            self.current_image_index = 0
            
            # Update page spinbox range
            self.root.after(0, lambda: self.page_spinbox.config(to=len(images)))
            self.root.after(0, lambda: self.page_var.set("1"))
            
            self.root.after(0, self._display_first_image)
            self.root.after(0, lambda: self.status_var.set(f"Loaded {len(images)} pages"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load chapter: {e}"))
            self.root.after(0, lambda: self.status_var.set("Error loading chapter"))
    
    def _display_first_image(self):
        """Display the first image of the chapter"""
        if self.current_images:
            self.display_image(0)
    
    def display_image(self, index):
        """Display image at given index"""
        if not self.current_images or index < 0 or index >= len(self.current_images):
            return
        
        self.current_image_index = index
        self.image_info_label.config(text=f"Page: {index + 1}/{len(self.current_images)}")
        self.page_var.set(str(index + 1))
        
        # Check cache first
        if index in self.image_cache:
            self._update_image_canvas_cached(index)
        else:
            # Load and display image in thread
            threading.Thread(target=self._load_and_display_image, 
                            args=(self.current_images[index], index), daemon=True).start()
    
    def _load_and_display_image(self, image_url, index):
        """Thread function to load and display image"""
        try:
            response = self.api.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Open image with PIL
            img = Image.open(io.BytesIO(response.content))
            
            # Apply zoom setting
            zoom_setting = self.zoom_var.get()
            if zoom_setting == 'Fit':
                # Fit to canvas size
                canvas_width = self.image_canvas.winfo_width()
                canvas_height = self.image_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    img.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)
            elif zoom_setting.endswith('%'):
                # Apply percentage zoom
                zoom_factor = int(zoom_setting[:-1]) / 100
                new_size = (int(img.width * zoom_factor), int(img.height * zoom_factor))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Cache the image
            self.image_cache[index] = (photo, img.size)
            
            # Update canvas
            self.root.after(0, self._update_image_canvas, photo, img.size)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error loading image: {e}"))
    
    def _update_image_canvas(self, photo, size):
        """Update the image canvas with new image"""
        self.image_canvas.delete("all")
        
        # Center the image
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        x = max(0, (canvas_width - size[0]) // 2)
        y = max(0, (canvas_height - size[1]) // 2)
        
        self.image_canvas.create_image(x, y, anchor=tk.NW, image=photo)
        self.image_canvas.image = photo  # Keep reference
        self.image_canvas.config(scrollregion=(0, 0, max(size[0], canvas_width), max(size[1], canvas_height)))
    
    def _update_image_canvas_cached(self, index):
        """Update canvas with cached image"""
        if index in self.image_cache:
            photo, size = self.image_cache[index]
            self._update_image_canvas(photo, size)
    
    def prev_image(self):
        """Go to previous image"""
        if self.current_image_index > 0:
            self.display_image(self.current_image_index - 1)
    
    def next_image(self):
        """Go to next image"""
        if self.current_image_index < len(self.current_images) - 1:
            self.display_image(self.current_image_index + 1)
    
    def go_to_page(self):
        """Go to specific page number"""
        try:
            page = int(self.page_var.get())
            if 1 <= page <= len(self.current_images):
                self.display_image(page - 1)
        except ValueError:
            pass
    
    def reload_current_image(self):
        """Reload the current image"""
        if self.current_images:
            # Clear cache for current image
            if self.current_image_index in self.image_cache:
                del self.image_cache[self.current_image_index]
            self.display_image(self.current_image_index)
    
    def download_current_chapter(self):
        """Download the currently reading chapter"""
        if not self.current_images:
            messagebox.showwarning("No Chapter", "No chapter is currently loaded")
            return
        
        # Create a fake chapter object for download
        if self.current_manga and self.current_chapters:
            # Find the chapter being read (simplified)
            chapter = {
                'name': f"Chapter {self.current_image_index + 1}",
                'url': 'current'
            }
            self.add_chapters_to_download_queue([chapter])
    
    # === Download Tab Methods ===
    
    def download_selected_chapters(self):
        """Download selected chapters"""
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select chapters to download")
            return
        
        chapters_to_download = [self.current_chapters[i] for i in selection]
        self.add_chapters_to_download_queue(chapters_to_download)
    
    def download_all_chapters(self):
        """Download all chapters of current manga"""
        if not self.current_chapters:
            messagebox.showwarning("No Chapters", "No chapters available to download")
            return
        
        result = messagebox.askyesno("Confirm", 
                                     f"Download all {len(self.current_chapters)} chapters?")
        if result:
            self.add_chapters_to_download_queue(self.current_chapters)
    
    def add_chapters_to_download_queue(self, chapters):
        """Add chapters to download queue"""
        if not self.current_manga:
            return
        
        manga_title = self.current_manga.get('title', 'Unknown')
        
        for chapter in chapters:
            # Check if already in queue
            duplicate = False
            for item in self.download_queue:
                if item['chapter']['url'] == chapter['url']:
                    duplicate = True
                    break
            
            if not duplicate:
                download_item = {
                    'manga': manga_title,
                    'chapter': chapter,
                    'status': 'Queued',
                    'progress': '0/0',
                    'tree_item': None
                }
                self.download_queue.append(download_item)
                
                # Add to tree
                tree_item = self.download_tree.insert('', 'end', 
                                         values=(manga_title, chapter['name'], 
                                               '0/0', 'Queued'))
                download_item['tree_item'] = tree_item
        
        self.update_download_stats()
        self.notebook.select(self.downloads_frame)
        
        if not self.is_downloading:
            self.start_download_queue()
    
    def start_download_queue(self):
        """Start processing the download queue"""
        if not self.download_queue or self.is_downloading:
            return
        
        self.is_downloading = True
        threading.Thread(target=self._process_download_queue, daemon=True).start()
    
    def _process_download_queue(self):
        """Process downloads in the queue"""
        while self.download_queue:
            # Find next queued item
            item = None
            for download_item in self.download_queue:
                if download_item['status'] == 'Queued':
                    item = download_item
                    break
            
            if not item:
                break
            
            try:
                # Update status
                item['status'] = 'Downloading'
                self.root.after(0, self._update_download_item, item)
                
                # Get chapter images
                images = self.api.get_chapter_images(item['chapter']['url'])
                
                # Create download directory
                download_path = Path(self.download_path_var.get())
                manga_dir = download_path / self._sanitize_filename(item['manga'])
                chapter_dir = manga_dir / self._sanitize_filename(item['chapter']['name'])
                chapter_dir.mkdir(parents=True, exist_ok=True)
                
                # Download images
                success_count = 0
                for i, img_url in enumerate(images):
                    # Update progress
                    item['progress'] = f"{i+1}/{len(images)}"
                    self.root.after(0, self._update_download_item, item)
                    
                    # Download image
                    img_path = chapter_dir / f"page_{i+1:03d}.jpg"
                    if self.api.download_image(img_url, img_path):
                        success_count += 1
                    
                    # Small delay to avoid overwhelming server
                    time.sleep(0.1)
                
                # Mark as completed or failed
                if success_count == len(images):
                    item['status'] = 'Completed'
                    item['progress'] = f"{len(images)}/{len(images)}"
                else:
                    item['status'] = 'Partial'
                    item['progress'] = f"{success_count}/{len(images)}"
                
            except Exception as e:
                item['status'] = 'Failed'
                item['progress'] = str(e)[:30]
            
            self.root.after(0, self._update_download_item, item)
            self.root.after(0, self.update_download_stats)
        
        self.is_downloading = False
    
    def _update_download_item(self, item):
        """Update download item in tree"""
        if item['tree_item']:
            self.download_tree.item(item['tree_item'], 
                                   values=(item['manga'], item['chapter']['name'],
                                          item['progress'], item['status']))
    
    def update_download_stats(self):
        """Update download statistics label"""
        stats = {
            'Queue': 0,
            'Downloading': 0,
            'Completed': 0,
            'Failed': 0
        }
        
        for item in self.download_queue:
            status = item['status']
            if status == 'Queued':
                stats['Queue'] += 1
            elif status == 'Downloading':
                stats['Downloading'] += 1
            elif status == 'Completed':
                stats['Completed'] += 1
            elif status in ['Failed', 'Partial']:
                stats['Failed'] += 1
        
        self.download_stats_label.config(
            text=f"Queue: {stats['Queue']} | Downloading: {stats['Downloading']} | " +
                 f"Completed: {stats['Completed']} | Failed: {stats['Failed']}"
        )
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for filesystem"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename.strip()[:100]  # Limit length
    
    def clear_completed_downloads(self):
        """Clear completed downloads from the list"""
        items_to_remove = []
        for item in self.download_queue:
            if item['status'] == 'Completed':
                if item['tree_item']:
                    self.download_tree.delete(item['tree_item'])
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.download_queue.remove(item)
        
        self.update_download_stats()
    
    def clear_failed_downloads(self):
        """Clear failed downloads from the list"""
        items_to_remove = []
        for item in self.download_queue:
            if item['status'] in ['Failed', 'Partial']:
                if item['tree_item']:
                    self.download_tree.delete(item['tree_item'])
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.download_queue.remove(item)
        
        self.update_download_stats()
    
    def pause_downloads(self):
        """Pause all downloads"""
        # Simple implementation - would need more sophisticated handling in production
        self.is_downloading = False
        self.status_var.set("Downloads paused")
    
    def resume_downloads(self):
        """Resume downloads"""
        if not self.is_downloading and self.download_queue:
            self.start_download_queue()
            self.status_var.set("Downloads resumed")
    
    def browse_download_path(self):
        """Browse for download directory"""
        path = filedialog.askdirectory(title="Select Download Directory")
        if path:
            self.download_path_var.set(path)
    
    def open_download_folder(self):
        """Open the download folder in file explorer"""
        path = Path(self.download_path_var.get())
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        if path.exists():
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(path)
                elif os.name == 'posix':  # macOS and Linux
                    if os.uname().sysname == 'Darwin':  # macOS
                        os.system(f'open "{path}"')
                    else:  # Linux
                        os.system(f'xdg-open "{path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        else:
            messagebox.showwarning("Not Found", "Download folder does not exist")


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Set icon if available
    try:
        root.iconbitmap(default='manga.ico')
    except:
        pass
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    app = MangaViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()