
# Nbdler (Not-Bad-Downloader)

**基于python所编写的多线程HTTP/HTTPS下载模块。**


****

## 本项目会跟随另一个项目： https://github.com/ZSAIm/iqiyi-parser 进行更新。



## 特征
* 支持断点续传。
* 支持多来源地址下载。
* 多线程分片下载。
* 自动分片控制管理。

## 更新说明
* **2019/05/07**
	* 修复小文件无法释放写出缓存问题。
	
* **2019/05/03**
	* 修复分片切割器失控问题。
	* 支持Manager进行嵌套成多级组下载。

* **2019/04/28**
	* 修复断点续传功能无法使用问题。

* **2019/04/25**
	* 添加方法：线程阻塞join，安全关闭线程shutdown。
	* 支持多线程字段自定义，可通过参数range_format控制，以适应多种多线程方式。(默认:　Range: bytes=%d-%d)
	* 提高线程池稳定性。
	* 修复ssl握手错误： sslv3 alert handshake failure (_ssl.c:646)
	* 修复模块的导出错误问题。
	* 优化若干bug。
* **2019/04/12**
	* 加入线程池来管理线程。
	* 修复线程失控问题。
	* 修复下载无线重试问题。
* **2019/02/25**
    * 修复内存泄露问题，优化下载缓冲方式。
    * 优化部分代码结构，提高代码可读性。
* **2019/02/17** 
    * 兼容python 2/3。
    * 优化部分代码。
    * 修复若干bug。
* **2019/02/14**
    * 完善DLManager，增加下载任务管理模块。
* **2019/02/13**
    * 项目更名为nbdler。
    * 基于not-bad-downloader 进行代码重构。


****
## 总体架构

```
+----------------------------------------------------------------------------+
| Manager                                                                    |
|     +--------------------------------------------------------------------+ |
|     | Handler                                                            | |
|     |      +-----------------------------------------------------------+ | |
|     |      | GlobalProgress                                            | | |
|     |      |      +------------------------------+      +-----------+  | | |
|     |      |      | Progress                     |      | Allotter  |  | | |
|     |      |      |       +-------------------+  |      |           |  | | |
|     |      |      |       | processor         |  |      |           |  | | |
|     |      |      |       |                   |  |      +-----------+  | | |
|     |      |      |       +-------------------+  |                     | | |
|     |      |      +------------------------------+      +-----------+  | | |
|     |      |                                            | Inspector |  | | |
|     |      |      +------------------------------+      |           |  | | |
|     |      |      | Progress                     |      |           |  | | |
|     |      |      |       +-------------------+  |      +-----------+  | | |
|     |      |      |       | processor         |  |                     | | |
|     |      |      |       |                   |  |                     | | |
|     |      |      |       +-------------------+  |                     | | |
|     |      |      +------------------------------+                     | | |
|     |      |                                                           | | |
|     |      |      ......                                               | | |
|     |      |                                                           | | |
|     |      +-----------------------------------------------------------+ | |
|     +--------------------------------------------------------------------+ |
|                                                                            |
|     +--------------------------------------------------------------------+ |
|     | Handler                                                            | |
|     |      ......                                                        | |
|     +--------------------------------------------------------------------+ |
|                                                                            |
|     ......                                                                 |
|                                                                            |
+----------------------------------------------------------------------------+
```

### 模块说明
* **Manager** : Handler**s**管理器。
* **Handler** : 目标任务的信息载体。
* **GlobalProgress** : 任务进度信息管理者。
* **Progress** : 分片信息载体。
* **Processor** : 分片操作处理器。
* **Allotter** : 分片切割器。
* **Inspector** : 处理器线程监视器。



# 以下使用方法一部分已不可用，等有心情了再进行修改使用说明。

## nbdler.open()可控参数
### 全局参数：

 参数  |  默认  |  说明
 ---- | -----  |  -----
