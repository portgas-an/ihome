# -*- coding:utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
from tornado.options import define, options
from urls import urls
import config
import torndb
import redis

define("port", type=int, default=8080, help="run server on the given port")


class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        # self.db = torndb.Connection(
        #     host=config.mysql_options["host"],
        #     database=config.mysql_options["database"],
        #     user=config.mysql_options["user"],
        #     password=config.mysql_options["password"]
        # )
        self.db = torndb.Connection(**config.mysql_options)
        # self.redis = redis.StrictRedis(
        #     host=config.redis_options["host"]
        # )
        self.redis = redis.StrictRedis(**config.redis_options)


def main():
    options.logging = "debug"
    options.log_file_prefix = config.log_file
    tornado.options.parse_command_line()
    app = Application(urls, **config.setting)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
