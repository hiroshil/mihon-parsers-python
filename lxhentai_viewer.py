#!/usr/bin/env python3
"""
LxHentai Manga Viewer and Downloader
A Tkinter-based GUI application for browsing, viewing, and downloading manga from LxHentai
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from tkinter import PhotoImage
import requests
from bs4 import BeautifulSoup
import json
import os
import threading
from urllib.parse import urljoin, urlencode, urlparse
from PIL import Image, ImageTk
import io
from datetime import datetime
import re
import time
from pathlib import Path
import webbrowser


class LxHentaiAPI:
    """API client for LxHentai manga website"""
    
    def __init__(self, base_url="https://lxmanga.help"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': base_url
        })
        
        # Genre list from the Kotlin source
        self.genres = [
            ("Mature", 1), ("Manhwa", 2), ("Group", 3), ("Housewife", 4),
            ("NTR", 5), ("Adult", 6), ("Series", 7), ("Complete", 8),
            ("Ngực Lớn", 9), ("Lãng Mạn", 10), ("Truyện Màu", 11),
            ("Mind Break", 12), ("Mắt Kính", 13), ("Ngực Nhỏ", 14),
            ("Fantasy", 15), ("Ecchi", 16), ("Bạo Dâm", 17), ("Harem", 18),
            ("Hài Hước", 19), ("Cosplay", 20), ("Hầu Gái", 21), ("Loli", 22),
            ("Shota", 23), ("Gangbang", 24), ("Doujinshi", 25), ("Guro", 26),
            ("Virgin", 27), ("OneShot", 28), ("Chơi Hai Lỗ", 29), ("Hậu Môn", 30),
            ("Nữ Sinh", 31), ("Mang Thai", 32), ("Giáo Viên", 33), ("Loạn Luân", 34),
            ("Truyện Không Che", 35), ("Futanari", 36), ("Yuri", 37), ("Nô Lệ", 38),
            ("Đồ Bơi", 39), ("Thể Thao", 40), ("Truyện Ngắn", 41), ("Lão Gìa Dâm", 42),
            ("Hãm Hiếp", 43), ("Monster Girl", 44), ("Y Tá", 45), ("Supernatural", 46),
            ("3D", 47), ("Truyện Comic", 48), ("Animal girl", 49), ("Thú Vật", 50),
            ("Kinh Dị", 51), ("Quái Vật", 52), ("Xúc Tua", 53), ("Gender Bender", 54),
            ("Yaoi", 55), ("CG", 56), ("Trap", 57), ("Furry", 58),
            ("Mind Control", 59), ("Elf", 60), ("Côn Trùng", 61), ("Kogal", 62),
            ("Artist", 63), ("Scat", 64), ("Milf", 65), ("LXHENTAI", 66)
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
    
    def search_manga(self, page=1, query="", sort_by="-views", status="1,2", 
                     accept_genres=None, reject_genres=None, author="", doujinshi=""):
        """Search for manga with filters"""
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
            response.raise_for_status()
            return self._parse_manga_list(response.text)
        except Exception as e:
            print(f"Error searching manga: {e}")
            return []
    
    def _parse_manga_list(self, html):
        """Parse manga list from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        manga_list = []
        
        for item in soup.select("div.grid div.manga-vertical"):
            try:
                link_elem = item.select_one("div.p-2.truncate a")
                if not link_elem:
                    continue
                    
                manga = {
                    'url': link_elem.get('href', ''),
                    'title': link_elem.text.strip(),
                    'thumbnail': ''
                }
                
                # Extract thumbnail URL from data-bg attribute
                cover_elem = item.select_one("div.cover")
                if cover_elem and cover_elem.get('data-bg'):
                    manga['thumbnail'] = urljoin(self.base_url, cover_elem['data-bg'])
                
                manga_list.append(manga)
            except Exception as e:
                print(f"Error parsing manga item: {e}")
                continue
        
        return manga_list
    
    def get_manga_details(self, manga_url):
        """Get detailed information about a manga"""
        full_url = urljoin(self.base_url, manga_url)
        try:
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
        
        # Title
        title_elem = soup.select_one("div.mb-4 span")
        if title_elem:
            details['title'] = title_elem.text.strip()
        
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
            # Extract URL from style attribute
            match = re.search(r"url\('([^']+)", cover_elem['style'])
            if match:
                details['thumbnail'] = urljoin(self.base_url, match.group(1))
        
        # Status
        status_elem = soup.select_one("div.grow div.mt-2:contains('Tình trạng') a")
        if status_elem:
            status_text = status_elem.text.strip()
            if status_text == "Đã hoàn thành":
                details['status'] = "Completed"
            elif status_text == "Đang tiến hành":
                details['status'] = "Ongoing"
            else:
                details['status'] = "Unknown"
        
        return details
    
    def get_chapter_list(self, manga_url):
        """Get list of chapters for a manga"""
        full_url = urljoin(self.base_url, manga_url)
        try:
            response = self.session.get(full_url, timeout=10)
            response.raise_for_status()
            return self._parse_chapter_list(response.text)
        except Exception as e:
            print(f"Error getting chapter list: {e}")
            return []
    
    def _parse_chapter_list(self, html):
        """Parse chapter list from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        chapters = []
        
        for item in soup.select("ul.overflow-y-auto.overflow-x-hidden > a"):
            try:
                chapter = {
                    'url': item.get('href', ''),
                    'name': item.select_one("span.text-ellipsis").text.strip() if item.select_one("span.text-ellipsis") else "",
                    'date': ''
                }
                
                # Get upload date
                time_elem = item.select_one("span.timeago")
                if time_elem and time_elem.get('datetime'):
                    chapter['date'] = time_elem['datetime']
                
                chapters.append(chapter)
            except Exception as e:
                print(f"Error parsing chapter: {e}")
                continue
        
        return chapters
    
    def get_chapter_images(self, chapter_url):
        """Get image URLs for a chapter"""
        full_url = urljoin(self.base_url, chapter_url)
        try:
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
        
        for img_elem in soup.select("div.text-center div.lazy"):
            img_url = img_elem.get('data-src', '')
            if not img_url and img_elem.get('abs:data-src'):
                img_url = img_elem['abs:data-src']
            if img_url:
                images.append(urljoin(self.base_url, img_url))
        
        return images
    
    def download_image(self, url, save_path):
        """Download an image from URL"""
        try:
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
        
        # API client
        self.api = LxHentaiAPI()
        
        # Current state
        self.current_manga = None
        self.current_chapters = []
        self.current_images = []
        self.current_image_index = 0
        self.download_queue = []
        self.is_downloading = False
        
        # Setup UI
        self.setup_ui()
        
        # Load initial manga list
        self.load_manga_list()
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Browse tab
        self.browse_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.browse_frame, text="Browse")
        self.setup_browse_tab()
        
        # Details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="Manga Details")
        self.setup_details_tab()
        
        # Reader tab
        self.reader_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reader_frame, text="Reader")
        self.setup_reader_tab()
        
        # Downloads tab
        self.downloads_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.downloads_frame, text="Downloads")
        self.setup_downloads_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_browse_tab(self):
        """Setup the browse tab UI"""
        # Search frame
        search_frame = ttk.Frame(self.browse_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_manga())
        
        ttk.Label(search_frame, text="Sort:").pack(side=tk.LEFT, padx=5)
        self.sort_var = tk.StringVar(value=self.api.sort_options[3][1])  # Default to "Xem nhiều"
        self.sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_var, width=15)
        self.sort_combo['values'] = [opt[0] for opt in self.api.sort_options]
        self.sort_combo.current(3)
        self.sort_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="Search", command=self.search_manga).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Popular", command=self.load_popular).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Latest", command=self.load_latest).pack(side=tk.LEFT, padx=5)
        
        # Manga list frame with scrollbar
        list_frame = ttk.Frame(self.browse_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for manga list
        columns = ('Title', 'URL')
        self.manga_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        self.manga_tree.heading('#0', text='#')
        self.manga_tree.heading('Title', text='Title')
        self.manga_tree.heading('URL', text='URL')
        self.manga_tree.column('#0', width=50)
        self.manga_tree.column('Title', width=400)
        self.manga_tree.column('URL', width=300)
        
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
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.browse_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.page_var = tk.IntVar(value=1)
        ttk.Button(nav_frame, text="Previous", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Label(nav_frame, text="Page:").pack(side=tk.LEFT, padx=5)
        self.page_label = ttk.Label(nav_frame, textvariable=self.page_var)
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next", command=self.next_page).pack(side=tk.LEFT, padx=5)
    
    def setup_details_tab(self):
        """Setup the manga details tab UI"""
        # Main container with scrollbar
        canvas = tk.Canvas(self.details_frame)
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
        
        # Title
        self.title_label = ttk.Label(info_frame, text="Title: ", font=('Arial', 12, 'bold'))
        self.title_label.pack(anchor=tk.W, pady=2)
        
        # Author
        self.author_label = ttk.Label(info_frame, text="Author: ")
        self.author_label.pack(anchor=tk.W, pady=2)
        
        # Status
        self.status_label = ttk.Label(info_frame, text="Status: ")
        self.status_label.pack(anchor=tk.W, pady=2)
        
        # Genres
        self.genres_label = ttk.Label(info_frame, text="Genres: ", wraplength=800)
        self.genres_label.pack(anchor=tk.W, pady=2)
        
        # Description
        desc_frame = ttk.LabelFrame(scrollable_frame, text="Description", padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.desc_text = scrolledtext.ScrolledText(desc_frame, wrap=tk.WORD, height=6)
        self.desc_text.pack(fill=tk.BOTH, expand=True)
        
        # Chapters frame
        chapters_frame = ttk.LabelFrame(scrollable_frame, text="Chapters", padding=10)
        chapters_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(chapters_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Download All Chapters", command=self.download_all_chapters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Download Selected", command=self.download_selected_chapters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Read Selected", command=self.read_selected_chapter).pack(side=tk.LEFT, padx=5)
        
        # Chapter list
        self.chapter_listbox = tk.Listbox(chapters_frame, selectmode=tk.EXTENDED, height=15)
        self.chapter_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        chapter_scrollbar = ttk.Scrollbar(chapters_frame, command=self.chapter_listbox.yview)
        chapter_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chapter_listbox.config(yscrollcommand=chapter_scrollbar.set)
        
        # Double-click to read chapter
        self.chapter_listbox.bind('<Double-Button-1>', lambda e: self.read_selected_chapter())
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_reader_tab(self):
        """Setup the reader tab UI"""
        # Controls frame
        controls_frame = ttk.Frame(self.reader_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Previous", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        
        self.image_info_label = ttk.Label(controls_frame, text="Page: 0/0")
        self.image_info_label.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(controls_frame, text="Next", command=self.next_image).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Download Chapter", command=self.download_current_chapter).pack(side=tk.LEFT, padx=20)
        
        # Image display with scrollbars
        image_frame = ttk.Frame(self.reader_frame)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for image
        self.image_canvas = tk.Canvas(image_frame, bg='black')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(image_frame, orient="vertical", command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient="horizontal", command=self.image_canvas.xview)
        
        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.image_canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        image_frame.grid_rowconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)
        
        # Bind keyboard shortcuts
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
    
    def setup_downloads_tab(self):
        """Setup the downloads tab UI"""
        # Controls
        controls_frame = ttk.Frame(self.downloads_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Clear Completed", command=self.clear_completed_downloads).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Open Download Folder", command=self.open_download_folder).pack(side=tk.LEFT, padx=5)
        
        self.download_path_var = tk.StringVar(value=str(Path.home() / "Downloads" / "LxHentai"))
        ttk.Label(controls_frame, text="Download Path:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(controls_frame, textvariable=self.download_path_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Browse", command=self.browse_download_path).pack(side=tk.LEFT, padx=5)
        
        # Download list
        list_frame = ttk.Frame(self.downloads_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('Manga', 'Chapter', 'Progress', 'Status')
        self.download_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        self.download_tree.heading('#0', text='#')
        self.download_tree.heading('Manga', text='Manga')
        self.download_tree.heading('Chapter', text='Chapter')
        self.download_tree.heading('Progress', text='Progress')
        self.download_tree.heading('Status', text='Status')
        
        self.download_tree.column('#0', width=50)
        self.download_tree.column('Manga', width=300)
        self.download_tree.column('Chapter', width=200)
        self.download_tree.column('Progress', width=150)
        self.download_tree.column('Status', width=100)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.download_tree.yview)
        self.download_tree.configure(yscrollcommand=vsb.set)
        
        self.download_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
    
    def load_manga_list(self, page=1):
        """Load manga list (popular by default)"""
        self.status_var.set("Loading manga list...")
        threading.Thread(target=self._load_manga_list_thread, args=(page,), daemon=True).start()
    
    def _load_manga_list_thread(self, page):
        """Thread function to load manga list"""
        try:
            manga_list = self.api.search_manga(page=page, sort_by="-views")
            self.root.after(0, self._update_manga_list, manga_list)
            self.root.after(0, lambda: self.status_var.set(f"Loaded {len(manga_list)} manga"))
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
            self.root.after(0, lambda: self.status_var.set(f"Found {len(manga_list)} results"))
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
        
        self.status_var.set("Loading latest manga...")
        threading.Thread(target=self._load_latest_thread, daemon=True).start()
    
    def _load_latest_thread(self):
        """Thread function to load latest manga"""
        try:
            manga_list = self.api.search_manga(sort_by="-updated_at")
            self.root.after(0, self._update_manga_list, manga_list)
            self.root.after(0, lambda: self.status_var.set(f"Loaded {len(manga_list)} latest manga"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load latest: {e}"))
            self.root.after(0, lambda: self.status_var.set("Error loading latest"))
    
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
        self.title_label.config(text=f"Title: {details.get('title', 'Unknown')}")
        self.author_label.config(text=f"Author: {details.get('author', 'Unknown')}")
        self.status_label.config(text=f"Status: {details.get('status', 'Unknown')}")
        self.genres_label.config(text=f"Genres: {details.get('genres', 'Unknown')}")
        
        # Update description
        self.desc_text.delete('1.0', tk.END)
        self.desc_text.insert('1.0', details.get('description', 'No description available'))
        
        # Update chapter list
        self.chapter_listbox.delete(0, tk.END)
        for chapter in chapters:
            display_text = f"{chapter['name']} - {chapter.get('date', '')}"
            self.chapter_listbox.insert(tk.END, display_text)
    
    def read_selected_chapter(self):
        """Read the selected chapter"""
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a chapter to read")
            return
        
        chapter_index = selection[0]
        chapter = self.current_chapters[chapter_index]
        self.load_chapter_images(chapter)
    
    def load_chapter_images(self, chapter):
        """Load images for a chapter"""
        self.status_var.set(f"Loading chapter: {chapter['name']}")
        self.notebook.select(self.reader_frame)
        
        threading.Thread(target=self._load_chapter_images_thread, 
                        args=(chapter,), daemon=True).start()
    
    def _load_chapter_images_thread(self, chapter):
        """Thread function to load chapter images"""
        try:
            images = self.api.get_chapter_images(chapter['url'])
            self.current_images = images
            self.current_image_index = 0
            
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
        
        # Load and display image in thread
        threading.Thread(target=self._load_and_display_image, 
                        args=(self.current_images[index],), daemon=True).start()
    
    def _load_and_display_image(self, image_url):
        """Thread function to load and display image"""
        try:
            response = self.api.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Open image with PIL
            img = Image.open(io.BytesIO(response.content))
            
            # Resize if too large
            max_width = 900
            max_height = 700
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update canvas
            self.root.after(0, self._update_image_canvas, photo, img.size)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error loading image: {e}"))
    
    def _update_image_canvas(self, photo, size):
        """Update the image canvas with new image"""
        self.image_canvas.delete("all")
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.image_canvas.image = photo  # Keep reference
        self.image_canvas.config(scrollregion=(0, 0, size[0], size[1]))
    
    def prev_image(self):
        """Go to previous image"""
        if self.current_image_index > 0:
            self.display_image(self.current_image_index - 1)
    
    def next_image(self):
        """Go to next image"""
        if self.current_image_index < len(self.current_images) - 1:
            self.display_image(self.current_image_index + 1)
    
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
        
        self.add_chapters_to_download_queue(self.current_chapters)
    
    def download_current_chapter(self):
        """Download the currently reading chapter"""
        if not self.current_images:
            messagebox.showwarning("No Chapter", "No chapter is currently loaded")
            return
        
        # Find current chapter
        # This is simplified - in production, you'd track which chapter is being read
        messagebox.showinfo("Download", "Downloading current chapter...")
        # Implementation would go here
    
    def add_chapters_to_download_queue(self, chapters):
        """Add chapters to download queue"""
        if not self.current_manga:
            return
        
        manga_title = self.current_manga.get('title', 'Unknown')
        
        for chapter in chapters:
            download_item = {
                'manga': manga_title,
                'chapter': chapter,
                'status': 'Queued',
                'progress': '0/0'
            }
            self.download_queue.append(download_item)
            
            # Add to tree
            self.download_tree.insert('', 'end', 
                                     values=(manga_title, chapter['name'], 
                                           '0/0', 'Queued'))
        
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
            item = self.download_queue[0]
            
            try:
                # Get chapter images
                images = self.api.get_chapter_images(item['chapter']['url'])
                
                # Create download directory
                download_path = Path(self.download_path_var.get())
                manga_dir = download_path / self._sanitize_filename(item['manga'])
                chapter_dir = manga_dir / self._sanitize_filename(item['chapter']['name'])
                chapter_dir.mkdir(parents=True, exist_ok=True)
                
                # Download images
                for i, img_url in enumerate(images):
                    # Update progress
                    progress = f"{i+1}/{len(images)}"
                    self.root.after(0, self._update_download_progress, 0, progress, "Downloading")
                    
                    # Download image
                    img_path = chapter_dir / f"page_{i+1:03d}.jpg"
                    self.api.download_image(img_url, img_path)
                
                # Mark as completed
                self.root.after(0, self._update_download_progress, 0, f"{len(images)}/{len(images)}", "Completed")
                
            except Exception as e:
                self.root.after(0, self._update_download_progress, 0, "Error", str(e))
            
            self.download_queue.pop(0)
        
        self.is_downloading = False
    
    def _update_download_progress(self, index, progress, status):
        """Update download progress in the tree"""
        items = self.download_tree.get_children()
        if index < len(items):
            item = items[index]
            values = list(self.download_tree.item(item)['values'])
            values[2] = progress
            values[3] = status
            self.download_tree.item(item, values=values)
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for filesystem"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        return filename.strip()
    
    def clear_completed_downloads(self):
        """Clear completed downloads from the list"""
        items = self.download_tree.get_children()
        for item in items:
            values = self.download_tree.item(item)['values']
            if values[3] == "Completed":
                self.download_tree.delete(item)
    
    def browse_download_path(self):
        """Browse for download directory"""
        path = filedialog.askdirectory(title="Select Download Directory")
        if path:
            self.download_path_var.set(path)
    
    def open_download_folder(self):
        """Open the download folder in file explorer"""
        path = Path(self.download_path_var.get())
        if path.exists():
            if os.name == 'nt':  # Windows
                os.startfile(path)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{path}"' if sys.platform == 'darwin' else f'xdg-open "{path}"')
        else:
            messagebox.showwarning("Not Found", "Download folder does not exist")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = MangaViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()