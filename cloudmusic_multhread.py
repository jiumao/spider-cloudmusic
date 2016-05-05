# -*- coding: utf-8 -*-

# 多线程爬取网易云音乐所有歌曲点赞数第一的评论
# 包括爬取专辑ID、歌曲评论，不包括爬取歌手ID（从数据库直接读取歌手ID）
# HuangZhe
# 2016.4.25

import threading
import time
import Queue
import db_api
import pprint
from cloudmusic import get_one_album_comment
from cloudmusic import get_onesinger_album_id


default_timeout = 1000
SHARE_Q = Queue.Queue()  #构造一个不限制大小的的队列
_WORKER_THREAD_NUM = 20   #设置线程个数


class MyThread(threading.Thread) :
    def __init__(self, func) :
        super(MyThread, self).__init__()
        self.func = func
    def run(self) :
        self.func()


###########################################################################
## 多线程爬取专辑ID
###########################################################################
# 将未爬取的歌手加入到爬取队列
def add_singer_to_queue( max_num ):
    uncrawled_singer = db_api.search_record('singer', 'status', '0')
    num = 0
    for elm in uncrawled_singer:
        singer_id = elm[0]
        print "#### singer id:", singer_id
        print "#### Add to scrawling quene..."
        SHARE_Q.put(singer_id)
        num = num + 1
        if num > max_num :
            break

# 爬取专辑ID
def worker_crawl_album_id() :
    global SHARE_Q
    while not SHARE_Q.empty():
        singer_id = SHARE_Q.get() #获得任务
        get_onesinger_album_id(singer_id)
        time.sleep(1)
        SHARE_Q.task_done()

# 多线程爬取所有专辑ID
def get_all_album_id():
    threads = []
    uncrawled_singer = db_api.search_record('singer', 'status', '0')
    print "#### uncrawled singer:", len(uncrawled_singer)
    while len(uncrawled_singer)>0:
        # 一次向队列加入100个歌手
        add_singer_to_queue(100)
        for i in range(_WORKER_THREAD_NUM) :
            thread = MyThread(worker_crawl_album_id)
            thread.start()
            threads.append(thread)
        for thread in threads :
            thread.join()
        # 输出爬取状态
        temp = db_api.read_one_row('singer', 'singer_id')
        total_singer = len(temp)
        print "#### Total singer:", total_singer
        crawled_num = len ( db_api.search_record('singer', 'status', '1') )
        print ">>>>>>>>>> progress",crawled_num, "of", total_singer, "; Total singer:", total_singer

###########################################################################
## 多线程爬取歌曲评论
###########################################################################
# 将还没爬取的专辑ID加入爬取队列
def add_album_to_queue( max_num ):
    uncrawled_album = db_api.search_record('album', 'status', '0')
    num = 0
    for elm in uncrawled_album:
        album_id = elm[0]
        print "#### album id:", album_id
        print("#### Add to scrawling quene...")
        SHARE_Q.put(album_id)
        num = num + 1
        if num > max_num :
            break

# 爬取歌曲评论
def worker_crawl_song_comment() :
    global SHARE_Q
    while not SHARE_Q.empty():
        album_id = SHARE_Q.get() #获得任务
        get_one_album_comment(album_id)
        time.sleep(1)
        SHARE_Q.task_done()

# 多线程爬取所有歌曲评论
def get_all_song_comment():
    threads = []
    uncrawled_album = db_api.search_record('album', 'status', '0')
    print "#### uncrawled album:", len(uncrawled_album)
    while len(uncrawled_album)>0:
        # 一次向队列加入100张专辑
        add_album_to_queue(100)
        for i in range(_WORKER_THREAD_NUM) :
            thread = MyThread(worker_crawl_song_comment)
            thread.start()
            threads.append(thread)
        for thread in threads :
            thread.join()
        # 输出爬取状态
        temp = db_api.read_one_row('album', 'album_id')
        total_album = len(temp)
        print "#### Total album:", total_album
        crawled_num = len ( db_api.search_record('album', 'status', '1') )
        print ">>>>>>>>>> progress",crawled_num, "of", total_album, "; Total album:", total_album


###########################################################################
## main函数
###########################################################################
def main() :

    start_time = time.time()
    print( "Start time:", time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(start_time)) )

    db_api.create_database()
    get_all_album_id()
    get_all_song_comment()

    end_time = time.time()
    print( "End time:", time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(end_time)) )


if __name__ == '__main__':
    main()

