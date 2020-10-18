Script started on 2020-10-18 16:20:48-0400
]0;jackson@jackson-Aspire-A515-51: ~/Projects/archive/social_network_database[01;32mjackson@jackson-Aspire-A515-51[00m:[01;34m~/Projects/archive/social_network_database[00m$ python3 run.py 
Welcome to the command line social network.
Type "help" for more information.

>>> user become Alice

>>> user search
screen_name: Obama
name: 
location: 
(ctrl-D on a newline to submit)
description:
created_at_start: 
created_at_end: 
limit: 4
offset: 
+-----------------+---------------------+-------------------------------------+---------------------+
|   screen_name   |      location       |             description             |     created_at      |
+-----------------+---------------------+-------------------------------------+---------------------+
|   BarackObama   |   Washington, DC    | Dad, husband, President, citizen... | 2007-03-05 22:08:25 |
| ObamaFoodorama  |   Washington, DC    | Presidential food/policy histori... | 2008-12-11 19:27:28 |
| ObamaWhiteHouse |   Washington, DC    | This is an archive of an Obama A... | 2009-04-10 21:10:30 |
|    Jobama420    | England, Derbyshire | I'm going to write a book on pro... | 2010-06-06 20:26:45 |
+-----------------+---------------------+-------------------------------------+---------------------+

>>> post search 
screen_name: BarackObama
created_at_start: 
created_at_end: 
(ctrl-D on a newline to submit)
topics:
group_id: 
limit: 10
offset: 
+-------------+-------------------------------------+---------------------+---------------------+
| screen_name |               content               |     created_at      |       post_id       |
+-------------+-------------------------------------+---------------------+---------------------+
| BarackObama | Merry Christmas and happy holida... | 2018-12-19 21:48:12 | 1075508118359076864 |
| BarackObama | There’s no better time than the ... | 2018-12-20 20:55:31 | 1075857251066363905 |
| BarackObama | Enjoy the holiday season with th... | 2018-12-25 14:14:37 | 1077568301281263616 |
| BarackObama | As 2018 draws to a close, I’m co... | 2018-12-28 14:34:43 | 1078660520650174464 |
| BarackObama | As the year winds down and we lo... | 2018-12-29 16:15:18 | 1079048221861634048 |
| BarackObama | Leaders like Dejah Powell, who s... | 2018-12-29 16:15:18 | 1079048223342264320 |
| BarackObama | Leaders like Moussa Kondo and Sa... | 2018-12-29 16:15:19 | 1079048227448475649 |
| BarackObama | Leaders like Hong Hoang, who mob... | 2018-12-29 16:15:20 | 1079048228354457600 |
| BarackObama | Leaders like Jonny Boucher, a Ch... | 2018-12-29 16:15:20 | 1079048229382017024 |
| BarackObama | I hope you find inspiration in t... | 2018-12-29 16:15:20 | 1079048231298883584 |
+-------------+-------------------------------------+---------------------+---------------------+

>>> post tree 1075508118359076864
|- (post_id=1075508118359076864 screen_name=BarackObama, content=Merry Christmas and happy holidays to the extraordinary kids, families, and staff at Children’s National. And thank… https://t.c..., created_at=2018-12-19...)
   |- (post_id=1075571675561783296 screen_name=JessPoint0, content=@BarackObama Ily, created_at=2018-12-20...)
   |- (post_id=1075693355357622272 screen_name=PeanutFreeMom, content=@BarackObama He IS real, you guys!, created_at=2018-12-20...)
   |- (post_id=1239932214374207523 screen_name=jackson, content=Thank you and merry xmas to you!, created_at=2020-10-18...)
   |- (post_id=1239932214374207524 screen_name=Alice, content=Merry xmas, created_at=2020-10-18...)
      |- (post_id=1239932214374207525 screen_name=BarackObama, content=Thank you Alice, created_at=2020-10-18...)
         |- (post_id=1239932214374207526 screen_name=Alice, content=no problem!, created_at=2020-10-18...)
   |- (post_id=1239932214374207527 screen_name=Bob, content=And merry xmas to you, created_at=2020-10-18...)
   |- (post_id=1239932214374207528 screen_name=Bob, content=Merry xmas and happy holidays to you too, created_at=2020-10-18...)

>>> post view 1075508118359076864

created_at: 2018-12-19 21:48:12
screen_name: BarackObama
content: Merry Christmas and happy holidays to the extraordinary kids, families, and staff at Children’s National. And thank… https://t.co/zhMp8GSpfO




>>> post create
parent_id: 1075508118359076864
(ctrl-D on a newline to submit)
content: Merry xmas to you too!
(ctrl-D on a newline to submit)
topics:
group_id: 
[INFO] Created with post_id=1239932214374207529

>>> post tree 1075508118359076864
|- (post_id=1075508118359076864 screen_name=BarackObama, content=Merry Christmas and happy holidays to the extraordinary kids, families, and staff at Children’s National. And thank… https://t.c..., created_at=2018-12-19...)
   |- (post_id=1075571675561783296 screen_name=JessPoint0, content=@BarackObama Ily, created_at=2018-12-20...)
   |- (post_id=1075693355357622272 screen_name=PeanutFreeMom, content=@BarackObama He IS real, you guys!, created_at=2018-12-20...)
   |- (post_id=1239932214374207523 screen_name=jackson, content=Thank you and merry xmas to you!, created_at=2020-10-18...)
   |- (post_id=1239932214374207524 screen_name=Alice, content=Merry xmas, created_at=2020-10-18...)
      |- (post_id=1239932214374207525 screen_name=BarackObama, content=Thank you Alice, created_at=2020-10-18...)
         |- (post_id=1239932214374207526 screen_name=Alice, content=no problem!, created_at=2020-10-18...)
   |- (post_id=1239932214374207527 screen_name=Bob, content=And merry xmas to you, created_at=2020-10-18...)
   |- (post_id=1239932214374207528 screen_name=Bob, content=Merry xmas and happy holidays to you too, created_at=2020-10-18...)
   |- (post_id=1239932214374207529 screen_name=Alice, content=Merry xmas to you too!, created_at=2020-10-18...)

>>> Bye
]0;jackson@jackson-Aspire-A515-51: ~/Projects/archive/social_network_database[01;32mjackson@jackson-Aspire-A515-51[00m:[01;34m~/Projects/archive/social_network_database[00m$ exit
exit

Script done on 2020-10-18 16:21:53-0400
