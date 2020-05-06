import requests
import os
from requests.exceptions import ReadTimeout
import chardet
from bs4 import BeautifulSoup
import re
import json
import math
from GetPpt import GetPpt
import time
import pdfkit

class GetAll:
    def __init__(self, url, savepath):
        """
        :param url: 待爬取文档所在页面的url
        :param savepath: 生成文档保存路径
        """
        self.url = url
        self.savepath = savepath if savepath != '' else os.getcwd()
        self.startpage = 1
        self.url = self.url + "&pn=1"
        self.html = ''
        self.wkinfo ={}     # 存储文档基本信息:title、docType、docID、totalPageNum
        self.jsonurls = []
        self.pdfurls = []

        self.getHtml()
        self.getWkInfo()
        self.htmlsdirpath = self.makeDirForHtmlSave()
        self.pdfsdirpath = self.makeDirForPdfSave()
        self.htmlfile = self.wkinfo.get('title')+".html"


    # 创建临时文件夹保存html文件
    def makeDirForHtmlSave(self):
        if not os.path.exists(os.path.join(self.savepath,'htmlfiles')):
            os.mkdir(os.path.join(self.savepath,'htmlfiles'))
        return os.path.join(self.savepath, 'htmlfiles')


    def makeDirForPdfSave(self):
        if not os.path.exists(os.path.join(self.savepath, 'pdffiles')):
            os.mkdir(os.path.join(self.savepath,'pdffiles'))
        return os.path.join(self.savepath,'pdffiles')

    # 创建html文档,用于组织爬取的文件
    def creatHtml(self):
        with open(os.path.join(self.htmlsdirpath, str(self.startpage) + self.htmlfile), "w") as f:
            # 生成文档头
            message = """
            <!DOCTYPE html>
            <html class="expanded screen-max">
                <head>
                <meta charset="utf-8">
                <title>文库</title>"""
            f.write(message)


    def addMessageToHtml(self,message):
        """:param message:向html文档中添加内容 """
        with open(os.path.join(self.htmlsdirpath, str(self.startpage) + self.htmlfile), "a", encoding='utf-8') as a:
            a.write(message)

    # 获取网站源代码
    def getHtml(self):
        try:
            header = {'User-Agent': 'Mozilla/5.0 '
                                    '(Macintosh; Intel Mac OS X 10_14_6) '
                                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                                    'Chrome/78.0.3904.108 Safari/537.36'}
            response = requests.get(self.url, headers = header)
            self.transfromEncoding(response)
            self.html = BeautifulSoup(response.text, 'html.parser')  # 格式化html
        except ReadTimeout as e:
            print(e)

    # 转换网页源代码为对应编码格式
    def transfromEncoding(self, html):
        html.encoding = chardet.detect(html.content).get("encoding")   #检测并修改html内容的编码方式

    # 获取文档基本信息:名字,类型,文档ID
    def getWkInfo(self):
        items = ["'title'","'docType'","'docId'","'totalPageNum"]
        for item in items:
            ls = re.findall(item+".*'", str(self.html))
            if len(ls) != 0:
                message = ls[0].split(':')
                self.wkinfo[eval(message[0])] = eval(message[1])


    # 获取存储信息的json文件的url
    def getJsonUrl(self):
            urlinfo = re.findall("WkInfo.htmlUrls = '.*?;", str(self.html))
            urls = re.findall("https:.*?}", urlinfo[0])
            urls = [str(url).replace("\\", "").replace('x22}','') for url in urls ]
            self.jsonurls = urls

    # 获取json字符串
    def getJson(self, url):
        """
        :param url: json文件所在页面的url
        :return: json格式字符串
        """
        response = requests.get(url)
        jsonstr = response.text[response.text.find('(')+1: response.text.rfind(')')]  # 获取json格式数据
        return jsonstr

    # 获取json字符串对应的字典
    def convertJsonToDict(self, jsonstr):
        """
        :param jsonstr: json格式字符串
        :return: json字符串所对应的python字典
        """
        textdict = json.loads(jsonstr)  # 将json字符串转换为python的字典对象
        return textdict

    # 判断文档是否为ppt格式
    def isPptStyle(self):
        iswholepic = False
        ispptlike = False
        for url in self.jsonurls:
            if "0.json" in url:
                textdict = self.convertJsonToDict(self.getJson(url))
                # 若json文件中的style属性为空字符串且font属性为None,则说明pdf全由图片组成
                if textdict.get("style") == "" and textdict.get("font") is None:
                    iswholepic = True
                    break
                elif textdict.get('page').get('pptlike'):
                    ispptlike = True
                    break
            break

        return iswholepic and ispptlike


    # 从html中匹配出与控制格式相关的css文件的url
    def getCssUrl(self):
        pattern =  re.compile('<link href="//.*?\.css')
        allmessage =  pattern.findall(str(self.html))
        allcss = [x.replace('<link href="', "https:") for x in allmessage]
        return allcss


    def getPageTag(self):
        """:return:返回id属性包含 data-page-no 的所有标签,即所有页面的首标签"""
        def attributeFilter(tag):
            return tag.has_attr('data-page-no')
        return self.html.find_all(attributeFilter)


    def getDocIdUpdate(self):
        """:return:doc_id_update字符串"""
        pattern = re.compile('doc_id_update:".*?"')
        for i in pattern.findall(str(self.html)):
            return i.split('"')[1]


    def getAllReaderRenderStyle(self):
        """:return: style <id = "reader - render - style">全部内容"""
        page = 1
        style = '<style id='+'"reader-render-style">\n'
        for url in self.jsonurls:
            if "json" in url:
                textdict = self.convertJsonToDict(self.getJson(url))
                style += self.getReaderRenderStyle(textdict.get('style'), textdict.get('font'), textdict.get('font'), page)
                page += 1
            else:
                break
        style += "</style>\n"

        return style


    def getReaderRenderStyle(self, allstyle, font, r, page):
        """
        :param allstyle: json数据的style内容
        :param font: json数据的font内容
        :param r: TODO:解析作用未知,先取值与e相同
        :param page: 当前页面
        :return: style <id = "reader - render - style">
        """
        p, stylecontent = "", []
        for index in range(len(allstyle)):
            style = allstyle[index]
            if style.get('s'):
                p = self.getPartReaderRenderStyle(style.get('s'), font, r).strip(" ")
            l = "reader-word-s" + str(page) + "-"
            p and stylecontent.append("." + l + (",." + l).join([str(x) for x in style.get('c')]) + "{ " + p + "}")
            if style.get('s').get("font-family"):
                pass
        stylecontent.append("#pageNo-" + str(page) + " .reader-parent{visibility:visible;}")
        return "".join(stylecontent)


    def getPartReaderRenderStyle(self, s, font, r):
        """
        :param s:  json style下的s属性
        :param font:  json font属性
        :param r: fontMapping TODO:先取为与e相同
        :return: style <id = "reader - render - style">中的部分字符串
        """
        content = []
        n, p = 10, 1349.19 / 1262.85  # n为倍数, p为比例系数, 通过页面宽度比得出

        def fontsize(f):
            content.append("font-size:" + str(math.floor(eval(f) * n * p)) + "px;")

        def letterspacing(l):
            content.append("letter-spacing:" + str(eval(l) * n) + "px;")

        def bold(b):
            "false" == b or content.append("font-weight:600;")

        def fontfamily(o):
            n = font.get(o) or o if font else o
            content.append("font-family:'" + n + "','" + o + "','" + (r.get(n) and r[n] or n) + "';")

        for attribute in s:
            if attribute == "font-size":
                fontsize(s[attribute])
            elif attribute == "letter-spacing":
                letterspacing(s[attribute])
            elif attribute == "bold":
                bold(s[attribute])
            elif attribute == "font-family":
                fontfamily(s[attribute])
            else:
                content.append(attribute + ":" + s[attribute] + ";")
        return "".join(content)


    # 向html中添加css
    def AddCss(self):
        urls = self.getCssUrl()
        urls = [url  for url in urls if "htmlReader" in url or "core" in url or "main" in url or "base" in url]
        for url in urls:
            message = '<style type="text/css">'+requests.get(url).text+"</style>>"
            self.addMessageToHtml(message)

        content = self.getAllReaderRenderStyle()  # 获取文本控制属性css
        self.addMessageToHtml(content)


    def addMainContent(self):
        """
        :param startpage: 开始生成的页面数
        :return:
        """

        self.addMessageToHtml("\n\n\n<body>\n")
        docidupdate = self.getDocIdUpdate()

        # 分别获取json和png所在的url
        jsonurl = [x for x in self.jsonurls if "json" in x]
        pngurl = [x for x in self.jsonurls if "png" in x]

        tags = self.getPageTag()
        for page, tag in enumerate(tags):
            if page > 50:
                break
            tag['style'] = "height: 1349.19px;"
            tag['id'] = "pageNo-" + str(page+1)
            self.addMessageToHtml(str(tag).replace('</div>', ''))
            diu = self.getDocIdUpdate()
            n = "-webkit-transform:scale(1.00);-webkit-transform-origin:left top;"
            textdict = self.convertJsonToDict(self.getJson(jsonurl[page]))

            # 判断是否出现图片url少于json文件url情况
            if page < len(pngurl):
                maincontent = self.creatMainContent(textdict.get('body'), textdict.get('page'), textdict.get('font'), page + 1, docidupdate,
                                                    pngurl[page])
            else:
                maincontent = self.creatMainContent(textdict.get('body'), textdict.get('page'), textdict.get('font'), page + 1, docidupdate, "")
            content = "".join([
                '<div class="reader-parent-' + diu + " reader-parent " + '" style="position:relative;top:0;left:0;' + n + '">',
                '<div class="reader-wrap' + diu + '" style="position:absolute;top:0;left:0;width:100%;height:100%;">',
                '<div class="reader-main-' + diu + '" style="position:relative;top:0;left:0;width:100%;height:100%;">', maincontent,
                "</div>", "</div>", "</div>", "</div>"])

            self.addMessageToHtml(content)
            print("已完成%s页的写入,当前写入进度为%f" % (str(page+self.startpage), 100*(page+self.startpage)/int(self.wkinfo.get('totalPageNum'))) + '%')

        self.addMessageToHtml("\n\n\n</body>\n</html>")


    def isNumber(self, obj):
        """
        :param obj:任意对象
        :return: obj是否为数字
        """
        return isinstance(obj, int) or isinstance(obj, float)


    def creatMainContent(self, body, page, font, currentpage, o, pngurl):
        """
        :param body: body属性
        :param page: page属性
        :param font: font属性
        :param currentpage: 当前页面数
        :param o:doc_id_update
        :param pngurl: 图片所在url
        :return:文本及图片的html内容字符串
        """
        content, p, s, h = 0, 0, 0, 0
        main = []
        l = 2
        c = page.get('v')

        d = font   # d原本为fongmapping
        y = {
                "pic": '<div class="reader-pic-layer" style="z-index:__NUM__"><div class="ie-fix">',
                "word": '<div class="reader-txt-layer" style="z-index:__NUM__"><div class="ie-fix">'
            }
        g = "</div></div>"
        MAX1 , MAX2 = 0, 0
        body = sorted(body, key=lambda k: k.get('p').get('z'))
        for index in range(len(body)):
            content = body[index]
            if "pic" == content.get('t'):
                MAX1 = max(MAX1, content.get('c').get('ih') + content.get('c').get('iy') + 5)
                MAX2 = max(MAX2, content.get('c').get('iw'))
        for index in range(len(body)):
            content = body[index]
            s = content.get('t')
            if not p:
                p = h = s
            if p == s:
                if content.get('t') == "word":
                    # m函数需要接受可变参数
                    main.append(self.creatTagOfWord(content, currentpage, font, d, c))
                elif content.get('t') == 'pic':
                    main.append(self.creatTagOfImage(content, pngurl, MAX1, MAX2))
            else:
                main.append(g)
                main.append(y.get(s).replace('__NUM__', str(l)))
                l += 1
                if content.get('t') == "word":
                    # m函数需要接受可变参数
                    main.append(self.creatTagOfWord(content, currentpage, font, d, c))
                elif content.get('t') == 'pic':
                    main.append(self.creatTagOfImage(content, pngurl, MAX1, MAX2))
                p = s
        return y.get(h).replace('__NUM__', "1") + "".join(main) + g


    def creatTagOfWord(self, t, currentpage, font, o, version, *args):
        """
        :param t: body中的每个属性
        :param currentpage: page
        :param font: font属性
        :param o:font属性
        :param version: page中的version属性
        :param args:
        :return:<p>标签--文本内容
        """
        p = t.get('p')
        ps = t.get('ps')
        s = t.get('s')
        z = ['<b style="font-family:simsun;">&nbsp</b>', "\n"]
        k, N = 10, 1349.19 / 1262.85
        # T = self.j
        U = self.O(ps)
        w, h, y, x, D= p.get('w'), p.get('h'), p.get('y'), p.get('x'), p.get('z')
        pattern=re.compile("[\s\t\0xa0]| [\0xa0\s\t]$")
        final = []

        if U and ps and ((ps.get('_opacity') and ps.get('_opacity') == 1) or (ps.get('_alpha') and ps.get('_alpha') == 0)):
            return ""
        else:
            width = math.floor(w * k * N)
            height = math.floor(h * k * N)
            final.append("<p "+'class="'+"reader-word-layer" + self.processStyleOfR(t.get('r'), currentpage) + '" ' + 'style="' + "width:" +str(width) + "px;" + "height:" + str(height) + "px;" + "line-height:" + str(height) + "px;")
            final.append("top:"+str(math.floor(y * k * N))+"px;"+"left:"+str(math.floor(x * k * N))+"px;"+"z-index:"+str(D)+";")
            final.append(self.processStyleOfS(s, font, o, version))
            final.append(self.processStyleOf_rotate(ps.get('_rotate'), w, h, x, y, k, N) if U and ps and self.isNumber(ps.get('_rotate')) else "")
            final.append(self.processStyleOfOpacity(ps.get('_opacity')) if U and ps and ps.get('_opacity') else "")
            final.append(self.processStyleOf_scaleX(ps.get('_scaleX'), width, height) if U and ps and ps.get('_scaleX') else "")
            final.append(str(isinstance(t.get('c'), str) and len(t.get('c')) == 1 and pattern.match(t.get('c')) and "font-family:simsun;") if isinstance(t.get('c'), str) and len(t.get('c')) == 1 and pattern.match(t.get('c')) else "")
            final.append('">')
            final.append(t.get('c') if t.get('c') else "")
            final.append(U and ps and str(self.isNumber(ps.get('_enter'))) and z[ps.get('_enter') if ps.get('_enter') else 1] or "")
            final.append("</p>")

            return "".join(final)


    def processStyleOfS(self, t, font, r, version):
        """
        :param t: 文本的s属性
        :param font: font属性
        :param r:font属性
        :param version:
        :return:处理好的S属性字符串
        """
        infoOfS = []
        n = {"font-size": 1}
        p , u = 10, 1349.19 / 1262.85

        def fontfamily(o):
            n = font.get(o) or o if font else o
            if abs(version) > 5:
                infoOfS.append("font-family:'"+ n + "','" + o + "','" + (r.get('n') and r[n] or n) + "';")
            else:
                infoOfS.append("font-family:'" + o + "','" + n + "','" + (r.get(n) and r[n] or n) + "';")

        def bold(e):
            "false" == e or infoOfS.append("font-weight:600;")

        def letter(e):
            infoOfS.append("letter-spacing:" + str(eval(e) * p) + "px;")

        if t is not None:
            for attribute in t:
                if attribute == "font-family":
                    fontfamily(t[attribute])
                elif attribute == "bold":
                    bold(t[attribute])
                elif attribute == "letter-spacing":
                    letter(t[attribute])
                else:
                    infoOfS.append(attribute + ":" + (str(math.floor(((t[attribute] if self.isNumber(t[attribute]) else eval(t[attribute])) * p * u))) + "px" if n.get(attribute) else t[attribute]) + ";")

        return "".join(infoOfS)


    def processStyleOfR(self, r, page):
        """
        :param r: 文本的r属性
        :param page: 当前页面
        :return:
        """
        l = " " + "reader-word-s" + str(page) + "-"
        return "".join([l + str(x) for x in r]) if isinstance(r, list) and len(r) != 0 else ""


    def processStyleOf_rotate(self, t, w, h, x, y, k, N):
        """
        :param t: _rotate属性
        :param w: body中p.w
        :param h: body中p.h
        :param x: body中p.x
        :param y: body中p.y
        :param k: 倍数10
        :param N: 比例系数
        :return: 处理好的_rotate属性字符串
        """
        p = []
        s = k * N
        if t == 90:
            p.append("left:" + str(math.floor(x + (w - h) / 2) * s) + "px;" + "top:" + str(math.floor(y - (h - w) / 2) * s) + "px;" + "text-align: right;" + "height:" + str(math.floor(h + 7) * s) + "px;")
        elif t == 180:
            p.append("left:" + str(math.floor(x - w) * s) + "px;" + "top:" + str(math.floor(y - h) * s) + "px;")
        elif t == 270:
            p.append("left:" + str(math.floor(x + (h - w) / 2) * s) + "px;" + "top:" + str(math.floor(y - (w - h) / 2) * s) + "px;")

        return "-webkit-"+"transform:rotate("+str(t)+"deg);"+"".join(p)


    def processStyleOf_scaleX(self, t, width, height):
        """
        :param t:     _scaleX属性
        :param width: 计算好的页面width
        :param height:计算好的页面height
        :return: 处理好的_scaleX属性字符串
        """
        return "-webkit-" + "transform: scaleX(" + str(t) + ");" + "-webkit-" + "transform-origin:left top;width:" + str(width + math.floor(width / 2)) + "px;height:" + str(height + math.floor(height / 2)) + "px;"


    def processStyleOfOpacity(self,t):
        """
        :param t: opacity属性
        :return:处理好的opacity属性字符串
        """
        t = (t or 0),
        return "opacity:" + str(t) + ";"


    def creatTagOfImage(self,t,url, *args):
        """
        :param t: 图片的字典
        :param url:图片链接
        :param args:
        :return:图像标签
        """
        u, l = t.get('p'), t.get('c')
        if u.get("opacity") and u.get('opacity') == 0:
            return ""
        else:
            if u.get("x1") or (u.get('rotate') != 0 and u.get('opacity') != 1):
                message = '<div class="reader-pic-item" style="' + "background-image: url(" + url + ");" + "background-position:" + str(-l.get('ix')) + "px " + str(-l.get('iy')) + "px;" \
                          + "width:" + str(l.get('iw')) + "px;" + "height:" + str(l.get('ih')) + "px;" + self.getStyleOfImage(u, l) + 'position:absolute;overflow:hidden;"></div>'
            else:
                [s, h] = [str(x) for x in args]
                message = '<p class="reader-pic-item" style="' + "width:" + str(l.get('iw')) + "px;" + "height:" + str(l.get('ih')) + "px;" + self.getStyleOfImage(u, l) + 'position:absolute;overflow:hidden;"><img width="' + str(h) + '" height="' + str(s) + '" style="position:absolute;top:-' + str(l.get('iy')) + "px;left:-" + str(l.get('ix')) + "px;clip:rect(" + str(l.get('iy')) + "px," + str(int(h) - l.get('ix')) + "px, " + str(s) + "px, " + str(l.get('ix')) + 'px);" src="' + url + '" alt=""></p>'

            return message


    def getStyleOfImage(self, t, e):
        """
        :param t: 图片p属性
        :param e: 图片c属性
        :return:
        """
        def parseFloat(string):
            """
            :param string:待处理的字符串
            :return: 返回字符串中的首个有效float值，若字符首位为非数字，则返回nan
            """
            if string is None:
                return math.nan
            elif isinstance(string, float):
                return string
            elif isinstance(string, int):
                return float(string)
            elif string[0] != ' ' and not str.isdigit(string[0]):
                return math.nan
            else:
                p = re.compile("\d+\.?\d*")
                all = p.findall(string)
                return float(all[0]) if len(all) != 0 else math.nan

        if t is None:
            return ""
        else:
            r, o, a, n = 0, 0, "", 0
            iw = e.get('iw')
            ih = e.get('ih')
            u = 1349.19 / 1262.85
            l = str(t.get('x') * u) + "px"
            c = str(t.get('y') * u) + "px"
            d = ""
            x = {}
            w = {"opacity": 1, "rotate": 1, "z": 1}
            for n in t:
                x[n] = t[n] * u if (self.isNumber(t[n]) and not w.get(n)) else t[n]

            if x.get('w') != iw or x.get('h') != ih:
                if x.get('x1'):
                    a = self.P(x.get('x0'), x.get('y0'), x.get('x1'), x.get('y1'), x.get('x2'), x.get('y2'))
                r = parseFloat(parseFloat(a[0])/iw if len(a) else x.get('w') / iw)
                o = parseFloat(parseFloat(a[1])/ih if len(a) else x.get('h') / ih)

                m, v = iw * (r-1), ih * (o-1)
                c = str((x.get('y1') + x.get('y3')) / 2 - parseFloat(ih) / 2)+"px" if x.get('x1') else str(x.get('y') + v / 2) + "px"
                l = str((x.get('x1') + x.get('x3')) / 2 - parseFloat(iw) / 2)+"px" if x.get('x1') else str(x.get('x') + m / 2) + "px"
                d = "-webkit-" + "transform:scale(" + str(r) + "," + str(o) + ")"

            message = "z-index:" + str(x.get('z')) + ";" + "left:" + l + ";" + "top:" + c + ";" + "opacity:" + str(x.get('opacity') or 1) + ";"
            if x.get('x1'):
                message += self.O(x.get('rotate')) if x.get('rotate') > 0.01 else self.O(0, x.get('x1'), x.get('x2'), x.get('y0'), x.get('y1'), d)
            else:
                message += d + ";"

            return message


    def P(self,t, e, r, i, o, a):
        p = round(math.sqrt(math.pow(abs(t - r), 2) + math.pow(abs(e - i), 2)), 4)
        s = round(math.sqrt(math.pow(abs(r - o), 2) + math.pow(abs(i - a), 2)), 4)
        return [s, p]


    def O(self, t, *args):
        [e, r, i, o, a] = [0, 0, 0, 0, ""] if len(args) == 0 else [x for x in args]
        n = o > i
        p = e > r
        if n and p:
            a += " Matrix(1,0,0,-1,0,0)"
        elif n:
            a += " Matrix(1,0,0,-1,0,0)"
        elif p:
            a += " Matrix(-1,0,0,1,0,0)"
        elif t:
            a += " rotate(" + str(t) + "deg)"
        return a + ";"


    def convertHtmlToPdf(self):
        savepath = os.path.join(self.pdfsdirpath, str(self.startpage)+self.wkinfo.get('title') + '.pdf')

        # 每个url的最大页数为50
        exactpages = int(self.wkinfo.get('totalPageNum'))
        if exactpages > 50:
            exactpages = 50
        options = {'disable-smart-shrinking':'',
                   'lowquality': '',
                   'image-quality': 60,
                   'page-height': str(1349.19*0.26458333),
                   'page-width': '291',
                   'margin-bottom': '0',
                   'margin-top': '0',
                   }
        pdfkit.from_file(os.path.join(self.htmlsdirpath, str(self.startpage) + self.htmlfile), savepath, options=options)

    def Run(self):
        self.getJsonUrl()
        # 判断是否文档是否为ppt格式
        if self.isPptStyle():
            GetPpt(self.url, self.savepath).getPPT()
        else:
            for epoch in range(int(int(self.wkinfo.get('totalPageNum'))/50)+1):
                self.startpage = epoch * 50 + 1
                if epoch == 0:
                    self.creatHtml()

                    start = time.time()
                    print('-------------Start Add Css--------------')
                    self.AddCss()
                    print('-------------Css Add Finissed-----------')
                    end = time.time()
                    print("Add Css Cost: %ss" % str(end - start))

                    start = time.time()
                    print('-------------Start Add Content----------')
                    self.addMainContent()
                    print('-------------Content Add Finished-------')
                    end = time.time()
                    print("Add MainContent Cost: %ss" % str(end - start))

                    start = time.time()
                    print('-------------Start Convert--------------')
                    self.convertHtmlToPdf()
                    print('-------------Convert Finished-----------')
                    end = time.time()
                    print("Convert Cost: %ss" % str(end - start))
                else:
                    self.url = self.url[:self.url.find('&pn=')] + "&pn=" + str(self.startpage)
                    print(self.url)
                    self.getHtml()
                    self.getJsonUrl()

                    self.creatHtml()

                    start = time.time()
                    print('-------------Start Add Css--------------')
                    self.AddCss()
                    print('-------------Css Add Finissed-----------')
                    end = time.time()
                    print("Add Css Cost: %ss" % str(end - start))

                    start = time.time()
                    print('-------------Start Add Content----------')
                    self.addMainContent()
                    print('-------------Content Add Finished-------')
                    end = time.time()
                    print("Add MainContent Cost: %ss" % str(end - start))

                    start = time.time()
                    print('-------------Start Convert--------------')
                    self.convertHtmlToPdf()
                    print('-------------Convert Finished-----------')
                    end = time.time()
                    print("Convert Cost: %ss" % str(end - start))




if __name__ == '__main__':
    # 若存储路径为空，则在当前文件夹生成
    GetAll('https://wenku.baidu.com/view/fb92d7d3b8d528ea81c758f5f61fb7360a4c2b61.html?from=search',
                  "").Run()

