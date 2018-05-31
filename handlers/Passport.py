# coding:utf-8

from .BaseHandler import BaseHandler
import logging
from utils.response_code import RET, error_map
import hashlib
import config
from utils.session import Session


class RegisterHandler(BaseHandler):
    def post(self):
        mobile = self.json_args.get("mobile")
        sms_code = self.json_args.get("phonecode")
        password = self.json_args.get("password")
        if not all((mobile, sms_code, password)):
            return self.write(dict(errcode=RET.PARAMERR, msg=error_map.PARAMERR))
        real_code = self.redis.get("sms_code_%s" % mobile).decode('utf-8')
        if real_code != str(sms_code):
            return self.write(dict(errcode="2", msg="验证码无效"))
        password = hashlib.sha256((config.passwd_hash_key + password).encode("utf8")).hexdigest()
        try:
            res = self.db.execute("insert into ih_user_profile(up_name, up_mobile,up_passwd) "
                                  "values(%(name)s, %(mobile)s, %(passwd)s)",
                                 name=mobile, mobile=mobile, passwd=password)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode="3", msg="用户已存在"))
        try:
            self.session = Session(self)
            self.session.data['user_id'] = res
            self.session.data['name'] = mobile
            self.session.data['mobile'] = mobile
            self.session.save()
        except Exception as e:
            logging.error(e)
        self.write(dict(errcode=RET.OK, msg="OK"))


class LoginHandler(BaseHandler):
    def post(self):
        mobile = self.json_args.get("mobile")
        password = self.json_args.get("password")
        if not all((mobile, password)):
            return self.write(dict(errcode=RET.PARAMERR, msg=error_map.PARAMERR))
        res = self.db.get("select up_user_id,up_name,up_passwd from ih_user_profile"
                          "where up_mobile=%(mobile)s", mobile=mobile)
        password = hashlib.sha256(config.passwd_hash_key+password).hexdigest()
        if res and res["up_passwd"] == password:
            try:
                self.session = Session(self)
                self.session.data['user_id'] = res['up_user_id']
                self.session.data['name'] = res['up_name']
                self.session.data['mobile'] = mobile
                self.session.save()
            except Exception as e:
                logging.error(e)
            return self.write(dict(errcode=RET.OK, msg="OK"))
        else:
            return self.write(dict(errcode='2', msg="手机号或密码错误"))


class CheckLoginHandler(BaseHandler):
    """检查登陆状态"""

