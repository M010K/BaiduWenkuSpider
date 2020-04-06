from requests import get
from PIL import Image
from os import removedirs,remove,mkdir,getcwd
from os.path import join, exists
from requests.exceptions import ReadTimeout
from chardet import detect
from bs4 import BeautifulSoup
from re import findall
from json import loads
from time import time


class GetPpt:
    def __init__(self, url, savepath):
        self.url = url
        self.savepath = savepath if savepath != '' else getcwd()
        self.tempdirpath = self.makeDirForImageSave()
        self.pptsavepath = self.makeDirForPptSave()

        self.html = ''
        self.wkinfo ={}     # 存储文档基本信息:title、docType、docID
        self.ppturls = []   # 顺序存储包含ppt图片的url

        self.getHtml()
        self.getWkInfo()


    # 获取网站源代码
    def getHtml(self):
        try:
            header = {'User-Agent': 'Mozilla/5.0 '
                                    '(Macintosh; Intel Mac OS X 10_14_6) '
                                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                                    'Chrome/78.0.3904.108 Safari/537.36'}
            response = get(self.url, headers = header)
            self.transfromEncoding(response)
            self.html = BeautifulSoup(response.text, 'html.parser')  #格式化
        except ReadTimeout as e:
            print(e)
            return None


    # 转换网页源代码为对应编码格式
    def transfromEncoding(self,html):
        html.encoding =  detect(html.content).get("encoding")   #检测并修改html内容的编码方式


    # 获取文档基本信息:名字,类型,文档ID
    def getWkInfo(self):
        items = ["'title'","'docType'","'docId'","'totalPageNum"]
        for item in items:
            ls = findall(item+".*'", str(self.html))
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
        jsonstr = response.text[response.text.find('(')+1: response.text.rfind(')')]  # 获取json格式数据
        return jsonstr


    # 获取json字符串对应的字典
    def convertJsonToDict(self, jsonstr):
        """
        :param jsonstr: json格式字符串
        :return: json字符串所对应的python字典
        """
        textdict = loads(jsonstr)  # 将json字符串转换为python的字典对象
        return textdict


    # 创建临时文件夹保存图片
    def makeDirForImageSave(self):
        if not exists(join(self.savepath,'tempimages')):
            mkdir(join(self.savepath,'tempimages'))
        return join(self.savepath,'tempimages')

    # 创建临时文件夹保存ppt
    def makeDirForPptSave(self):
        if not exists(join(self.savepath,'pptfiles')):
            mkdir(join(self.savepath,'pptfiles'))
        return join(self.savepath,'pptfiles')


    # 从json文件中提取ppt图片的url
    def getImageUrlForPPT(self):
        timestamp = round(time()*1000)  # 获取时间戳
        desturl = "https://wenku.baidu.com/browse/getbcsurl?doc_id="+\
                  self.wkinfo.get("docId")+\
                  "&pn=1&rn=99999&type=ppt&callback=jQuery1101000870141751143283_"+\
                  str(timestamp) + "&_=" + str(timestamp+1)


        textdict = self.convertJsonToDict(self.getJson(desturl))
        self.ppturls = [x.get('zoom') for x in textdict.get('list')]


    # 通过给定的图像url及名称保存图像至临时文件夹
    def getImage(self, imagename, imageurl):
        imagename = join(self.tempdirpath, imagename)
        with open(imagename,'wb') as ig:
            ig.write(get(imageurl).content)  #content属性为byte


    # 将获取的图片合成pdf文件
    def mergeImageToPDF(self, pages):
        if pages == 0:
            raise IOError


        namelist = [join(self.tempdirpath, str(x)+'.png')  for x in range(pages)]
        firstimg = Image.open(namelist[0])
        imglist = []
        for imgname in namelist[1:]:
            img = Image.open(imgname)
            img.load()

            if img.mode == 'RGBA':  # png图片的转为RGB mode,否则保存时会引发异常
                img.mode = 'RGB'
            imglist.append(img)

        savepath = join(self.pptsavepath, self.wkinfo.get('title')+'.pdf')
        firstimg.save(savepath, "PDF", resolution=100.0,
                      save_all=True, append_images=imglist)

    # 清除下载的图片
    def removeImage(self,pages):
        namelist = [join(self.tempdirpath, str(x)+'.png') for x in range(pages)]
        for name in namelist:
            if  exists(name):
                remove(name)
        if exists(join(self.savepath,'tempimages')):
            removedirs(join(self.savepath,'tempimages'))


    def getPPT(self):
        self.getImageUrlForPPT()
        for page, url in enumerate(self.ppturls):
            self.getImage(str(page)+'.png', url)
        self.mergeImageToPDF(len(self.ppturls))
        self.removeImage(len(self.ppturls))


if __name__ == '__main__':
    GetPpt('https://wenku.baidu.com/view/a5fc216dc9d376eeaeaad1f34693daef5ff7130b.html?from=search', '').getPPT()

