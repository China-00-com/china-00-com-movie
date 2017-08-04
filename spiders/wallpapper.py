# coding:utf-8

"""
壁纸抓取
URL:http://wallpaperswide.com/latest_wallpapers.html
"""

import requests


def download(url):
    resp = requests.get(url)
    return resp.content


class WallPaperMod(object):
    def __init__(self):
        self.title = ""
        self.desc = ""
        self.author = ""
        self.pb_time = ""
        self.thumb = ""
        self.default = ""
        self.cate_1 = ""
        self.cate_2 = ""
        self.tags = ""
        self.score = 0
        self.n_download = 0
        self.n_like = 0
        self.related = list()

    def to_dict(self):
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d):
        self = cls()
        for k, v in d.items():
            self.__dict__[k] = v


class BaseParser(object):
    pass


class WPCateUpdater(BaseParser):
    def update_cate(cls):
        pass


class WPDetailParser(BaseParser):
    @classmethod
    def parse_detail(cls):
        pass


class WPListParser(BaseParser):
    @classmethod
    def parse_list(cls):
        pass


class WPTask(object):
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
        pass


if __name__ == "__main__":
    TASK_MAP = {

    }
