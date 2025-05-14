import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List
from urllib.parse import urljoin
import random
from ...models import SChapter, SManga, Page, FilterList
from .xxmanhwadto import ChapterDto, PageDto



class XxManhwa:
    def __init__(self):
        self.name = "XXManhwa"
        self.lang = "vi"
        self.default_base_url = "https://google.xxmanhwa2.top"
        self.base_url = self.default_base_url
        self.headers = {
            "Referer": self.base_url + "/"
        }
        self.preferences = {
            "KEY_HIDE_PAID_CHAPTERS": False,
            "BASE_URL_PREF": self.default_base_url
        }

    def popular_manga_request(self, page: int) -> str:
        return f"{self.base_url}/tat-ca-cac-truyen?page_num={page}"

    def popular_manga_selector(self) -> str:
        return "div[data-type=story]"

    def popular_manga_from_element(self, element: BeautifulSoup) -> SManga:
        manga = SManga()
        a_tag = element.select_one("a")
        manga.url = a_tag["href"]
        manga.title = a_tag["title"]
        img_div = element.select_one("div.posts-list-avt")
        manga.thumbnail_url = img_div["data-img"] if img_div else None
        return manga

    def search_manga_request(self, page: int, query: str, filters: FilterList) -> str:
        url = f"{self.base_url}/search"
        params = {
            "page_num": page,
            "s": query,
            "post_type": "story"
        }
        return f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def search_manga_selector(self) -> str:
        return self.popular_manga_selector()

    def search_manga_from_element(self, element: BeautifulSoup) -> SManga:
        return self.popular_manga_from_element(element)

    def manga_details_parse(self, response: requests.Response) -> SManga:
        soup = BeautifulSoup(response.text, "html.parser")
        manga = SManga()
        manga.title = soup.select_one("h1").text.strip()
        summary = soup.select_one(".story-details-content p")
        manga.description = summary.text.strip() if summary else ""
        
        img_tag = soup.select_one("div.col-inner.img-max-width img")
        manga.thumbnail_url = img_tag["src"] if img_tag else None
        
        genre_map_html = next((script_tag for script_tag in soup.select("script") if 'StoryType_CAT' in script_tag.text), '')
        genre_map_data = genre_map_html.text.split("'cat_story': [")[1].split("],")[0]
        genre_map = json.loads(f'[{genre_map_data}]') # wrap the data in brackets
        genre_map_dict = {item["term_id"]: item["name"] for item in genre_map}
        
        taxonomy_div = soup.select_one("div[data-taxonomy]")
        if taxonomy_div:
            category_ids = taxonomy_div["data-id"].split(",")
            manga.genre = ", ".join(genre_map_dict.get(cid, "Unknown") for cid in category_ids)
        
        return manga

    def chapter_list_parse(self, response: requests.Response) -> List[SChapter]:
        chapters_html = response.text.split("var scope_data=")[1].split(";</script")[0]
        chapters_data = json.loads(chapters_html)
        print(chapters_data) # debug
        
        hide_paid = self.preferences.get("KEY_HIDE_PAID_CHAPTERS", False)
        return [
            chapter.to_schapter()
            for chapter in [ChapterDto(**item) for item in chapters_data]
            if not chapter.member_type.strip() or not hide_paid
        ]

    def page_list_parse(self, response: requests.Response) -> List[Page]:
        soup = BeautifulSoup(response.text, "html.parser")
        
        login_required = soup.select_one(".story_view_permisstion p.yellowcolor")
        if login_required:
            raise Exception(f"{login_required.text}. Please login in WebView.")
        
        wp_nonce = "e732af2390628a21d8b7500e621b1493c28d9330b415e88f27b8b4e2f9a440a3"
        
        manga_id = response.request.url.split("/")[-2]
        chapter_id = response.request.url.split("/")[-1].split("-")[0]
        
        expiry_match = re.search(r"expire:(\d+)", response.text)
        token_match = re.search(r'token:"([0-9a-f.]+)"', response.text)
        
        if not expiry_match or not token_match:
            raise Exception("Could not find token information")
        
        expiry = expiry_match.group(1)
        token = token_match.group(1)
        
        src_tag = soup.select_one("div.cur p[data-src]")
        if not src_tag:
            raise Exception("Could not get filename of first image")
        
        src = src_tag["data-src"]
        iid = ''.join(random.choices('234567abcdefghijklmnopqrstuvwxyz', k=12))
        
        form_data = {
            "iid": f"_0_{iid}",
            "ipoi": "1",
            "sid": chapter_id,
            "cid": manga_id,
            "expiry": expiry,
            "token": token,
            "src": f"/{src.split('/')[-1]}",
            "doing_ajax": "1"
        }
        
        try:
            ebe_captcha_key = response.text.split("action_ebe_captcha('")[1].split("')")[0]
            captcha_url = f"{self.base_url}/{ebe_captcha_key}?_wpnonce={wp_nonce}"
            
            captcha_response = requests.post(captcha_url, data={"nse": str(random.random())})
            captcha_soup = BeautifulSoup(captcha_response.text, "html.parser")
        except:
            captcha_soup = soup
        
        for input_tag in captcha_soup.select("input"):
            form_data[input_tag["name"]] = input_tag.get("value", "")
        
        image_request = requests.post(
            f"{self.base_url}/chaps/img",
            headers=self.headers,
            data=form_data
        )
        
        page_data = json.loads(image_request.text)
        print(page_data) # debug
        base_page_url = f"https://{page_data['media']}/{page_data['src'].split('//')[-2]}/"
        
        pages = []
        for i, p_tag in enumerate(soup.select("div.cur p[data-src]")):
            page_url = base_page_url + p_tag["data-src"].split("/")[-1]
            pages.append(Page(i, imageUrl=page_url))
        
        return pages

    def setup_preferences(self):
        """Simulate preference setup for configuration"""
        self.preferences["KEY_HIDE_PAID_CHAPTERS"] = False
        self.preferences["BASE_URL_PREF"] = self.default_base_url
