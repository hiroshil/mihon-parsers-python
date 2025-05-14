from datetime import datetime

class ChapterDto:
    def __init__(self, post_modified: str, post_title: str, chap_link: str, member_type: str, **kwargs):
        self.post_modified = post_modified
        self.post_title = post_title
        self.chap_link = chap_link
        self.member_type = member_type

    def to_schapter(self):
        chapter = SChapter()
        chapter.url = f"/{self.chap_link}"
        chapter.name = self.post_title
        if self.member_type.strip():
            chapter.name += f" ({self.member_type})"
        chapter.date_upload = int(
            datetime.strptime(self.post_modified, "%Y-%m-%d %H:%M:%S").timestamp()
        )
        return chapter


class PageDto:
    def __init__(self, src: str, media: str):
        self.src = src
        self.media = media