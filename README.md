
# 项目简介
* Python爬虫，爬取网易云音乐上所有歌曲页面下，“精彩评论”中点赞数第一的评论，保存到数据库。
* 使用前先更改config.py文件，配置自己的网易云音乐账号。

# 开发环境
* Python版本：python2.7  
* 数据库：SQLite

# 文件结构
* config.py : 配置网易云音乐用户名、密码  
* comment_api.py : 获取歌曲评论的API，From Zhihu。  
* db_api.py : 对数据库进行操作的API。  
* cloudmusic.py ：网易云音乐评论爬虫(单线程)。
* cloudmusic_multhread.py ：网易云音乐评论爬虫（多线程）。

# 数据表格式
表一：歌手信息表 singer  
数据项内容：( (text)singer_id, (text)name, (int)status)  
singer_id: 歌手ID。  
name：歌手名称  
state : 该歌手专辑信息爬取状态。0：没爬取，1：已经爬取（并保存到album表）。  

表二：专辑信息表album  
数据项内容：((text)album_id, (text)name, (text)singer_id, (int)status)  
album_id：专辑ID。  
name：专辑名称。  
singer_id：该专辑的歌手ID。  
state : 爬取状态，0：没爬取，1：已经爬取（并保存到song表）。 

表三：歌曲信息表song（每首歌曲保存一个点赞数最多的评论）  
数据项内容：((text)song_id, (text)name, (text)album_id, (int)total_comment, (text)comment, (int)likecnt )  
song_id：歌曲ID。  
name：歌曲名称。  
album_id：该歌曲所属专辑ID。  
total_comment：该歌曲评论总数。  
comment：该歌曲页面下点赞数最高的一个评论。  
likecnt：该评论的点赞数。  
