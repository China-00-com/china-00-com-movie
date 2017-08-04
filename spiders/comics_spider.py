# coding:utf-8

"""邪恶漫画解析"""

# coding:utf-8
from urllib import quote
from pymongo import MongoClient

NEW_USER = "username"
NEW_PASSWORD = quote("password")
NEW_HOST_PORT = "ip:port"
NEW_DATABASE = "db_name"
NEW_MONGO_URL = "mongodb://{0}:{1}@{2}/{3}".format(NEW_USER, NEW_PASSWORD, NEW_HOST_PORT, NEW_DATABASE)
MONGO_URL = NEW_MONGO_URL
client_p = MongoClient(host=MONGO_URL, maxPoolSize=1, minPoolSize=1)
db_p = client_p.get_default_database()

# coding:utf-8
"""
工具函数：
    1.图片数据上传OSS
"""
import json
import uuid
import oss2
from datetime import datetime
from bs4 import Tag, BeautifulSoup

access_key_id = ""
access_key_secret = ""
auth = oss2.Auth(access_key_id, access_key_secret)
region = "oss-url"
name = "group-name"
bucket = oss2.Bucket(auth, region, name)


def upload_file_to_oss(data):
    """上传图片到oss"""
    target_name = str(uuid.uuid1().hex) + ".jpg"
    try:
        respond = bucket.put_object(target_name, data)
    except Exception as e:
        logging.warning(e)
        logging.warning("upload image exception")
        return False
    if respond.status != 200:
        logging.info("upload image to oss error: %s" % respond.status)
        return False
    pic_url = '///' + target_name
    return pic_url


class ExtractTool(object):
    base_conf = {"attribute": "text", "params": {"selector": "COMMIC-SPIDER"}, "method": "select"}

    @staticmethod
    def find_tag(root, param):
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

    @staticmethod
    def find_tags(root, param):
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

    @staticmethod
    def extract_tag_attribute(root, name="text"):
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


def format_time(t=None):
    f = "%Y-%m-%d %H:%M:%S"
    if t is None:
        return datetime.utcnow()
    try:
        result = datetime.strptime(t, f)
    except Exception:
        result = datetime.utcnow()
    return result


import json
import re
import logging
import requests
from w3lib.encoding import html_to_unicode
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from bs4 import Tag, BeautifulSoup
from urlparse import urljoin


class Chapter(object):
    def __init__(self):
        self.title = ""
        self.cover_pic = ""
        self.pic_nums = 0
        self.pics = []
        self.ori_url = ""


class Book(object):
    def __init__(self):
        self.name = ""
        self.cover_pic = ""
        self.description = ""
        self.pic_nums = 0
        self.chap_nums = 0
        self.chapters = []
        self.ori_url = ""


