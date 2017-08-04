# coding:utf-8

"""
壁纸抓取
URL:http://wallpaperswide.com/latest_wallpapers.html
"""
import re
from urlparse import urljoin
import requests
from w3lib.encoding import html_to_unicode
from bs4 import Tag, BeautifulSoup


class WallPaperMod(object):
    def __init__(self):
        self.title = ""
        self.desc = ""
        self.author = ""
        self.pb_time = ""
        self.ori_page_url = ""
        self.thumb1 = ""
        self.thumb2 = ""
        self.default = ""
        self.cate_1 = ""
        self.cate_2 = ""
        self.tags = ""
        self.score = 0
        self.n_download = 0
        self.n_like = 0

    def to_dict(self):
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d):
        self = cls()
        for k, v in d.items():
            self.__dict__[k] = v


class BaseParser(object):
    @classmethod
    def download(cls, url):
        resp = requests.get(url)
        return resp.content

    @classmethod
    def find_tag(cls, root, param):
        if not isinstance(root, (Tag, BeautifulSoup)):
            return None
        method = param.get("method", "find")
        params = param["params"]
        nth = param.get("nth", 0)
        if method == "find":
            tag = root.find(**params)
            return tag
        elif method == "find_all":
            tags = root.find_all(**params)
        elif method == "select":
            tags = root.select(**params)
        else:
            raise ValueError("param['method'] only support find, find_all and select")
        return tags[nth] if len(tags) > nth else None

    @classmethod
    def find_tags(cls, root, param):
        if not isinstance(root, (Tag, BeautifulSoup)):
            return []
        method = param.get("method", "find_all")
        params = param["params"]
        if method == "find":
            tag = root.find(**params)
            if tag is None:
                return []
            else:
                return [tag]
        elif method == "find_all":
            tags = root.find_all(**params)
        elif method == "select":
            tags = root.select(**params)
        else:
            raise ValueError("param['method'] only support find, find_all and select")
        return tags

    @classmethod
    def extract_tag_attribute(cls, root, name="text"):
        if root is None:
            return ""
        assert isinstance(root, (Tag, BeautifulSoup))
        if name == "text":
            return root.get_text().strip()
        else:
            value = root.get(name, "")
            if isinstance(value, (list, tuple)):
                return ",".join(value)
            else:
                return value.strip()

    @classmethod
    def find_extract_tag_attribute(cls, tag, params):
        if params.get("params"):
            tag = cls.find_tag(tag, params)
        attribute = params.get("attribute", "text")
        return cls.extract_tag_attribute(tag, attribute)


class WPCateUpdater(BaseParser):
    def update_cate(cls):
        pass


class WPDetailParser(BaseParser):
    TITLE = re.compile('<h3>Download(.*?)wallpaper</h3>')
    SCORE = re.compile('\((\d+) votes\)')
    AUTHOR = re.compile('>(.*?)</a> <meta itemprop="author"')
    DESC = re.compile('<b>Description:</b>(.*?)<br />')

    @classmethod
    def parse(cls, url):
        wallpaper = WallPaperMod()
        content = cls.download(url)

    @classmethod
    def get_title(cls, soup):
        title = cls.TITLE.findall(str(soup))
        if not title:
            title = ""
        else:
            title = title[0].strip()
        return title

    @classmethod
    def get_desc(cls, soup):
        desc = cls.DESC.findall(str(soup))
        if not desc:
            desc = ""
        else:
            desc = desc[0].strip()
        return desc

    @classmethod
    def get_author(cls, soup):
        author = cls.AUTHOR.findall(str(soup))
        if not author:
            author = "佚名"
        else:
            author = author[0].strip()
        return author

    @classmethod
    def get_cates(cls, soup):
        pass

    @classmethod
    def get_tags(cls, soup):
        pass

    @classmethod
    def get_score(cls, soup):
        score = cls.SCORE.findall(str(soup))
        if not score:
            score = 0
        else:
            score = int(score[0])
        return score

    @classmethod
    def get_thumb(cls, soup):
        pass


class WPListParser(BaseParser):
    tags_selector = "li.wall"
    TITLE = {"params": {"selector": "h1"}, "method": "select"}
    DETAIL_URL = {"attribute": "href", "params": {"selector": "div#hudtitle > a"}, "method": "select"}
    N_VIEW_DOWN = re.compile('<em>(\d+) views \| (\d+) downloads</em>')
    THUMB = {"attribute": "src", "params": {"selector": "img.thumb_img"}, "method": "select"}
    URL = ""

    @classmethod
    def parse(cls, url):
        cls.URL = url
        item_list = list()
        content = cls.download(url)
        tags = cls.get_tags(content)
        for tag in tags:
            meta = dict()
            meta["title"] = cls.get_title(tag)
            meta["detail_url"] = cls.get_detail_url(tag)
            meta["n_view"], meta["down"] = cls.get_n_view_down(tag)
            meta["n_thumb"] = cls.get_thumb(tag)
            item_list.append(meta)
        return item_list

    @classmethod
    def get_title(cls, soup):
        title = cls.find_extract_tag_attribute(soup, cls.TITLE)
        return title

    @classmethod
    def get_thumb(cls, soup):
        thumb = cls.find_extract_tag_attribute(soup, cls.THUMB)
        urljoin(cls.URL, thumb)
        return thumb

    @classmethod
    def get_n_view_down(cls, soup):
        n = cls.N_VIEW_DOWN.findall(str(soup))
        if not n:
            n_view = 0
            n_down = 0
        else:
            n_view, n_down = n[0]
        return int(n_view), int(n_down)

    @classmethod
    def get_detail_url(cls, soup):
        detail_url = cls.find_extract_tag_attribute(soup, cls.DETAIL_URL)
        detail_url = urljoin(cls.URL, detail_url)
        return detail_url

    @classmethod
    def get_tags(cls, document):
        soup = BeautifulSoup(document, "lxml")
        tags = soup.select(selector=cls.tags_selector)
        return tags


class WPTask(object):
    last_url = "http://wallpaperswide.com/latest_wallpapers.html"

    @classmethod
    def update_cate(cls):
        pass

    @classmethod
    def check_all(cls):
        pass

    @classmethod
    def get_all(cls):
        pass

    @classmethod
    def day(cls):
        for i in WPListParser.parse(cls.last_url):
            print i


if __name__ == "__main__":
    WPTask.day()
