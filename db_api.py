# -*- coding: utf-8 -*-

## 对数据库进行操作
## HuangZhe
## 2016.4.21
import sqlite3

##数据库名
database = "cloudmusic.db"
# database = "test.db"

#建立数据库及数据表
def create_database():
    conn = sqlite3.connect( database )
    curs = conn.cursor()
    #建立歌手信息表：singer, 用if not exists来判断表是否存在
    curs.execute('''CREATE TABLE IF NOT EXISTS singer
      (singer_id text,
      name text,
      status int)''')
    #建立专辑信息表：album,
    curs.execute('''CREATE TABLE IF NOT EXISTS album
      (album_id text,
      name text,
      singer_id text,
      status int,
      FOREIGN KEY (singer_id) REFERENCES singer(singer_id))''')
    #建立歌曲信息表：song,
    curs.execute('''CREATE TABLE IF NOT EXISTS song
      (song_id text,
      name text,
      album_id text,
      total_comment int,
      comment text,
      likecnt int,
      FOREIGN KEY (album_id) REFERENCES album(album_id))''')
    #打印数据表名
    curs.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")
    print ( curs.fetchall() )
    conn.commit()
    conn.close()


# 向数据表中插入记录（插入之前先查询（通过记录第一个字段），如果记录已存在，则不执行插入操作
# table：数据表名； key：记录的第一个字段名称； records： 要插入的记录
def insert_record(table, key, records):
    conn = sqlite3.connect( database )
    curs = conn.cursor()
    for elm in records:
        # print "record:",elm
        # 从records提取信息，生成SQL查询指令
        sel_cmd = 'SELECT key FROM table WHERE key = data'
        sel_cmd = sel_cmd.replace("table", table)
        sel_cmd = sel_cmd.replace("key", key)
        sel_cmd = sel_cmd.replace("data", elm[0])
        # 先执行一次查询指令，判断记录是否已经存在
        # print("# SQL cmmond: ", sel_cmd )
        curs.execute(sel_cmd)
        # 查询结果长度为0：不存在记录，可以插入；查询结果长度为1：记录已经存在，不插入
        if ( len(curs.fetchall()) == 0 ):
            #提取要插入的记录的具体内容，生产符合SQL要求的格式
            record = "("
            for content in elm:
                # 整型数据转换成字符串
                if isinstance(content, int):
                    # print content
                    record = record + str(content) + ','
                else:
                    # 字符数据，将特殊字符(暂时只发现’和\x00)转换成_，否则会出现错误
                    content = content.replace("\'", "_")
                    content = content.replace("\x00", "_")
                    record = record + '\'' + content + '\','
                # print content
            # print "record:", record
            # 将record的最后一个字符，替换成），保持到data
            data = record[:-1] + ")"
            print "# Data: ", data

            # 生成SQL插入指令
            ins_cmd = 'INSERT INTO table VALUES ' + data
            ins_cmd = ins_cmd.replace("table", table)
            print("# SQL cmmond: ", ins_cmd )
            curs.execute(ins_cmd)
    conn.commit()
    conn.close()


# 从数据表中读出一列数据（用来读取歌手ID， 专辑ID）
# table：数据表名； key：要读出的字段名称
def read_one_row(table, key):
    conn = sqlite3.connect( database )
    curs = conn.cursor()
    cmd = '''SELECT keyword FROM table'''
    cmd = cmd.replace('keyword', key)
    cmd = cmd.replace('table', table)
    # print(cmd)
    curs.execute( cmd )
    result = curs.fetchall()
    # print(result)
    conn.close()
    return(result)


# 根据关键字内容查询，返回该记录项
def search_record(table, key, content):
    conn = sqlite3.connect( database )
    curs = conn.cursor()
    cmd = '''SELECT * FROM table WHERE keyword = content'''
    cmd = cmd.replace('keyword', key)
    cmd = cmd.replace('table', table)
    cmd = cmd.replace('content', content)
    # print("# SQL cmmond: ", cmd )
    curs.execute( cmd )
    result = curs.fetchall()
    conn.close()
    return(result)


#验证抓取到的数据是否成功写入数据表中
#table:数据表名, key:数据表字段名， records:要验证的数据项
def check_records(table, key, records):
    flag = 0
    for elm in records:
        data = search_record(table, key, elm[0])
        if elm != data[0]:
            print("## Error!! ## Can't find record in database!!")
            print("## record=",elm,"database=",data[0])
            flag = 1
    if ( flag==0 ):
        print("## Check database record correct!")
    return


# 更新数据表中的记录
def updata_records(table, search_key, search_content, updata_key, updata_contenr):
    conn = sqlite3.connect( database )
    curs = conn.cursor()
    cmd = '''UPDATE table SET updata_key = updata_contenr WHERE search_key = search_content '''
    cmd = cmd.replace('table', table)
    cmd = cmd.replace('updata_key', updata_key)
    cmd = cmd.replace('updata_contenr', str(updata_contenr))
    cmd = cmd.replace('search_key', search_key)
    cmd = cmd.replace('search_content', search_content )
    print("# SQL cmmond: ", cmd )
    curs.execute( cmd )
    conn.commit()
    conn.close()
    return()


#获取数据库中已存在的数据表名称并打印出来
def get_table_name():
    conn = sqlite3.connect( database )
    curs = conn.cursor()
    curs.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")
    print ( curs.fetchall() )
    conn.commit()
    conn.close()


# create_database()
# result = search_record("singer", "singer_id", "196134")
# print(result)
#
# updata_records("singer", "singer_id", "196134", "status", 0)
#
# result = search_record("singer", "singer_id", "196134")
# print(result)