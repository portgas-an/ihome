# coding:utf-8
import logging

from .BaseHandler import BaseHandler
from utils.commons import required_login
from utils.qiniu_storage import storage
from utils.response_code import RET,error_map


class AvatarHandler(BaseHandler):
    """"""

    @required_login
    def post(self):
        user_id = self.session.data["user_id"]
        try:
            image = self.request.files["avatar"][0]["body"]
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.PARAMERR, msg="参数错误"))
        try:
            image_name = storage(image)
        except Exception as e:
            logging.error(e)
            image_name = None
        if not image_name:
            return self.write(dict(errcode=RET.THIRDERR, msg=error_map[RET.THIRDERR]))
        try:
            ret = self.db.execute("update ih_user_profile set up_avatar=%s where up_user_id=%s", image_name, user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="upload failed"))
        image_url = "" + image_name
        return self.write(dict(errcode=RET.OK, msg="OK", data=image_url))
