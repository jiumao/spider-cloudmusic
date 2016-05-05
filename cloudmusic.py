# -*- coding: utf-8 -*-

# 单线程爬取网易云音乐所有歌曲点赞数第一的评论
# HuangZhe
# 2016.4.22

import requests
import re
from bs4 import BeautifulSoup
import db_api
import pprint
from comment_api import get_one_singer_comment

# 请求超时时间
default_timeout = 1000


#######################################################################################################
## 爬取歌手ID信息，写入数据表：singer
## 数据表项格式： （singer_id, name, status)
## get_all_singer_id()：爬取网站全部歌手信息，该函数调用如下两个函数：
##   ==> get_category_id(): 爬取歌手分类页面ID
##   ==> get_onepage_singer_id(cat_id, init_id): 爬取歌手分类链接上一个页面的所有歌手id，并写入数据表
#######################################################################################################
#获取歌手分类页面ID
#返回字典值: category_id
def get_category_id():
    category_id = {}
    url = r'http://music.163.com/discover/artist/cat?id=1001'
    req = requests.get(url, timeout=default_timeout)
    page = BeautifulSoup(req.text, "html.parser")
    # print(page.prettify())
    a = page.find_all("a", class_="cat-flag")
    #对连接进行处理，分割出分类名及ID
    for elm in a:
        #print( elm['href'] )
        href = elm['href'].split('?')
        if ( len(href) == 2 ):
            category_id[ href[1][3:] ] = elm.string
    return(category_id)

#爬取歌手分类链接上一个页面所有歌手id，并将结果写入数据表singer
#输入参数： cat_id：歌手分类ID ；init_id：页面ID（ 0,65-90 : “其他”，“A-Z”）
def get_onepage_singer_id(cat_id, init_id):
    singer_id = []
    url = r'http://music.163.com/discover/artist/cat'
    payload = {'id': cat_id , 'initial': init_id}
    req = requests.get(url, params=payload, timeout=default_timeout)
    #print(req.url)
    page = BeautifulSoup(req.text, "html.parser")
    #print(page.prettify())
    #查找并分割出歌手名称及ID，存入singer_id
    a = page.find_all("a", href = re.compile(r"artist\?id=[0-9]+"))
    for elm in a:
        if elm.string != None:
            href = elm['href'].split('?')
            id = href[1][3:]
            #将特殊符号’替换为_，否则会导致SQL指令出错
            name = elm.string.replace('\'','_')
            #按singer数据表的字段顺序保存，并将status字段设为0
            singer_id.append( (id , name, 0) )
            # print( elm )
    #将结果保存到数据表singer
    print("## Writing to database...")
    db_api.insert_record("singer", "singer_id", singer_id)
    # #验证数据是否正确写入数据库中
    # db_api.check_records("singer", "singer_id", singer_id)
    return(singer_id)

#获取网站上全部歌手ID信息
#返回抓取到的歌手数量
def get_all_singer_id():
    #先获取歌手分类ID
    category_id = get_category_id()
    pprint.pprint(category_id)
    singer_id = []
    #逐个分类爬取
    for elm in category_id:
        #“其他”页面，ID为0
        print("#### crawling : cat_id=",elm,"page_id=",0)
        result = get_onepage_singer_id( str(elm), str(0))
        singer_id = singer_id + result
        # “A-Z”页面，ID为65-90
        for number in range(65,91):
            print("#### crawling : cat_id=",elm,"page_id=",number)
            result = get_onepage_singer_id( str(elm), str(number))
            singer_id = singer_id + result
    print("#### Crawl singer id Succeed #### total singer: ", len(singer_id))
    return ( len(singer_id) )


