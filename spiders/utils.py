# coding:utf-8

import base64


# http://www.btcha.com/

class DownConverter(object):
    @staticmethod
    def thunder_encode(url):
        thunder_prefix = "AA"
        thunder_posix = "ZZ"
        thunder_title = "thunder://"
        tem_t_url = url
        thunderUrl = thunder_title + base64.encodestring(thunder_prefix + tem_t_url + thunder_posix)
        return thunderUrl

    @staticmethod
    def thunder_decode(url):
        url = url.replace('thunder://', '')
        thunder_url = base64.decodestring(url)
        thunder_url = thunder_url[2:len(thunder_url) - 2]
        return thunder_url

    @staticmethod
    def qq_encode(url):
        url = "qqdl://" + base64.encodestring(url)
        return url

    @staticmethod
    def qq_decode(url):
        url = url.replace('qqdl://', '')
        qqurl = base64.decodestring(url)
        return qqurl

    @staticmethod
    def flashget_encode(url):
        url = 'Flashget://' + base64.encodestring('[FLASHGET]' + url + '[FLASHGET]')  # + '&1926'
        return url

    @staticmethod
    def flashget_decode(url):
        url = url.replace('Flashget://', '')
        try:
            url = url[0:url.index('&')]
        except:
            pass
        url = base64.decodestring(url)
        flashgeturl = url.replace('[FLASHGET]', '')
        flashgeturl = flashgeturl.replace('[FLASHGET]', '')
        return flashgeturl


if __name__ == "__main__":
    url = DownConverter.thunder_decode("thunder://QUFmdHA6Ly93OndAZDMuZGwxMjM0LmNvbTo0NTY3L1slRTclOTQlQjUlRTUlQkQlQjElRTUlQTQlQTklRTUlQTAlODJ3d3cuZHkyMDE4LmNvbV0lRTYlQUQlQTMlRTQlQjklODklRTglODElOTQlRTclOUIlOUYlRTUlQTQlQTclRTYlODglOTglRTUlQjAlOTElRTUlQjklQjQlRTYlQjMlQjAlRTUlOUQlQTZCRCVFNCVCOCVBRCVFOCU4QiVCMSVFNSU4RiU4QyVFNSVBRCU5Ny5ybXZiWlo=")

    from urllib import unquote

    print unquote(url)