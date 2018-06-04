# coding:utf-8

from .BaseHandler import BaseHandler
from utils.response_code import RET
import logging
import constants
import json


class AreaInfoHandler(BaseHandler):
    """"""
    def get(self):
        try:
            ret = self.redis.get("area_info").decode('utf-8')
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
           logging.debug(ret)
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