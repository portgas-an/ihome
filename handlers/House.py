# coding:utf-8

from .BaseHandler import BaseHandler
from utils.response_code import RET
import logging
import constants
import json
from utils.commons import required_login
import config

class AreaInfoHandler(BaseHandler):
    """"""
    def get(self):
        try:
            ret = self.redis.get("area_info").decode('utf-8')
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
           return self.write('{"errcode":%s ,"msg":"OK","data":%s}' % (RET.OK, ret))

        try:
            ret = self.db.query("select ai_area_id,ai_name from ih_area_info")
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="get data error"))
        if not ret:
            return self.write(dict(errcode=RET.NODATA, msg="no area data"))
        areas = []
        for l in ret:
            area ={
                "area_id": l["ai_area_id"],
                "name" : l["ai_name"]
            }
            areas.append(area)
        try:
            self.redis.setex("area_info", constants.AREA_INFO_REDIS_EXPIRES_SECONDS, json.dumps(areas))
        except Exception as e:
            logging.error(e)
        return self.write(dict(errcode=RET.OK, msg="OK", data=areas))


class MyHouseHandler(BaseHandler):
    """"""

    @required_login
    def get(self):
        user_id = self.session.data["user_id"]
        try:
            ret = self.db.query("select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url "
                                "from ih_house_info a left join ih_area_info b on a.hi_area=b.ai_area_id where "
                                "a.hi_user_id=%s", user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="get data errno"))
        houses = []
        if ret:
            for i in ret:
                house = {
                    "house_id": i["hi_house_id"],
                    "title": i["hi_title"],
                    "price": i["hi_price"],
                    "ctime": i["hi_ctime"].strftime("%Y-%m-%d"),
                    "area_name": i["ai_name"],
                    "img_url": config.qiniu_url + i["hi_index_image_url"] if i["hi_index_image_url"] else ""
                }
                houses.append(house)
        return self.write(dict(errcode=RET.OK, msg="OK", houses=houses))


class HouseInfoHandler(BaseHandler):

    def get(self):
        pass

    def post(self):
        """保存"""
        pass