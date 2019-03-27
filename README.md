# 爱奇艺解析器 (IQIYI-parser)

	以游客身份下载爱奇艺视频。

## 注意
__build目录下编译好的文件一定要把其目录下的两个js放到目录下。__

## 更新说明

* **2019/03/27**
 * 加入GUI支持。（花了两天粗劣写个一个GUI，等以后有时间再整理下）
 * 删除了一些设定。
 * 加入支持复制下载链接。  
* **2019/02/25**
	* 更新下载器程序。
* **2019/02/17**
	* 更新下载器程序，优化减少资源占用。
	* 支持更改下载路径。
	* 支持更改同时最大下载任务数。
	* 支持合并完后自动删除分段视频。
* **2018/09/07**
	* 修复若干bug。


## 使用说明

* 打开程序 main.exe，然后自己摸索。。。

### 以下信息我就先不更新了，将就看吧
	
## 项目包含
* __``/nbdler/*.py ``__: dl目录下的是下载器。(github: https://github.com/ZSAIm/nbdler)
* __``iqiyi-parse.py``__ : 视频解析。 ( / 目录下的两个js文件是用于解析地址的。)
* __``merge.py``__: 视频合并。
* __``/build/*``__: 已经编译好的程序。

## 安装模块
* __``Pyv8``__		: https://code.google.com/archive/p/pyv8/downloads
* __``pyperclip``__	: pip install pyperclip
* __``BeautifulSoup``__	: pip install beautifulsoup


## 引用项目
__``nbdler``__: https://github.com/ZSAIm/nbdler

***
## 项目地址
	github: https://github.com/ZSAIm/iqiyi-parser
