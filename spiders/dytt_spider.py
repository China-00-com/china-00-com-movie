# coding:utf-8
import re
import HTMLParser
import requests
import chardet


class DetailParserBase(object):
    pass


class DyttDetailParser(DetailParserBase):
    POSTER = re.compile(u'<img.*?src="(.*?)".*?◎')
    TRANSE_TITLE = re.compile(u'>◎译　　名(.*?)<')
    TITLE = re.compile(u'>◎片　　名(.*?)<')
    AGE = re.compile(u'>◎年　　代(.*?)<')
    RELEASE = re.compile(u'>◎上映日期(.*?)<')
    PRODUCT_ORI = re.compile(u'>◎产　　地(.*?)<')
    CATE = re.compile(u'>◎类　　别(.*?)<')
    LANGUAGE = re.compile(u'>◎语　　言(.*?)<')
    SUBTITLE = re.compile(u'>◎字　　幕(.*?)<')
    IMDB_SCORE = re.compile(u'>◎IMDb评分(.*?)<')
    DOUBAN_SCORE = re.compile(ur'>◎豆瓣评分(.*?)<')
    EPISODES = re.compile(u'>◎集　　数(.*?)<')
    FORMAT = re.compile(u'>◎文件格式(.*?)<')
    SIZE = re.compile(u'>◎视频尺寸(.*?)<')
    CD_NUM = re.compile(u'>◎文件大小(.*?)<')
    DURATION = re.compile(u'>◎片　　长(.*?)<')
    DIRECTOR = re.compile(u'>◎导　　演(.*?)<')
    ACTOR = re.compile(u'◎主　　演(.*?)◎')
    INTRO = re.compile(u'◎简　　介(.*?)</p>')
    DOWLOAD_URL = re.compile(u'')
    HTML_CLEAN = re.compile(u'<.*?>')
    SPLIT_TAG = "TACEY"

    @classmethod
    def __clean_html(cls, text, split_tag):
        text = re.sub('<img.*?/>', "", text)
        text = cls.HTML_CLEAN.sub(cls.SPLIT_TAG, text)
        return text

    @classmethod
    def get_title(cls, document):
        titles = cls.TITLE.findall(document)
        return titles

    @classmethod
    def get_transe_title(cls, document):
        transe_titles = cls.TRANSE_TITLE.findall(document)
        if not transe_titles:
            return []
        else:
            transe_titles = transe_titles[0]
        transe_titles = transe_titles.strip().split("/")
        return transe_titles

    @classmethod
    def get_age(cls, document):
        age = cls.AGE.findall(document)
        if not age:
            return 0
        age = int(age[0])
        return age

    @classmethod
    def get_product_ori(cls, document):
        product_ori = cls.PRODUCT_ORI.findall(document)
        if not product_ori:
            return ""
        product_ori = product_ori[0]
        return product_ori

    @classmethod
    def get_cate(cls, document):
        cates = cls.CATE.findall(document)
        if not cates:
            return []
        cates = cates[0]
        cates = map(lambda x: x.strip(), cates.strip().split("/"))
        return cates

    @classmethod
    def get_language(cls, document):
        lang = cls.LANGUAGE.findall(document)
        if not lang:
            return ""
        lang = lang[0].strip()
        return lang

    @classmethod
    def get_subtitle(cls, document):
        subtitle = cls.SUBTITLE.findall(document)
        if not subtitle:
            return ""
        subtitle = subtitle[0].strip()
        return subtitle

    @classmethod
    def get_score(cls, document):
        imdb_score = cls.IMDB_SCORE.findall(document)
        print imdb_score
        if not imdb_score:
            imdb_score = ""
        else:
            imdb_score = imdb_score[0].strip()
        douban_score = cls.IMDB_SCORE.findall(document)
        if not douban_score:
            douban_score = ""
        else:
            douban_score = douban_score[0].strip()
        score = dict()
        score["douban"] = douban_score
        score["imdb"] = imdb_score
        return score

    @classmethod
    def get_episodes(cls, documen):
        episodes = cls.EPISODES.findall(documen)
        if not episodes:
            episodes = 1
        else:
            episodes = episodes[0].strip()
            episodes = re.findall('\d+', episodes)
            if episodes:
                episodes = int(episodes[0])
            else:
                episodes = 1
        return episodes

    @classmethod
    def get_format(cls, document):
        format = cls.FORMAT.findall(document)
        if not format:
            return ""
        format = format[0].strip()
        return format

    @classmethod
    def get_size(cls, document):
        size_info = {
            "width": 0,
            "height": 0,
            "text": 0
        }
        size = cls.SIZE.findall(document)
        if not size:
            return size_info
        size = size[0].strip()
        size_info["text"] = size
        size = map(lambda x: x.strip(), size.split("x"))
        size_info["width"] = int(size[0])
        size_info["height"] = int(size[1])
        return size_info

    @classmethod
    def get_cd_num(cls, document):
        cd_num = cls.CD_NUM.findall(document)
        if not cd_num:
            cd_num = 1
        else:
            cd_num = cd_num[0]
            cd_num = re.findall('\d+', cd_num)
            if cd_num:
                cd_num = cd_num[0]
            else:
                cd_num = 1
        return cd_num

    @classmethod
    def get_duration(cls, document):
        duration = cls.DURATION.findall(document)
        if not duration:
            return 0
        duration = duration[0].strip()
        duration = re.findall(u'(\d+)(分钟|小时|秒)', duration)
        if not duration:
            return 0
        seconds = 0
        digit = float(duration[0][0])
        unit = duration[0][1]
        if unit == u'分钟':
            seconds = int(digit * 60)
        elif unit == u'小时':
            seconds = int(digit * 60 * 60)
        elif unit == "秒":
            seconds = int(digit)
        return seconds

    @classmethod
    def get_director(cls, document):
        director = cls.DIRECTOR.findall(document)
        if not director:
            return ""
        director = director[0].strip()
        return [director]

    @classmethod
    def get_actor(cls, document):
        actor = cls.ACTOR.findall(document)
        if not actor:
            return []
        actor = actor[0].strip()
        actor = cls.__clean_html(actor, split_tag=cls.SPLIT_TAG)
        actor = filter(lambda x: x != u"",
                       map(lambda x: x.strip(),
                           actor.split(cls.SPLIT_TAG)))
        return actor

    @classmethod
    def get_intro(cls, document):
        intro = cls.INTRO.findall(document)
        if not intro:
            return ""
        intro = intro[0].strip()
        intro_pics = re.findall('<img.*?src="(.*?)"', intro)
        intro = cls.__clean_html(intro, split_tag=cls.SPLIT_TAG)
        intro_text = filter(lambda x: x != u"", map(lambda x: x.strip(), intro.split(cls.SPLIT_TAG)))
        intro_content = list()
        for text in intro_text:
            intro_content.append({"content": text, "type": "text"})
        for pic in intro_pics:
            intro_content.append({"content": pic, "type": "img"})
        return intro_content

    @classmethod
    def get_poster(cls,document):
        poster = cls.POSTER.findall(document)
        if not poster:
            return []
        return poster



def transe2unicode(text):
    if isinstance(text, str):
        check_result = chardet.detect(text)
        encode = check_result["encoding"]
        if 'GB' in encode:
            return text.decode("gbk")
        elif "8" in encode:
            return text.decode("utf-8")
        else:
            return text
    elif isinstance(text, unicode):
        return text


def unescape(html):
    html_parser = HTMLParser.HTMLParser()
    return html_parser.unescape(html)


def get_html(url):
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
    resp = requests.get(url, headers={"user-agent": ua})
    content = resp.content
    content = transe2unicode(content)
    content = unescape(content)
    return content


if __name__ == "__main__":
    url = "http://www.dytt8.net/html/gndy/jddy/20170708/54460.html"
    doc = get_html(url)
    print DyttDetailParser.get_poster(doc)
