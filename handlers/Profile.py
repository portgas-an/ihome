import logging

from .BaseHandler import BaseHandler
from utils.commons import required_login
from utils.qiniu_storage import storage
from utils.response_code import RET, error_map
import config


class Profile(BaseHandler):
    @required_login
    def get(self):
        user_id = self.session.data["user_id"]
        try:
            ret = self.db.get("select up_name,up_avatar,up_mobile from ih_user_profile where up_user_id=%(user_id)s",
                              user_id=user_id)
        except Exception as e:
            logging.error(e)
            self.write(dict(errcode=RET.DBERR, msg="查询数据库出错"))
        name = ret["up_name"]
        avatar = config.qiniu_url + ret["up_avatar"]
        mobile = ret["up_mobile"]
        if not avatar:
            avatar = "http://img4.imgtn.bdimg.com/it/u=16550438,2220103346&fm=27&gp=0.jpg"
        self.write(dict(errcode=RET.OK, msg="OK", data={"name": name, "avatar": avatar, "mobile": mobile}))


class AvatarHandler(BaseHandler):
    """上传头像"""

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
        image_url = config.qiniu_url + image_name
        return self.write(dict(errcode=RET.OK, msg={"url": image_url}))


class NameHandler(BaseHandler):
    """上传名字"""
    @required_login
    def post(self):
        user_id = self.session.data["user_id"]
        name = self.json_args.get("name")
        try:
            ret = self.db.execute("update ih_user_profile set up_name=%s where up_user_id=%s", name, user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="upload failed"))
        return self.write(dict(errcode=RET.OK, msg="OK"))


class AuthHandler(BaseHandler):
    """实名认证"""
    @required_login
    def get(self):
        user_id = self.session.data["user_id"]
        try:
            ret = self.db.get("select up_real_name,up_id_card from ih_user_profile where up_user_id=%(user_id)s",
                              user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="查询数据库出错"))
        real_name = ret["up_real_name"]
        id_card = ret["up_id_card"]
        data = {}
        if real_name:
            data["real_name"] = real_name
        if id_card:
            data["id_card"] = id_card
        return self.write(dict(errcode=RET.OK, msg="OK", data=data))

    @required_login
    def post(self):
        user_id = self.session.data["user_id"]
        real_name = self.json_args.get("real_name")
        id_card = self.json_args.get("id_card")
        try:
            ret = self.db.execute("update ih_user_profile set up_real_name=%s,up_id_card=%s where up_user_id=%s",
                                  real_name, id_card, user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="upload failed"))
        return self.write(dict(errcode=RET.OK, msg="OK"))