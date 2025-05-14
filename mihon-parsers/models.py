from typing import Dict, Optional, Any

class SChapter:
    def __init__(self):
        self.url = ""
        self.name = ""
        self.date_upload = 0
        self.chapter_number = 0.0
        self.scanlator = None

    def to_chapter_info(self):
        return {
            "dateUpload": self.date_upload,
            "key": self.url,
            "name": self.name,
            "number": self.chapter_number,
            "scanlator": self.scanlator or ""
        }

    @staticmethod
    def from_chapter_info(chapter_info: Dict[str, Any]):
        chapter = SChapter()
        chapter.url = chapter_info["key"]
        chapter.name = chapter_info["name"]
        chapter.date_upload = chapter_info["dateUpload"]
        chapter.chapter_number = chapter_info["number"]
        chapter.scanlator = chapter_info["scanlator"]
        return chapter


class SManga:
    def __init__(self):
        self.url = ""
        self.title = ""
        self.artist = None
        self.author = None
        self.description = None
        self.genre = None
        self.status = 0
        self.thumbnail_url = None
        self.update_strategy = 0
        self.initialized = False

    STATUS_UNKNOWN = 0
    STATUS_ONGOING = 1
    STATUS_COMPLETED = 2
    STATUS_LICENSED = 3
    STATUS_PUBLISHING_FINISHED = 4
    STATUS_CANCELLED = 5
    STATUS_ON_HIATUS = 6
    STATUS_RECOMMENDS = 69

    def to_manga_info(self):
        return {
            "key": self.url,
            "title": self.title,
            "artist": self.artist or "",
            "author": self.author or "",
            "description": self.description or "",
            "genres": self.genre.split(", ") if self.genre else [],
            "status": self.status,
            "cover": self.thumbnail_url or ""
        }

    @staticmethod
    def from_manga_info(manga_info: Dict[str, Any]):
        manga = SManga()
        manga.url = manga_info["key"]
        manga.title = manga_info["title"]
        manga.artist = manga_info["artist"]
        manga.author = manga_info["author"]
        manga.description = manga_info["description"]
        manga.genre = ", ".join(manga_info["genres"])
        manga.status = manga_info["status"]
        manga.thumbnail_url = manga_info["cover"]
        return manga


class Page:
    def __init__(self, index: int, url: str = "", imageUrl: Optional[str] = None):
        self.index = index
        self.url = url
        self.imageUrl = imageUrl
        self.status = 0  # 0: QUEUE, 1: LOAD_PAGE, 2: DOWNLOAD_IMAGE, 3: READY, 4: ERROR
        self.progress = 0

    def to_page_url(self):
        return {"url": self.imageUrl or self.url}

    @staticmethod
    def from_page_url(page_url: Dict[str, str], index: int):
        return Page(index, imageUrl=page_url["url"])


class Filter:
    pass


class FilterList(list):
    def __init__(self, *filters: Filter):
        super().__init__(filters)