filename  |  from url  |  文件名称。
filepath  |  ""  |  文件路径。(默认当前目录, "")
block_size  |  1MB  |  下载块大小。(数值越小，块数量越多，可分片数量越多，占用资源越多）
buffer_size  |  20MB  |  下载缓冲空间大小。(理论上缓冲空间越大，占用内存资源越多，下载速度越快， 适当调大可以降低对硬盘读写损耗)
max_conn  |  无限制  |  最大连接数。(默认-1， 即无限制)
max_speed  |  无限制  |  最大下载速度。(尚未实现，先占位)

### 链接局部参数

 参数  |  默认  |  说明
----  |  -----  |  -----
urls  |    |  [url1, url2, ...]
cookies  |  ""  |  指定对应链接的cookie: [cookie1, cookie2, ...]
hosts  |  from url  |  指定对应链接的host: [host1, host2, ...]
ports  |  from url  |  指定对应链接的port: [port1, port2, ...]
paths  |  from url  |  指定对应链接的port: [path1, path2, ...]
headers  |  chrome  |  指定对应链接的port: [header1, header2, ...]
max_threads  |  无限制  |  限制对应链接的最大线程数: 默认无限制[max_thread1, max_thread2, ...]

#### 注意：各参数列表的一个索引对应生成一个链接来源地址节点。
#### 若len(urls) > 1时，cookies/hosts/ports/paths/headers 可以使用单个元素来设置全局链接的参数。 如 headers = [header]


## 使用方法
### 打开下载例程
```python
# 若要下载文件A, 并且文件A可以通过在以下两个地址来源进行获取:
# 1)    https://host1:port1/path1/A		, 限制最大线程数： -1（无限制)
# 2)	https://host2:port2/path2/A		, 限制最大线程数： 10
# 限制下载最大链接数： 32


# 方法一: (一步到位)

import nbdler
urls = ['https://host1:port1/path1/A', 'https://host2:port2/path2/A']
dl = nbdler.open(max_conn=32, urls=urls, max_threads=[-1, 10])


# 方法二: (逐步添加)

import nbdler
dl = nbdler.open()

dl.config(max_conn=32)

dl.addNode(url='https://host1:port1/path1/A', max_thread=-1)
dl.addNode(url='https://host2:port2/path2/A', max_thread=10)

```

### 获取下载信息
```python
# 省略以上任务建立代码

# 获取下载文件大小
dl.getFileSize()

# 获取下载文件名
dl.getFileName()

# 获取瞬时下载速度
dl.getInsSpeed()

# 获取平均下载速度
dl.getAvgSpeed()

# 获取剩余下载字节
dl.getLeft()

# 获取当前在线的分片(返回正在链接获取数据的分片)
dl.getOnlines()

# 获取任务是否完成
dl.isEnd()

# 获取当前链接分片(返回所有的未完成分片)
dl.getConnections()

# 获取所有下载来源地址数据
dl.getUrls()

```

### 任务操作
```python 
# 省略任务建立的代码

# 开始下载任务
dl.run()

# 任务暂停
dl.pause()	# 该方法将等待任务完全暂停后返回。

# 关闭完成任务
dl.close()	# 该方法将删除下载任务信息的本地文件 '*.nbdler'


# 临时安装新的GlobalProgress。

dl.install(GlobalProgress)

# 新添加下载来源地址节点(允许在下载过程中进行添加)
dl.addNode(id=-1, url, cookie, headers, host, port, path, protocal, proxy, max_thread)

# 批量添加下载来源地址节点(具体参数参见以上: 链接局部参数)
dl.batchAdd(wait=True, urls=urls, ..)	# 参数： wait，为False时将新建线程来执行而不占用主线程。

# 删除下载来源地址节点(不允许下载过程中删除)
dl.delete([url, ], [id, ])

# 文件校验(实则是对各个分片最后指定大小的数据的校验)
segs = dl.fileVerify()	# 返回所有校验不匹配的分片索引

# 对分片索引所对应的分片进行重新下载
dl.fix(segs)

# 取样匹配Url链接数据，返回包含的所有样本类型。
dl.sampleUrls()	# 返回一个二维列表，即匹配的样本将在处于同一列表中。

```

### 若非完整下载文件，而只是文件其中片段。

```python

import nbdler
urls = ['https://host1:port1/path1/A', 'https://host2:port2/path2/A']
dl = nbdler.open(max_conn=32, urls=urls, max_threads=[-1, 10])

# 若下载该文件的 0-512 和 1024-4096 段的数据，分别使用1和3个线程进行下载。。
dl.insert(0, 512, 1)
dl.insert(1024, 4096, 3)

# 对其进行下载
dl.manualRun()	# 当使用该方法运行的时候将自动进入片段下载模式而非文件下载模式

# 使用同样的方法进行获取下载过程信息
...
...

# 获取下载片段数据可以使用
dl.getSegsValue()	# 返回以范围为索引的数据数据流组成的字典，如{'0-512': ..., '1024-4096': ...} 

# 获取下载片段当前数据大小
dl.getSegsSize()	# 返回已下载并且完成缓冲的片段数据大小

# 片段的更多操作可以引用
dl.file.fp

```

### 下载任务管理
```python
# 管理多个下载任务，限制同时最大下载量为2个
# 假设目前有3个下载任务： A,B,C

import nbdler

# 任务A
dlA = nbdler.open(urls=[url_A], max_threads=[5], filename='A')

# 任务B
dlB = nbdler.open()
dlB.config(filename='B')
dlB.addNode(url=url_B)

# 任务C
dlB = nbdler.open(urls=[url_C], filename='C')

# 打开下载任务管理器
dlm = nbdler.Manager()

# 将Handler添加进入任务管理器的队列，返回为该任务生成对应的唯一id
# dlm.addHander(Handler= , [name=]), name为可选命名 
dlm.addHandler(dlA)
dlm.addHandler(dlB)
dlm.addHandler(dlC)

# 配置同时最大下载任务数
dlm.config(max_task=2)

# 启动下载任务管理器，以最大下载任务进行下载
dlm.run([id=])

# 暂停下载任务，指定id将暂停指定任务的Handler，否则将暂停所有任务
dlm.pause([id=])


# 获取下载信息

# 返回正在进行下载的队列id列表
dlm.getRunQueue()

# 返回处于暂停状态的队列id列表
dlm.getPauseQueue()

# 返回未下载完成的队列id列表
dlm.getUndoneQueue()

# 返回已下载完成的队列id列表
dlm.getDoneQueue()

# 返回所有任务队列信息
dlm.getAllTask()

# 通过name获取对应id
dlm.getIdFromName(id)

# 通过id获取对应name
dlm.getNameFromId(name)

# 通过id或者name来取得对应的Handler。
# getHandler([id=], [name=]) 
dlm.getHandler()

# 获取瞬时速度，指定id将返回对应的Handler的瞬时速度，否则将返回Run队列的瞬时速度总和。
dlm.getInsSpeed([id=])

# 获取平均速度，指定id和不指定的区别，同上。
dlm.getAvgSpeed([id=])

# 获取剩余下载字节，指定id与否意义同上。
dlm.getLeft([id=])

# 获取任务管理器是否全部下载完成，包括Run队列和Undone队列。
dlm.isEnd()


```


# LICENSE
Apache 2.0






