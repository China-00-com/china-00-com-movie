# coding:utf-8
"""
视频抓取脚本
"""

# coding:utf-8
"""
数据库配置
"""
from urllib import quote
from pymongo import MongoClient
DEBUG = False
# mongo
NEW_USER = "username"
NEW_PASSWORD = quote("password")
if DEBUG:
    NEW_HOST_PORT = "ip:port"
else:
    NEW_HOST_PORT = "ip:port"
NEW_DATABASE = "db_name"
NEW_MONGO_URL = "mongodb://{0}:{1}@{2}/{3}".format(NEW_USER, NEW_PASSWORD, NEW_HOST_PORT, NEW_DATABASE)
MONGO_URL = NEW_MONGO_URL
client = MongoClient(host=MONGO_URL, maxPoolSize=1, minPoolSize=1)




import random
from urlparse import urljoin
from urllib import unquote_plus
from datetime import datetime, timedelta
import json
import re
import logging
from collections import namedtuple
import requests
from w3lib.encoding import html_to_unicode
from bs4 import Tag, BeautifulSoup
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
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
def format_time(t=None):
    f = "%Y-%m-%d %H:%M:%S"
    if t is None:
        return datetime.utcnow()
    try:
        result = datetime.strptime(t, f)
    except Exception:
        result = datetime.utcnow()
    return result
