from requests import get
from requests.exceptions import ReadTimeout
from chardet import detect
from bs4 import BeautifulSoup
from os import getcwd,mkdir
from os.path import join,exists
from re import findall
from json import loads
from time import time


class GetTxt:
    def __init__(self, url, savepath):
        self.url = url
        self.savepath = savepath if savepath != '' else getcwd()
        self.txtsavepath = self.makeDirForTxtSave()
        self.html = ''
        self.wkinfo = {}  # 存储文档基本信息:title、docType、docID
        self.txturls = []

        self.getHtml()
        self.getWkInfo()


    # 创建临时文件夹保存ppt
    def makeDirForTxtSave(self):
        if not exists(join(self.savepath,'txtfiles')):
            mkdir(join(self.savepath,'txtfiles'))
        return join(self.savepath,'txtfiles')

    # 获取网站源代码
    def getHtml(self):
        try:
            header = {'User-Agent': 'Mozilla/5.0 '
                                    '(Macintosh; Intel Mac OS X 10_14_6) '
                                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                                    'Chrome/78.0.3904.108 Safari/537.36'}
            response = get(self.url, headers=header)
            self.transfromEncoding(response)
            self.html = BeautifulSoup(response.text, 'html.parser')  # 格式化

        except ReadTimeout as e:
            print(e)
            return None

    # 转换网页源代码为对应编码格式
    def transfromEncoding(self, html):
        # 检测并修改html内容的编码方式
        html.encoding = detect(html.content).get("encoding")

    # 获取文档基本信息:名字,类型,文档ID
    def getWkInfo(self):
        items = ["'title'", "'docType'", "'docId'", "'totalPageNum"]
        for item in items:
            ls = findall(item + ".*'", str(self.html))
            if len(ls) != 0:
                message = ls[0].split(':')
                self.wkinfo[eval(message[0])] = eval(message[1])

    # 获取json字符串
    def getJson(self, url):
        """
        :param url: json文件所在页面的url
        :return: json格式字符串
        """
        response = get(url)
        # 获取json格式数据
        jsonstr = response.text[response.text.find('(') + 1:response.text.rfind(')')]
        return jsonstr

    # 获取json字符串对应的字典
    def convertJsonToDict(self, jsonstr):
        """
        :param: jsonstr: json格式字符串
        :return: json字符串所对应的python字典
        """
        textdict = loads(jsonstr)  # 将json字符串转换为python的字典对象
        return textdict

    # 获取包含txt文本的json文件的url
    def getTxtUrlForTXT(self):
        timestamp = round(time() * 1000)  # 获取时间戳
        # 构造请求url,获取json文件所在url的参数
        messageurlprefix = "https://wenku.baidu.com/api/doc/getdocinfo?" \
                           "callback=cb&doc_id="
        messageurlsuffix = self.wkinfo.get("docId") + "&t=" + \
                           str(timestamp) + "&_=" + str(timestamp + 1)

        textdict = self.convertJsonToDict(
            self.getJson(messageurlprefix + messageurlsuffix))

        # 获取json文件所在url的参数
        self.txturls.append("https://wkretype.bdimg.com/retype/text/" +
                            self.wkinfo.get('docId') +
                            textdict.get('md5sum') +
                            "&callback=cb&pn=1&rn=" +
                            textdict.get("docInfo").get("totalPageNum") +
                            "&rsign=" + textdict.get("rsign") + "&_=" +
                            str(timestamp))

    # 将文本内容保存
    def saveToTxt(self, content):
        savepath = join(self.txtsavepath,self.wkinfo.get('title') + '.txt')
        with open(savepath, "a") as f:
            f.write(content)

    def getTXT(self):
        self.getTxtUrlForTXT()
        for url in self.txturls:
            textls = self.convertJsonToDict(self.getJson(url))
            for text in textls:
                content = text.get("parags")[0].get("c")
                self.saveToTxt(content)


if __name__ == '__main__':
    GetTxt('https://wenku.baidu.com/view/df3abfc36137ee06eff9183f.html?from=search', '').getTXT()



