# coding:utf-8
from handlers.BaseHandler import BaseHandler
from utils.commons import required_login
from utils.response_code import RET
import logging


class OrderHandler(BaseHandler):
    """订单"""
    @required_login
    def post(self):
        user_id = self.session.data["user_id"]
        house_id = self.json_args.get("house_id")
        start_time = self.json_args.get("start_date")
        end_time = self.json_args.get("end_date")
        # 参数检查
        if not all((house_id, start_time, end_time)):
            return self.write(dict(errcode=RET.PARAMERR, msg="参数错误"))
        try:
            house = self.db.get("select hi_price, hi_user_id from ih_house_info where hi_house_id=%s ")
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="查询出错"))
        if not house:
            return self.write(dict(errcode=RET.NODATA, msg="没有房屋信息"))
        if user_id == house["hi_user_id"]:
            return self.write(dict(errcode=RET.ROLEERR, msg="用户禁止"))
