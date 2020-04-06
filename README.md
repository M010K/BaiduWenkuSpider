# BaiduWenkuSpider
实现对百度文库文档以pdf形式原格式下载

## 简介
写在最前，要是好用的话不妨给个**🌟🌟🌟star🌟🌟🌟**🤪
本项目是基于python实现对百度文库可预览文档的下载,实现了对以下文档格式的下载：

- doc/docx
- ppt/pptx
- xls/xlsx
- pdf
- txt

⚠️本项目下载的文档均为pdf格式(除txt外)



## 安装

最简单的安装方式是直接克隆整个仓库：

```powershell
$ git clone https://github.com/M010K/BauduWenkuSpider
```

当然也可以选择下载zip文件至本地



## 依赖

由于本项目基于python开发，故需要安装相应的第三方库，具体名称以及版本需求如下

第三方库名称存储在requirement.txt中

### ⚠️⚠️⚠️需要下载的第三方库(个人的版本参照)

|           库名           |  版本  |
| :----------------------: | :----: |
|        `requests`        | 2.19.1 |
|        `chardet`         | 3.0.4  |
|          `bs4`           | 4.6.3  |
| `PIL`实际是 `（Pillow）` | 5.2.0  |
|         `pdfkit`         | 0.6.1  |

⚠️一般来说，使用pip命令安装即可,关于PIL的安装请参考这篇[python3 怎么安装 PIL](https://blog.csdn.net/dcz1994/article/details/71642979)

**⚠️⚠️⚠️使用pdfkit需要安装wkhtmltopdf，放上下载的教程**

**可以参考一下这篇 [Python快速将HTML转PDF ，妈妈再也不会担心我不会转PDF了](https://juejin.im/post/5c6d2591e51d457fd033e305)（类似的教程挺多的）**

**或者这篇[Convert HTML to PDF with Python](https://pythonexamples.org/python-convert-html-to-pdf/)**



## 使用

将项目clone至本地后，下载不同类型的文档使用不同py文件即可

| 文档类型 |   文件    |
| :------: | :-------: |
|   txt    | GetTxt.py |
|   ppt    | GetPpt.py |
| doc/docx | GetAll.py |
| xls/xlsx | GetAll.py |
|   pdf    | GetAll.py |

使用时将文档的url以及存储路径设置好即可,如下

存储路径若为空字符串，则默认在当前目录下生成

```python
GetTxt('https://wenku.baidu.com/view/df3abfc36137ee06eff9183f.html?from=search', '存储路径').getTXT()
```

```python
GetPpt('https://wenku.baidu.com/view/a5fc216dc9d376eeaeaad1f34693daef5ff7130b.html?from=search', '存储路径').getPPT()
```

```python
GetAll('https://wenku.baidu.com/view/fb92d7d3b8d528ea81c758f5f61fb7360a4c2b61.html?from=search',"存储路径").Run()
```

