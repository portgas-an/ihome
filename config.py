# coding:utf-8

import os
# Application配置文件
setting = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "template_path": os.path.join(os.path.dirname(__file__), "html"),
    "cookie_secret": "lvP2jGfDTeKqm9oekT0LR+DBsSojQEYTp7ZJlKM79jo=",
    "xsrf_cookies": True,
    "debug": True,
}

# mysql
mysql_options = dict(
    host="127.0.0.1:3306",
    database="ihome",
    user="root",
    password="12345",
)

# redis
redis_options = dict(
    host="127.0.0.1",
)

# log
log_file = os.path.join(os.path.dirname(__file__), "logs/log")


# session有效期
session_expires = 86400

# 密码加密key
passwd_hash_key = "nlgCjaTXQX2jpupQFQLoQo5N4OkEmkeHsHD9+BBx2WQ="

# 七牛外链地址
qiniu_url = "http://p9sat71l4.bkt.clouddn.com/"