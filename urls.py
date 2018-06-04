# coding:utf-8
import os

from handlers import VerifyCode
from handlers.BaseHandler import StaticFileHandler
from handlers import Passport
from handlers import Profile
from handlers import House
urls = [
    (r'/api/imagecode', VerifyCode.ImageCodeHandler),
    (r'/api/smscode', VerifyCode.PhoneCodeHandler),
    (r'/api/register$', Passport.RegisterHandler),
    (r'/api/login$', Passport.LoginHandler),
    (r'/api/check_login$', Passport.CheckLoginHandler),
    (r'/api/logout$', Passport.OutHandler),
    (r'/api/profile$', Profile.Profile),
    (r'/api/profile/avatar$', Profile.AvatarHandler),
    (r'/api/profile/name$', Profile.NameHandler),
    (r'/api/house/area$', House.AreaInfoHandler),
    (r'^/(.*?)$', StaticFileHandler,
     dict(path=os.path.join(os.path.dirname(__file__), "html"), default_filename="index.html")),

]