class VideoBase(object):
    """
    视频抓取基类
    """
    headers = {
        "user-agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                       " (KHTML, like Gecko) Chrome/50.0.2661.86 Safari/537.36")}
    timeout = 30
    r_json = False
    PB_SITE = None
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
    def build_video(cls, task):
        video = Video()
        video.pb_site = cls.PB_SITE
        video.site = task.site_id
        video.channel = task.channel_id
        video.cname = task.cname
        video.source_id = task.source_id
        video.chid = task.chid
        video.second_chid = task.second_chid
        return video
    @classmethod
    def parse(cls, document, task):
        raise NotImplementedError
    @classmethod
    def run(cls, task):
        url = task.url
        document = cls.download(url, c_json=cls.r_json)
        videos = cls.parse(document, task)
        logging.info("%s: %s" % (cls.__name__, len(videos)))
        return videos
class Video(object):
    """
    视频对象
    """
    def __init__(self):
        self.title = None
        self.pb_time = None
        self.pb_site = None
        self.pb_url = None
        self.author = None
        self.avatar = None
        self.insert = datetime.utcnow()
        self.site = None
        self.channel = None
        self.cname = None
        self.c_type = "mp4"
        self.c_src = None
        self.c_thumbnail = None
        self.c_duration = 0
        self.source_id = None
        self.chid = None
        self.second_chid = None
        self.style = 6
        self.rtype = 6
    def show(self):
        print "title: %s" % self.title
        print "pb_time: %s" % self.pb_time
        print "pb_site: %s" % self.pb_site
        print "site: %s" % self.site
        print "channel: %s" % self.channel
        print "pb_url: %s" % self.pb_url
        print "author: %s" % self.author
        print "avatar: %s" % self.avatar
        print "insert: %s" % self.insert
        print "c_type: %s" % self.c_type
        print "c_src: %s" % self.c_src
        print "c_thumbnail: %s " % self.c_thumbnail
        print "c_duration: % s " % self.c_duration
        print "*" * 120
class StoreVideo(object):
    """
    视频存储类，用于对爬取解析的数据进行多种形式的存储
    """
    db = client.get_default_database()
    collection = db.videos
    UPLOAD_URL = "http://10.25.60.218:8081/api/store/video"
    RELATE_URL = "http://10.25.60.218:8081/search/relate/video"
    def upload_to_mongodb(self, video):
        """
        上传至MONGO数据库，直接通过数据库驱动进行操作
        :param video:
        :return:
        """
        document = dict()
        document["title"] = video.title
        document["pb_time"] = video.pb_time
        document["insert"] = video.insert
        document["pb_site"] = video.pb_site
        document["cname"] = video.cname
        document["pb_url"] = video.pb_url
        document["author"] = video.author
        document["avatar"] = video.avatar
        document["site"] = str(video.site)
        document["channel"] = str(video.channel)
        document["content"] = dict()
        document["content"]["type"] = video.c_type
        document["content"]["src"] = video.c_src
        document["content"]["thumbnail"] = video.c_thumbnail
        if video.c_duration:
            document["content"]["duration"] = int(video.c_duration)
        else:
            document["content"]["duration"] = 0
        try:
            result = self.collection.insert_one(document)
        except DuplicateKeyError:
            pass
        except Exception as e:
            logging.error(e.message, exc_info=True)
        else:
            logging.info("store video data id: %s" % result.inserted_id)
    @classmethod
    def clean_pg_data(cls, data):
        """清洗上传到pg的数据, inplace"""
        if data["publish_site"] == VideoWeibo.PB_SITE:
            data["title"] = cls.clean_weibo_title(data["title"])
    @staticmethod
    def clean_weibo_title(title):
        """清洗标题"""
        title = title.strip("")
        words = title.split("#")
        return "".join([word for i, word in enumerate(words) if i % 2 == 0])
    @classmethod
    def upload_to_pg(cls, video):
        """上传至PG，通过统一Web存储API"""
        assert isinstance(video, Video)
        assert isinstance(video.pb_time, datetime)
        assert isinstance(video.insert, datetime)
        insert = video.insert + timedelta(hours=8)
        data = {
            "title": video.title,
            "unique_id": video.pb_url,
            "publish_url": video.pb_url,
            "publish_site": video.author,
            "publish_time": video.pb_time.isoformat()[:-7] + "Z",
            "insert_time": insert.isoformat()[:-7] + "Z",
            "author": video.author,
            "author_icon": video.avatar,
            "site_icon": video.avatar,
            "channel_id": video.chid,
            "second_channel_id": video.second_chid,
            "source_id": video.source_id,
            "online": True,
            "video_url": video.c_src,
            "video_thumbnail": video.c_thumbnail,
            "video_duration": video.c_duration,
            "play_times": 0,
        }
        # cls.clean_pg_data(data)  # 清洗要上传到pg的数据
        try:
            r = requests.post(cls.UPLOAD_URL, json=data, timeout=(5, 10))
        except Exception as e:
            logging.warning(e.message)
        else:
            if r.status_code == 200:
                logging.info(json.dumps(r.json()))
                # cls.store_relate_videos(r.json()["id"])
            else:
                logging.info(r.status_code)
    @classmethod
    def store_relate_videos(cls, nid):
        try:
            r = requests.post(cls.RELATE_URL, data={"id": nid}, timeout=(5, 10))
        except Exception as e:
            logging.warning(e.message)
        else:
            logging.info(len(r.json()))
    def store(self, video):
        """存储，存储调用函数"""
        if not (video.title and video.c_src and video.author
                and video.avatar and video.c_thumbnail):
            logging.warn("video data miss fields title: %s,c_src: %s"
                         % (video.title, video.c_src))
            return
        try:
            self.upload_to_mongodb(video)
            self.upload_to_pg(video)
        except Exception as e:
            logging.error(e.message)
class VideoMeiPai(VideoBase):
    """美拍视频抓取解析类"""
    PB_SITE = u"美拍"
    r_json = True
    @classmethod
    def parse(cls, document, task):
        data = [item["media"] for item in document if item["type"] == "media"]
        videos = list()
        for item in data:
            video = cls.build_video(task)
            video.title = item['caption']
            video.insert = format_time()
            video.pb_time = format_time(item['created_at'])
            video.pb_url = item['url']
            video.author = item["user"]["screen_name"]
            video.c_src = item["video"]
            video.c_thumbnail = item['cover_pic']
            video.c_duration = item['time']
            video.avatar = item["user"]["avatar"]
            videos.append(video)
        return videos
class VideoKuaiShou(VideoBase):
    """快手视频抓取解析类"""
    PB_SITE = u"快手"
    r_json = True
    @classmethod
    def parse(cls, document, task):
        data = document.get("feeds", [])
        videos = list()
        for item in data:
            video_urls = item.get("main_mv_urls")
            thumbs = item.get("cover_thumbnail_urls")
            avatars = item.get("headurls")
            if not all([video_urls, thumbs, avatars]):
                continue
            video = cls.build_video(task)
            video.title = item['caption']
            video.insert = format_time()
            video.pb_time = format_time(item['timestamp'])
            video.author = item["user_name"]
            video.c_src = video_urls[0]["url"]
            video.pb_url = video.c_src
            video.c_thumbnail = thumbs[0]["url"]
            duration = int(item["ext_params"].get("video", 0) / 1000.0)
            video.c_duration = duration
            video.avatar = avatars[0]["url"]
            videos.append(video)
        return videos
class VideoZAKER(VideoBase):
    """ZAKER视频抓取解析类"""
    PB_SITE = "ZAKER"
    r_json = True
    @classmethod
    def parse(cls, document, task):
        data = document["data"].get("articles", [])
        videos = list()
        for item in data:
            detail_url = item["full_url"]
            detail = cls.download(detail_url, c_json=True).get("data")
            if not detail:
                continue
            video_url = detail["video_info"]["url"]
            if video_url.endswith("m3u8"):
                video_url = video_url.replace("m3u8", "mp4")
            label = detail['video_info']["video_label"].split(":")[::-1]
            duration = 0
            for num, i in enumerate(label):
                duration += pow(60, num) * int(i)
            video = cls.build_video(task)
            video.title = item['title']
            video.pb_time = format_time()
            video.insert = format_time()
            video.author = item["auther_name"]
            video.c_src = video_url
            video.pb_url = item["weburl"]
            video.c_thumbnail = detail["video_info"]["pic_url"]
            video.c_duration = duration
            video.avatar = detail["article_group"]["logo"]["url"]
            videos.append(video)
        return videos
class VideoWeibo(VideoBase):
    """微博视频抓取解析类（仅能抓取其中得秒拍视频）"""
    PB_SITE = u"微博"
    r_json = False
    cookie_dict = {
        "SUB": "_2AkMvnF44dcPhrAJWm_EXzGzqaIhH-jycSTfOAn7uJhMyAxh77nc-qSWPCC49JGeSHgISGwk67XxQvGhEsQ.."}
    video_url_re = re.compile(r'video_src=(.*?)&playerType')
    config = {
        "detail_url": {"attribute": "href", "method": "select"},
        "title": {"params": {"selector": "div.txt_cut"}, "method": "select"},
        "user_name": {"params": {"selector": "div.item_a"}, "method": "select"},
        "user_avatar": {"attribute": "src", "params": {"selector": "img.face_pho"}, "method": "select"},
        "thumbnail": {"attribute": "src", "params": {"selector": "img.piccut"}, "method": "select"},
        "list": {"params": {"selector": "div.weibo_tv_frame > ul.li_list_1 > a"}, "method": "select"}
    }
    @classmethod
    def download(cls, url, c_json=False, skip=None, headers=None):
        session = requests.Session()
        session.cookies = requests.utils.cookiejar_from_dict(cls.cookie_dict,
                                                             cookiejar=None,
                                                             overwrite=True)
        response = session.get(url, headers=headers, timeout=(10, cls.timeout))
        content = response.content
        _, content = html_to_unicode(
            content_type_header=response.headers.get("content-type"),
            html_body_str=content
        )
        return content.encode("utf-8")
    @staticmethod
    def find_extract_tag_attribute(tag, params):
        if params.get("params"):
            tag = find_tag(tag, params)
        attribute = params.get("attribute", "text")
        return extract_tag_attribute(tag, attribute)
    @classmethod
    def parse(cls, document, task):
        soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
        tags = soup.select(selector="div.weibo_tv_frame > ul.li_list_1 > a")
        videos = list()
        for tag in tags:
            video = cls.build_video(task)
            video.title = cls.find_extract_tag_attribute(tag, cls.config["title"])
            video.pb_time = format_time()
            detail_url = urljoin("http://weibo.com", cls.find_extract_tag_attribute(tag, cls.config["detail_url"]))
            content = cls.download(url=detail_url)
            video_url = unquote_plus(cls.video_url_re.findall(content)[0])
            if "miaopai" not in video_url:
                continue
            video_url = video_url[:video_url.index('?')]
            video.c_src = video_url
            video.pb_url = detail_url
            video.author = cls.find_extract_tag_attribute(tag, cls.config["user_name"])
            video.c_thumbnail = cls.find_extract_tag_attribute(tag, cls.config["thumbnail"])
            video.c_duration = 0
            video.avatar = cls.find_extract_tag_attribute(tag, cls.config["user_avatar"])
            videos.append(video)
        return videos
class VideoThePaper(VideoBase):
    """澎湃新闻视频抓取解析类"""
    PB_SITE = "ThePaper"
    r_json = False
    video_url_re = re.compile(r'source src="(.*?)" type="video/mp4"')
    config = {
        "detail_url": {"attribute": "href", "params": {"selector": "a"}, "method": "select"},
        "title": {"params": {"selector": "div.video_title"}, "method": "select"},
        "user_name": {"params": {"selector": "div.t_source > a"}, "method": "select"},
        "user_avatar": {"attribute": "src", "params": {"selector": "div.video_txt_r_icon img"}, "method": "select"},
        "thumbnail": {"attribute": "src", "params": {"selector": "div.video_list_pic > img"}, "method": "select"},
        "list": {"params": {"selector": "div.video_list > li.video_news"}, "method": "select"}
    }
    @staticmethod
    def find_extract_tag_attribute(tag, params):
        if params.get("params"):
            tag = find_tag(tag, params)
        attribute = params.get("attribute", "text")
        return extract_tag_attribute(tag, attribute)
    @classmethod
    def parse(cls, document, task):
        soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
        tags = soup.select(selector=".video_news")
        videos = list()
        for tag in tags:
            video = cls.build_video(task)
            video.title = cls.find_extract_tag_attribute(tag, cls.config["title"])
            video.pb_time = format_time()
            detail_url = urljoin("http://www.thepaper.cn/",
                                 cls.find_extract_tag_attribute(tag, cls.config["detail_url"]))
            content = cls.download(url=detail_url)
            try:
                video_url = unquote_plus(cls.video_url_re.findall(content)[0])
            except IndexError as e:
                logging.warning("Can not get the url of the video")
                continue
            except Exception as e:
                logging.warning(e)
                continue
            video.c_src = video_url
            video.pb_url = detail_url
            video.author = cls.find_extract_tag_attribute(tag, cls.config["user_name"])
            video.author = video.author.replace(u"@所有人", u"澎湃视频")
            video.c_thumbnail = cls.find_extract_tag_attribute(tag, cls.config["thumbnail"])
            video.c_duration = 0
            detail_soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
            video.avatar = cls.find_extract_tag_attribute(detail_soup, cls.config["user_avatar"])
            videos.append(video)
        return videos
class VideoAutoHome(VideoBase):
    """汽车之家视频抓取解析类"""
    PB_SITE = u"汽车之家"
    site_icon = "https://oss-cn-hangzhou.aliyuncs.com/bdp-images/cf68e2b0b6d611e6ad6a00163e001e55.jpg"
    r_json = False
    vid_re = re.compile(r'vid=(.*?)&|vid: \"(.*?)\"')  #
    video_info_url = "http://p-vp.autohome.com.cn/api/gmi?mid={mid}&useragent=Android"
    config = {
        "detail_url": {"attribute": "href", "params": {"selector": "div.video-item-tit > a"}, "method": "select"},
        "title": {"params": {"selector": "div.video-item-tit > a"}, "method": "select"},
        "pb_time": {"params": {"selector": "div:nth-of-type(3) > span:nth-of-type(3)"}, "method": "select"},
    }
    @staticmethod
    def find_extract_tag_attribute(tag, params):
        if params.get("params"):
            tag = find_tag(tag, params)
        attribute = params.get("attribute", "text")
        return extract_tag_attribute(tag, attribute)
    @classmethod
    def parse(cls, document, task):
        soup = BeautifulSoup(document, "lxml", from_encoding="utf-8")
        tags = soup.select(selector="div.video-item")
        videos = list()
        for tag in tags:
            video = cls.build_video(task)
            video.title = cls.find_extract_tag_attribute(tag, cls.config["title"])
            pb_time = cls.find_extract_tag_attribute(tag, cls.config["pb_time"])
            video.pb_time = format_time(pb_time)
            if "youchuang" in task.url:
                detail_url = urljoin("http://youchuang.autohome.com.cn/",
                                     cls.find_extract_tag_attribute(tag, cls.config["detail_url"]))
            else:
                detail_url = urljoin("http://v.autohome.com.cn/",
                                     cls.find_extract_tag_attribute(tag, cls.config["detail_url"]))
            content = cls.download(url=detail_url)
            try:
                vid = cls.vid_re.findall(content)[0]
                vid = filter(lambda x: x, vid)[0]
            except IndexError as e:
                logging.warning("Can not get the vid of the video")
                continue
            video_info_url = cls.video_info_url.format(mid=vid)
            video_info = cls.download(video_info_url, c_json=True, skip=(5, -1))
            video.c_src = video_info["copies"][0]["playurl"]
            video.pb_url = detail_url
            video.author = cls.PB_SITE
            video.c_thumbnail = video_info["img"]
            video.c_duration = int(video_info["duration"])
            video.avatar = cls.site_icon
            videos.append(video)
        return videos
# ("meipai", "热门", "https://newapi.meipai.com/hot/feed_timeline.json?page=1&language=zh-Hans&client_id=1089857302&device_id=862535037295724&version=5920"),
# ("zaker", "视频", "http://iphone.myzaker.com/zaker/video_tab.php"),
# ("kuaishou","视频","http://api.gifshow.com/rest/n/feed/list?mod=Xiaomi%28MI%20MAX%29&lon=116.376867&country_code=CN&did=ANDROID_27dafccd6e32bfb2&app=0&net=WIFI&oc=UNKNOWN&ud=0&c=XIAOMI&sys=ANDROID_6.0.1&appver=4.53.6.3294&language=zh-cn&lat=39.905152&ver=4.53&id=4&token=&pv=false&client_key=3c2cd3f3&count=20&page=1&type=7&os=android&sig=1c4e1dd2e802c2c8bcc41269af64c91a&"),
Channel = namedtuple("Channel",
                     [
                         "desc",
                         "site_id",
                         "channel_id",
                         "url",
                         "handler",
                         "chid",
                         "second_chid",
                         "source_id",
                         "cname"
                     ])
TASKS = [
    Channel("美拍-搞笑", ObjectId("58be81943deaeb61dd2e28a6"), ObjectId("58be831eccb13641f8bbc7fc"),
            "https://newapi.meipai.com//channels/feed_timeline.json?id=13&type=1&feature=new&page=1&language=zh-Hans&client_id=1089857302&device_id=862535037295724&version=5920",
            VideoMeiPai, 44, 4402, 5256, u"搞笑"),
    Channel("美拍-宝宝", ObjectId("58be81943deaeb61dd2e28a6"), ObjectId("58be831eccb13641f8bbc7fd"),
            "https://newapi.meipai.com//channels/feed_timeline.json?id=18&type=1&feature=new&page=1&language=zh-Hans&client_id=1089857302&device_id=862535037295724&version=5920",
            VideoMeiPai, 44, 4403, 5257, u"萌宠萌娃"),
    Channel("美拍-宠物", ObjectId("58be81943deaeb61dd2e28a6"), ObjectId("58be831fccb13641f8bbc7fe"),
            "https://newapi.meipai.com//channels/feed_timeline.json?id=6&type=1&feature=new&page=1&language=zh-Hans&client_id=1089857302&device_id=862535037295724&version=5920",
            VideoMeiPai, 44, 4403, 5258, u"萌宠萌娃"),
    Channel("微博-搞笑", ObjectId("583bc5155d272cd5c47a7668"), ObjectId("58be8879ccb1364284fda8f1"),
            "http://weibo.com/tv/vfun",
            VideoWeibo, 44, 4402, 5259, u"搞笑"),
    Channel("微博-萌宠萌娃", ObjectId("583bc5155d272cd5c47a7668"), ObjectId("58be8879ccb1364284fda8f2"),
            "http://weibo.com/tv/moe",
            VideoWeibo, 44, 4403, 5260, u"萌宠萌娃"),
    Channel("微博-影视", ObjectId("583bc5155d272cd5c47a7668"), ObjectId("58c8ed29ccb1367615a9efdd"),
            "http://weibo.com/tv/movie",
            VideoWeibo, 44, 4404, 5261, u"娱乐"),
    Channel("微博-音乐", ObjectId("583bc5155d272cd5c47a7668"), ObjectId("58c8ed2accb1367615a9efde"),
            "http://weibo.com/tv/music",
            VideoWeibo, 44, 4404, 5262, u"娱乐"),
    Channel("微博-爱生活", ObjectId("583bc5155d272cd5c47a7668"), ObjectId("58c8ed2cccb1367615a9efe0"),
            "http://weibo.com/tv/lifestyle",
            VideoWeibo, 44, 4405, 5264, u"生活"),
    Channel("微博-体育健康", ObjectId("583bc5155d272cd5c47a7668"), ObjectId("58c8ed2dccb1367615a9efe1"),
            "http://weibo.com/tv/sports",
            VideoWeibo, 44, 4406, 5265, u"体育"),
    Channel("微博-明星综艺", ObjectId("583bc5155d272cd5c47a7668"), ObjectId("58c8ed2bccb1367615a9efdf"),
            "http://weibo.com/tv/show",
            VideoWeibo, 44, 4404, 5263, u"娱乐"),
    Channel("澎湃-视频", ObjectId("57a43ec2da083a1c19957a64"), ObjectId("59141c483deaeb61dd2e54b6"),
            "http://www.thepaper.cn/channel_26916",
            VideoThePaper, 44, 4, 5268, u"新闻"),
    Channel("汽车之家-原创视频", ObjectId("59141d373deaeb61dd2e54b7"), ObjectId("59141eab3deaeb61dd2e54b8"),
            "http://v.autohome.com.cn/Original#pvareaid=2029180",
            VideoAutoHome, 44, 4412, 5269, u"汽车"),
    Channel("汽车之家-视频广场", ObjectId("59141d373deaeb61dd2e54b7"), ObjectId("59141ffe3deaeb61dd2e54ba"),
            "http://v.autohome.com.cn/general/0-1-1#pvareaid=106447",
            VideoAutoHome, 44, 4412, 5270, u"汽车"),
    Channel("汽车之家-优创+精选", ObjectId("59141d373deaeb61dd2e54b7"), ObjectId("591420a23deaeb61dd2e54bb"),
            "http://youchuang.autohome.com.cn/Subject/VRecommend/Index",
            VideoAutoHome, 44, 4412, 5271, u"汽车")
]
def main():
    random.shuffle(TASKS)
    vs = StoreVideo()
    for task in TASKS:
        logging.info("start crawl: %s" % task.desc)
        try:
            videos = task.handler.run(task)
        except Exception as e:
            logging.error(e.message, exc_info=True)
        else:
            for video in videos:
                vs.store(video)
        logging.info("end crawl: %s" % task.desc)
    client.close()
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        filename="video.log",
                        filemode="a+")
    main()
    client.close()