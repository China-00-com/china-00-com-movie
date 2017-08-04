# coding:utf-8

"""磁力链接实时"""

import re
import requests
from w3lib.encoding import html_to_unicode
from urlparse import urljoin
from urllib import unquote_plus, unquote
from bs4 import Tag, BeautifulSoup
from datetime import datetime, timedelta


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


def find_extract_tag_attribute(tag, params):
    if params.get("params"):
        tag = find_tag(tag, params)
    attribute = params.get("attribute", "text")
    return extract_tag_attribute(tag, attribute)


class ListItem(object):
    def __init__(self):
        self.title = ""
        self.size = ""
        self.file_type = ""
        self.last_down = ""
        self.time = ""
        self.contain = list()


class DetailItem(object):
    def __init__(self):
        self.title = ""
        self.file_type = ""
        self.file_size = ""
        self.create_time = ""
        self.hot_score = ""
        self.file_count = ""
        self.magnet_link = ""
        self.tags = ""
        self.containt = ""


class BtParser(object):
    def get_soup(self, document):
        soup = BeautifulSoup(document, "lxml")
        return soup

    def get_tags(self, soup):
        tags = soup.select(selector="div#wall > div.search-item")
        return tags

    def decode_field(self, text):
        field_text_re = re.compile('decodeURIComponent\((.*?)\);')
        regex_result = field_text_re.findall(text)
        if not regex_result:
            field_text = text
        else:
            field_text = regex_result[0]
            field_text = "".join(map(lambda x: x.strip('"'), field_text.split("+")))
            field_text = unquote(field_text)
        return field_text

    def extract_detail(self, tag):
        pass

    def run(self, document):
        pass


class ListParser(BtParser):
    def extract_detail(self, tag):
        detail_url = {"attribute": "href", "params": {"selector": "div.item-title > h3 > a"}, "method": "select"}
        title_config = {"params": {"selector": "div.item-title > h3"}, "method": "select"}
        contain_config = {"params": {"selector": "div.item-list > ul > li"}, "method": "select"}
        file_type_config = {"params": {"selector": "div.item-list > ul > li"}, "method": "select"}
        file_size_config = {"params": {"selector": "div.item-list > ul > li"}, "method": "select"}
        last_down_config = {"params": {"selector": "div.item-list > ul > li"}, "method": "select"}
        list_item = ListItem()
        list_item.title = find_extract_tag_attribute(tag, title_config)
        list_item.file_type = find_extract_tag_attribute(tag, file_type_config)
        pass

    def run(self, document):
        soup = self.get_soup(document)
        tags = self.get_tags(soup)
        for tag in tags:
            print tag


class DetailParser(BtParser):
    def extract_detail(self, tag):
        title_conf = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        file_type_conf = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        file_size = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        create_time = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        hot_score = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        file_count = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        magnet_link = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        tags = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        containt = {"attribute": "text", "params": {"selector": "h2"}, "method": "select"}
        detail_item = DetailItem()
        detail_item.title = find_extract_tag_attribute(tag, title_conf)
        pass


if __name__ == "__main__":
    document = requests.get("http://www.btwhat.net/search/%E6%88%98%E7%8B%BC2/1-2.html").content
    lp = ListParser()
    lp.run(document)

"""
btbook
runbt.cc
cloudbt
https://github.com/a52948/cloudbt
"""
