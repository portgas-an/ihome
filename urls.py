# coding:utf-8
import os

from handlers import VerifyCode
from handlers.BaseHandler import StaticFileHandler
from handlers import Passport
urls = [
    (r'/api/imagecode', VerifyCode.ImageCodeHandler),
    (r'/api/smscode', VerifyCode.PhoneCodeHandler),
    (r'/api/register', Passport.RegisterHandler),
    (r'/(.*)', StaticFileHandler,
     dict(path=os.path.join(os.path.dirname(__file__), "html"), default_filename="index.html"))
]
