# IQIYI-parser
 parse IQIYI url, and download the videos.

# 爱奇艺解析器 (IQIYI-parser)

	这是个成品程序，可以直接使用去下载爱奇艺视频。

## 注意
__build目录下编译好的文件一定要把其目录下的两个js放到目录下。__

## 更新说明
* 添加一下代码解决由于python版本的更新出现的ssl问题。
```Python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```
	
## 项目包含
* __``/dl/*.py ``__: dl目录下的是下载器。(github: https://github.com/ZSAIm/not-bad-downloader)
* __``iqiyi-parse.py``__ : 视频解析。 ( / 目录下的两个js文件是用于解析地址的。)
* __``merge.py``__: 视频合并。
* __``/build/*``__: 已经编译好的程序。

## 安装模块
* __``Pyv8``__		: https://code.google.com/archive/p/pyv8/downloads
* __``pyperclip``__	: pip install pyperclip
* __``BeautifulSoup``__	: pip install beautifulsoup


## 引用项目
__``not-bad-downloader``__: https://github.com/ZSAIm/not-bad-downloader

***
## 项目地址
	github: https://github.com/ZSAIm/iqiyi-parser