#######################################################################################################
## 爬取专辑信息，写入数据表：album
## 数据表项格式： ((text)album_id, (text)name, (text)singer_id, (int)status)
## get_all_album_id()：爬取网站全部专辑信息，该函数调用如下两个函数：
##   ==> get_onesinger_album_id(singer_id): 爬取一个歌手（所有分页）的所有专辑信息,并将结果写入数据表album
##      ==> get_onepage_album_id(singer_id, offset): 抓取一个歌手页面上一个分页的专辑信息
#######################################################################################################
# 抓取歌手主页上一个页面的专辑ID
# 返回值：（list）album_record = [ (id, name, singer_id, 0), ]
def get_onepage_album_id(singer_id, offset):
    album_record = []
    url = r'http://music.163.com/artist/album'
    payload = {'id': singer_id, 'offset': offset}
    req = requests.get(url, params=payload, timeout=default_timeout)
    #print(req.url)
    page = BeautifulSoup(req.text, "html.parser")
    # print(page.prettify())
    # 过滤得到专辑名称及ID
    a = page.find_all("a", class_="tit f-thide s-fc0")
    for elm in a:
        href = elm['href'].split('?')
        id = href[1][3:]
        # 将专辑名称的’替换成_
        name = elm.string.replace('\'','_')
        album_record.append( (id , name,singer_id, 0) )
        # album_id[ href[1][3:] ] = elm.string
    return(album_record)

# 抓取一个歌手的所有专辑ID,并将专辑信息写入数据表album，同时更新singer表中该歌手数据项status字段为1
# 返回值：（list）album_record = [ (id, name, singer_id, 0), ]
def get_onesinger_album_id(singer_id):
    album_record = []
    #抓取第一页的专辑
    # print("## crawling ## singer id: ", singer_id, "offset:", '0')
    result = get_onepage_album_id(singer_id, '0')
    album_record = album_record + result
    #分析第一页（offset=0），判断该歌手页面的分页数
    url = r'http://music.163.com/artist/album'
    payload = {'id': singer_id, 'offset': 0}
    req = requests.get(url, params=payload, timeout=default_timeout)
    #print(req.url)
    page = BeautifulSoup(req.text, "html.parser")
    # print(page.prettify())
    # 过滤得到分页offset
    a = page.find_all("a", attrs = {'href' : re.compile(r"offset=[0-9]+"), 'class' : "zpgi"} )
    for elm in a:
        # 抓取该分页专辑ID
        href = elm['href'].split('&')
        offset = href[2][-2:]
        # print("## crawling ## singer id: ", singer_id, "offset:", offset)
        result = get_onepage_album_id(singer_id, str(offset))
        album_record = album_record + result
    print("## result ## singer_id:",singer_id, ", Total album is:", len(album_record) )
    #将结果保存到数据表album
    print("## Write to database...")
    db_api.insert_record("album", "album_id", album_record)
    #更新singer表中该歌手status字段为1，表示已抓取歌手信息
    db_api.updata_records('singer', 'singer_id', singer_id, 'status', 1)
    # #验证数据是否正确写入数据库中
    # db_api.check_records("album", "album_id", album_record)
    return(album_record)

# 爬取网站所有专辑ID
# 先从singer表读取所有歌手ID，然后逐个爬取歌手的专辑信息
def get_all_album_id():
    album_id = []
    #从数据表中读取抓取到的歌手ID，根据歌手ID逐个抓取专辑信息
    temp = db_api.read_one_row('singer', 'singer_id')
    total_singer = len(temp)
    # album_data = db_api.read_one_row('album', 'album_id')
    uncrawled_singer = db_api.search_record('singer', 'status', '0')
    uncrawled_num =  len(uncrawled_singer)
    crawled_num = total_singer - uncrawled_num
    print("#### Total singer: ",total_singer)
    print("#### Uncrawled singer: ",uncrawled_num)

    # 逐个歌手爬取专辑信息
    if uncrawled_num != 0:
        total_album = 0
        for elm in uncrawled_singer:
            singer_id = elm[0]
            # 读取singer表读取该歌手详细记录
            singer_record = db_api.search_record('singer', 'singer_id', singer_id)
            print("### singer id:", singer_record[0][0], "singer name:", singer_record[0][1])
            print("### Crawing...")
            data = get_onesinger_album_id(singer_id)
            album_id = album_id + data
            total_album = total_album +  len(data)
            print(">>>>>>>>>> progress",crawled_num, "of", total_singer, "; Total album:", total_album)
            crawled_num = crawled_num + 1


