# 爱奇艺解析器 (IQIYI-parser)

	以游客身份下载爱奇艺视频。

## 注意
__build目录下编译好的文件一定要把其目录下的两个js放到目录下。__

## 更新说明
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

* 打开程序 main.exe
* 复制爱奇艺视频的地址至剪切板。
* 返回 main.exe，等待解析完成。
* 选择解析结果。
* 等待下载完成，并且等待合并完成。
* 显示ok！，已完成，可关闭程序。

说明： 若下载过程中关闭了程序，可以再次打开程序解析同样的视频地址，接着下载。


## config.ini 
可以通过修改程序目录下的config.ini更改来下载器的一些设置。

```
[settings]
bids = [100, 200, 300, 400, 500, 600]
max_task = 5
save_path = 
del_after = T
```

* **bids** : 清晰度解析（范围100-600）,数值越高，清晰度越高，解析耗时越长。
* **max_task** : 同时最大下载任务。
* **save_path** : 视频保存路径。例如： save_path = d:/video/
* **del_after** : 合并任务完成后是否删除分段视频。 (是： T， 否： F）



	
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