class SpiderBase(object):
    headers = {
        "user-agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                       " (KHTML, like Gecko) Chrome/50.0.2661.86 Safari/537.36")}
    timeout = 30
    r_json = False
    PB_SITE = ""
    book_info_conf = {
        "name": ExtractTool.base_conf,
        "cover_pic": ExtractTool.base_conf,
        "description": ExtractTool.base_conf
    }
    chap_list_conf = {
        "title": ExtractTool.base_conf,
        "cover_pic": ExtractTool.base_conf,
        "url": ExtractTool.base_conf,
        "list": ExtractTool.base_conf
    }
    detail_conf = {
        "pic": ExtractTool.base_conf
    }

    @classmethod
    def download(cls, url, c_json=False, skip=None, headers=None):
        if headers is None:
            headers = cls.headers
        response = requests.get(url, headers=headers,
                                timeout=(10, cls.timeout))
        content = response.content
        if skip:
            content = content[skip[0]:skip[1]]
        if c_json:
            return json.loads(content)
        else:
            _, content = html_to_unicode(
                content_type_header=response.headers.get("content-type"),
                html_body_str=content
            )
            return content.encode("utf-8")

    @classmethod
    def download_pic(cls, url, headers=None):
        count = 0
        flag = False
        content = None
        while count > 3 or flag:
            try:
                req = requests.get(url, headers=headers)
                content = req.content
            except Exception as e:
                count += 1
            else:
                flag = True
        return content

    @classmethod
    def get_book_info(cls, book_url):
        book = Book()
        book.ori_url = book_url
        document = cls.download(book_url)
        soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
        book.name = ExtractTool.find_extract_tag_attribute(soup, cls.book_info_conf["name"])
        book.cover_pic = ExtractTool.find_extract_tag_attribute(soup, cls.book_info_conf["cover_pic"])
        book.cover_pic = urljoin(book_url, book.cover_pic)
        book.description = ExtractTool.find_extract_tag_attribute(soup, cls.book_info_conf["description"])
        if book.name and book.cover_pic:
            return book
        else:
            raise Exception("BOOK-INFO:未能正常解析")

    @classmethod
    def gen_pages_url(cls, book_url):
        return [book_url]

    @classmethod
    def get_chap_list(cls, book_url):
        """
        返回 /标题，封面，url/列表
        :param book_url:
        :return:
        """
        pages = cls.gen_pages_url(book_url)
        chaps = []
        for page in pages:
            document = cls.download(page)
            soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
            tags = ExtractTool.find_tags(soup, cls.chap_list_conf["list"])
            for tag in tags:
                chap = Chapter()
                chap.title = ExtractTool.find_extract_tag_attribute(tag, cls.chap_list_conf["title"])
                chap.cover_pic = ExtractTool.find_extract_tag_attribute(tag, cls.chap_list_conf["cover_pic"])
                chap.cover_pic = urljoin(book_url, chap.cover_pic)
                chap.ori_url = ExtractTool.find_extract_tag_attribute(tag, cls.chap_list_conf["url"])
                chap.ori_url = urljoin(book_url, chap.ori_url)
                chaps.append(chap)
        chaps.reverse()
        return chaps

    @classmethod
    def get_chap_detail(cls, chap_url):
        """
        返回 /返回图片地址列表/
        :param chap_url:
        :return:
        """
        document = cls.download(chap_url)
        soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
        tags = ExtractTool.find_tags(soup, cls.detail_conf["pic"])
        pics = []
        for tag in tags:
            param = {"attribute": "src", "params": {"selector": "img"}, "method": "select"}
            pic = ExtractTool.find_extract_tag_attribute(tag, param)
            pic = urljoin(chap_url, pic)
            pics.append(pic)
        return pics

    @classmethod
    def obj_to_doc(cls, obj):
        doc = dict()
        doc["name"] = obj.name
        doc["cover_pic"] = obj.cover_pic
        doc["description"] = obj.description
        doc["pic_nums"] = obj.pic_nums
        doc["chap_nums"] = obj.chap_nums
        doc["ori_url"] = obj.ori_url
        doc["chapters"] = []
        for chapter in obj.chapters:
            chap = dict()
            chap["title"] = chapter.title
            chap["cover_pic"] = chapter.cover_pic
            chap["pic_nums"] = chapter.pic_nums
            chap["ori_url"] = chapter.ori_url
            chap["pics"] = chapter.pics
            doc["chapters"].append(chap)
        doc["update_time"] = format_time()
        return doc

    @classmethod
    def store(cls, book):
        book_doc = cls.obj_to_doc(book)
        try:
            db_p.wudi_comics.insert(book_doc)
        except DuplicateKeyError as e:
            pass
        except Exception as e:
            logging.warning(e)

    @classmethod
    def show(cls, book):
        print "name:", book.name
        print "cover:", book.cover_pic
        print "chap_nums:", book.chap_nums
        print "pic_nums:", book.pic_nums
        for num, chap in enumerate(book.chapters):
            print num, chap.title, chap.cover_pic
            for pic in chap.pics:
                print pic

    @classmethod
    def process_pic(cls, book):
        raise NotImplemented

    @classmethod
    def special(cls, book):
        return book

    @classmethod
    def run(cls, book_url):
        book = cls.get_book_info(book_url)
        chap_list = cls.get_chap_list(book.ori_url)
        for chap in chap_list:
            pic_list = cls.get_chap_detail(chap.ori_url)
            pic_nums = len(pic_list)
            chap.pics.extend(pic_list)
            chap.pic_nums = pic_nums
            book.pic_nums += pic_nums
            book.chap_nums += 1
        book.chapters.extend(chap_list)
        book = cls.special(book)
        cls.store(book)
        cls.show(book)


class PapabaSpider_V1(SpiderBase):
    PB_SITE = u"福利啪啪吧"
    book_info_conf = {
        "name": {"params": {"selector": "div.title > h1"}, "method": "select"},
        "cover_pic": {"attribute": "src", "params": {"selector": "div#listfocus img"}, "method": "select"},
        "description": ExtractTool.base_conf,
    }
    chap_list_conf = {
        "title": {"attribute": "title", "params": {"selector": "a"}, "method": "select"},
        "cover_pic": {"attribute": "xsrc", "params": {"selector": "img"}, "method": "select"},
        "url": {"attribute": "href", "params": {"selector": "a"}, "method": "select"},
        "list": {"params": {"selector": "div.mainleft > ul.piclist.listcon > li"}, "method": "select"}
    }
    detail_conf = {
        "pic": {"params": {"selector": "li#imgshow"}, "method": "select"},
    }

    @classmethod
    def gen_pages_url(cls, book_url):
        url = book_url + "list_%s_%s.html"
        pages_url = []
        document = cls.download(book_url)
        soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
        page_conf = {"attribute": "href", "params": {"selector": "ul.pagelist li > a"}, "method": "select"}
        tags = ExtractTool.find_tags(soup, page_conf)
        try:
            last_page = str(list(tags)[-1])
        except:
            pages_url.append(book_url)
        else:
            result = re.findall(r"list_(\d+)_(\d+)\.html", last_page)[0]
            num = result[0]
            pages = result[1]
            for page in range(int(pages)):
                pages_url.append(url % (num, page + 1))
        print pages_url
        return pages_url


class PapabaSpider_V2(PapabaSpider_V1):
    chap_list_conf = {
        "title": {"attribute": "title", "params": {"selector": "a"}, "method": "select"},
        "cover_pic": ExtractTool.base_conf,
        "url": {"attribute": "href", "params": {"selector": "a"}, "method": "select"},
        "list": {"params": {"selector": "div#jishu > div.item"}, "method": "select"}
    }


class xmchkjSpider(SpiderBase):
    PB_SITE = u"酷乐吧"
    chap_list_conf = {
        "title": {"attribute": "title", "method": "select"},
        "cover_pic": {"attribute": "href", "method": "select"},
        "url": {"attribute": "href", "method": "select"},
        "list": {"params": {"selector": "div.article_comic_list > ul > a"}, "method": "select"}
    }
    detail_conf = {
        "pic": {"params": {"selector": "div.comic_pic_box"}, "method": "select"},
    }


class Cuntuba520Spider(SpiderBase):
    PB_SITE = u"寸土吧"
    chap_list_conf = {
        "title": {"attribute": "title", "method": "select"},
        "cover_pic": {"attribute": "href", "method": "select"},
        "url": {"attribute": "href", "method": "select"},
        "list": {"params": {"selector": "div.article_comic_list > ul > a"}, "method": "select"}
    }
    detail_conf = {
        "pic": {"params": {"selector": "div.comic_pic_box"}, "method": "select"},
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        filename="wudi_comics.log",
                        filemode="a+")
    PapabaSpider_V1.run("http://www.papaba.cc/lezhangburu/")
