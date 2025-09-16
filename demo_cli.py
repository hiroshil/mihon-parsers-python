#!/usr/bin/env python3
"""
Command-line demo for LxHentai API
Can run without Tkinter to test functionality
"""

import sys
import os
from pathlib import Path

# Import API from fixed version
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_fixed_api import LxHentaiAPIStandalone


def print_menu():
    """Print main menu"""
    print("\n" + "=" * 50)
    print("LXHENTAI MANGA DOWNLOADER - CLI DEMO")
    print("=" * 50)
    print("1. Browse Popular Manga")
    print("2. Search Manga")
    print("3. View Manga Details")
    print("4. List Chapters")
    print("5. Download Chapter")
    print("6. Toggle Mock Data Mode")
    print("0. Exit")
    print("-" * 50)


def browse_popular(api):
    """Browse popular manga"""
    print("\nLoading popular manga...")
    manga_list = api.search_manga(sort_by="-views")
    
    if not manga_list:
        print("No manga found!")
        return None
    
    print(f"\nFound {len(manga_list)} manga:")
    print("-" * 40)
    
    for i, manga in enumerate(manga_list, 1):
        print(f"{i}. {manga['title']}")
    
    return manga_list


def search_manga(api):
    """Search for manga"""
    query = input("\nEnter search query: ").strip()
    if not query:
        return None
    
    print(f"\nSearching for '{query}'...")
    manga_list = api.search_manga(query=query)
    
    if not manga_list:
        print("No results found!")
        return None
    
    print(f"\nFound {len(manga_list)} results:")
    print("-" * 40)
    
    for i, manga in enumerate(manga_list, 1):
        print(f"{i}. {manga['title']}")
    
    return manga_list


def view_details(api, manga_url):
    """View manga details"""
    print(f"\nLoading manga details...")
    details = api.get_manga_details(manga_url)
    
    if not details:
        print("Failed to load details!")
        return
    
    print("\n" + "=" * 50)
    print(f"Title: {details.get('title', 'Unknown')}")
    print(f"Author: {details.get('author', 'Unknown')}")
    print(f"Status: {details.get('status', 'Unknown')}")
    print(f"Genres: {details.get('genres', 'Unknown')}")
    print("-" * 50)
    print("Description:")
    desc = details.get('description', 'No description available')
    # Wrap long description
    words = desc.split()
    line = ""
    for word in words:
        if len(line) + len(word) > 70:
            print(line)
            line = word
        else:
            line = line + " " + word if line else word
    if line:
        print(line)
    print("=" * 50)


def list_chapters(api, manga_url):
    """List chapters of a manga"""
    print(f"\nLoading chapters...")
    chapters = api.get_chapter_list(manga_url)
    
    if not chapters:
        print("No chapters found!")
        return None
    
    print(f"\nFound {len(chapters)} chapters:")
    print("-" * 40)
    
    # Show first 10 and last 10 if more than 20
    if len(chapters) > 20:
        for i, chapter in enumerate(chapters[:10], 1):
            print(f"{i}. {chapter['name']}")
        print("...")
        for i, chapter in enumerate(chapters[-10:], len(chapters)-9):
            print(f"{i}. {chapter['name']}")
    else:
        for i, chapter in enumerate(chapters, 1):
            print(f"{i}. {chapter['name']}")
    
    return chapters


def download_chapter(api, chapter_url, chapter_name, manga_title):
    """Download a chapter"""
    print(f"\nDownloading: {chapter_name}")
    
    # Get images
    images = api.get_chapter_images(chapter_url)
    if not images:
        print("No images found!")
        return
    
    # Create download directory
    download_dir = Path.home() / "Downloads" / "LxHentai_CLI" / manga_title / chapter_name
    download_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading {len(images)} pages to: {download_dir}")
    print("-" * 40)
    
    success = 0
    for i, img_url in enumerate(images, 1):
        print(f"Downloading page {i}/{len(images)}...", end=" ")
        
        img_path = download_dir / f"page_{i:03d}.jpg"
        if api.download_image(img_url, str(img_path)):
            print("✓")
            success += 1
        else:
            print("✗")
    
    print("-" * 40)
    print(f"Download complete! {success}/{len(images)} pages saved.")
    print(f"Location: {download_dir}")


def main():
    """Main CLI application"""
    # Start with mock data by default
    use_mock = True
    api = LxHentaiAPIStandalone(use_mock_data=use_mock)
    
    current_manga = None
    current_manga_url = None
    
    print("\n" + "🎌" * 25)
    print("Welcome to LxHentai Manga Downloader CLI!")
    print("Starting in Mock Data Mode (no server connection needed)")
    print("🎌" * 25)
    
    while True:
        print_menu()
        
        if use_mock:
            print("📌 Currently using: MOCK DATA MODE")
        else:
            print("📌 Currently using: REAL API MODE")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            print("\nGoodbye! 👋")
            break
            
        elif choice == "1":
            manga_list = browse_popular(api)
            if manga_list:
                try:
                    selection = input("\nSelect manga number (or Enter to go back): ").strip()
                    if selection and selection.isdigit():
                        idx = int(selection) - 1
                        if 0 <= idx < len(manga_list):
                            current_manga = manga_list[idx]
                            current_manga_url = current_manga['url']
                            view_details(api, current_manga_url)
                except (ValueError, IndexError):
                    print("Invalid selection!")
                    
        elif choice == "2":
            manga_list = search_manga(api)
            if manga_list:
                try:
                    selection = input("\nSelect manga number (or Enter to go back): ").strip()
                    if selection and selection.isdigit():
                        idx = int(selection) - 1
                        if 0 <= idx < len(manga_list):
                            current_manga = manga_list[idx]
                            current_manga_url = current_manga['url']
                            view_details(api, current_manga_url)
                except (ValueError, IndexError):
                    print("Invalid selection!")
                    
        elif choice == "3":
            if current_manga_url:
                view_details(api, current_manga_url)
            else:
                print("\nNo manga selected! Browse or search first.")
                
        elif choice == "4":
            if current_manga_url:
                chapters = list_chapters(api, current_manga_url)
                if chapters:
                    try:
                        selection = input("\nSelect chapter to download (or Enter to go back): ").strip()
                        if selection and selection.isdigit():
                            idx = int(selection) - 1
                            if 0 <= idx < len(chapters):
                                chapter = chapters[idx]
                                manga_title = current_manga['title'].replace('[Mock Data]', '').strip()
                                download_chapter(api, chapter['url'], chapter['name'], manga_title)
                    except (ValueError, IndexError):
                        print("Invalid selection!")
            else:
                print("\nNo manga selected! Browse or search first.")
                
        elif choice == "5":
            if current_manga_url:
                chapters = list_chapters(api, current_manga_url)
                if chapters:
                    # Download first chapter as demo
                    chapter = chapters[0]
                    manga_title = current_manga['title'].replace('[Mock Data]', '').strip()
                    download_chapter(api, chapter['url'], chapter['name'], manga_title)
            else:
                print("\nNo manga selected! Browse or search first.")
                
        elif choice == "6":
            use_mock = not use_mock
            api = LxHentaiAPIStandalone(use_mock_data=use_mock)
            mode = "MOCK DATA MODE" if use_mock else "REAL API MODE"
            print(f"\nSwitched to: {mode}")
            if not use_mock:
                print("Note: Real API may not work due to Cloudflare protection")
                
        else:
            print("\nInvalid choice! Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye! 👋")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("The application will now exit.")