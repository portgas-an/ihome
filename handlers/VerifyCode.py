# coding:utf-8

from .BaseHandler import BaseHandler
import logging
from utils.captcha import captcha
import constants
from utils.response_code import RET
import random


class ImageCodeHandler(BaseHandler):
    def get(self):
        code_id = self.get_argument('codeid')
        pre_code_id = self.get_argument("pcodeid")
        if pre_code_id:
            try:
                self.redis.delete("image_code_%s" %pre_code_id)
            except Exception as e:
                logging.error(e)
        # name 图片验证码名称
        # text 图片验证码文本
        # image 图片二维码二进制数据
        name, text, image = captcha.captcha.generate_captcha()
        try:
            self.redis.setex("image_code_%s" % code_id, constants.IMAGE_CODE_EXPIRES_SECONDS, text)
        except Exception as e:
            logging.error(e)
            self.write("")
        self.set_header("Content-Type", "image/jpg")
        self.write(image)


class PhoneCodeHandler(BaseHandler):
    """"""
    def post(self):
        # 获取参数
        mobile = self.json_args.get("mobile")
        image_code_id = self.json_args.get("image_code_id")
        image_code_text = self.json_args.get("image_code_text")
        if not all((mobile, image_code_id, image_code_text)):
            return self.write(dict(errcode=RET.PARAMERR, msg="参数不完整"))
        # 判断图片验证码
        try:
            real_image_code_text = self.redis.get("image_code_%s" % image_code_id)
        except Exception:
            return self.write(dict(errcode=RET.DBERR, msg="查询出错"))
        if not real_image_code_text:
            return self.write(dict(errcode=RET.DATAERR, msg="验证码过期"))
        # 成功发送信息,失败返回错误信息
        sms_code = "%04d" % random.randint(0, 9999)
        try:
            self.redis.setex("sms_code_%s" % mobile, constants.SMS_CODE_EXPIRES_SECDONS, sms_code)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="生成验证码错误"))
        # 发送短信
        return self.write(dict(errcode=RET.OK, msg=sms_code))