#######################################################################################################
## 爬取歌曲信息，写入数据表：song
## 数据表项格式（ (text)song_id, (text)name, (text)album_id, (int)total_comment, (text)comment, (int)likecnt )
## get_all_song_comment()：爬取网站全部歌曲信息，该函数调用如下两个函数：
##   ==> get_onesong_comment(song_id): 爬取一首歌曲的评论信息
##   ==> get_onealbum_song_id(album_id): 抓取专辑的歌单（所有歌曲ID）
#######################################################################################################
# 抓取一个专辑上的歌单
# 返回值：（list）song_id = [ (id , name, album_id), ]
def get_onealbum_song_id(album_id):
    song_id = []
    url = r'http://music.163.com/album'
    payload = {'id': album_id}
    req = requests.get(url, params=payload, timeout=default_timeout)
    print(req.url)
    page = BeautifulSoup(req.text, "html.parser")
    # print(page.prettify())
    # 过滤得到歌曲名称及ID
    a = page.find_all("a", href = re.compile(r"song\?id=[0-9]+"))
    for elm in a:
        # print(elm)
        href = elm['href'].split('?')
        id = href[1][3:]
        name = elm.string.replace('\'','_')
        song_id.append( (id , name, album_id) )
    return(song_id)

# 抓取一首歌曲的评论信息
# 调用了comment_api里面的get_one_singer_comment函数
# 返回值：（tuple）song_id = (total_comment , comment, likedcount)
def get_onesong_comment(song_id):
    comment = get_one_singer_comment(song_id)
    # pprint.pprint(comment)
    total_comment = comment['total']
    if len(comment['hotComments']) == 0:
        return (total_comment, "No Hot Comments", 0)
    else:
        top_comment = comment['hotComments'][0]
        return (total_comment, top_comment['content'], top_comment['likedCount'])

# 抓取一个专辑的所有歌曲评论，并写入数据表song
# 先爬取该专辑歌单，然后再进入爬取歌曲评论
def get_one_album_comment(album_id):
    song = []
    album_record = db_api.search_record('album', 'album_id', album_id)
    print "### album id:", album_record[0][0], "album name:", album_record[0][1]
    print "### Crawing album..."
    # 爬取该专辑歌单
    song_record = get_onealbum_song_id(album_id)
    print "### Total song:", len(song_record)
    # pprint.pprint(song_record)
    for connent in song_record:
        song_id = connent[0]
        song_name = connent[1]
        # 爬取该歌曲评论
        comment = get_onesong_comment(song_id)
        print "## song id:", song_id , ", name = ", song_name, ", Total_comments:", comment[0]
        print "## TopComment:", comment[1], ", LikeCount:", comment[2]
        record = (song_id, song_name, album_id, comment[0], comment[1], comment[2])
        print "## Record:", record
        song.append(record)
    #将结果保存到数据表song
    # pprint.pprint(song)
    db_api.insert_record("song", "song_id", song)
    # 更新album表中该专辑的status字段
    db_api.updata_records('album', 'album_id', album_id, 'status', 1)
    #验证数据是否正确写入数据库中
    # print("## Write to database... ")
    # db_api.check_records("song", "song_id", song)

# 抓取网站上所有歌曲评论信息
def get_all_song_comment():
    temp = db_api.read_one_row('album', 'album_id')
    total_album = len(temp)
    print "#### Total album:", total_album
    uncrawled_album = db_api.search_record('album', 'status', '0')
    uncrawled_num = len(uncrawled_album)
    crawled_num = total_album - uncrawled_num
    print "#### Uncrawled album:", uncrawled_num
    # 逐个专辑爬取歌曲评论信息
    if uncrawled_num != 0:
        for elm in uncrawled_album:
            album_id = elm[0]
            get_one_album_comment(album_id)
            crawled_num = crawled_num + 1
            print ">>>>>>>>>> progress",crawled_num, "of", total_album, "; Total album:", total_album


def main():
    #   爬取网易云音乐歌曲评论信息
    # 创建数据库 => 爬取歌手id => 爬取专辑id => 爬取歌曲评论
    db_api.create_database()
    get_all_singer_id()
    get_all_album_id()
    get_all_song_comment()

if __name__ == '__main__':
    main()



###################
#### 测试代码  ####
###################
# category_id = get_category_id()
# pprint.pprint( category_id )

# singer_id = get_onepage_singer_id('6003','0')
# pprint.pprint( singer_id )

# album_id = get_onepage_album_id('6452','0')
# pprint.pprint( album_id )

# album_id = get_onesinger_album_id('2116')
# pprint.pprint( album_id )

# song_id = get_onealbum_song_id('2263029')
# pprint.pprint( song_id )

# r = get_onesong_comment('409941123')
# print (r)