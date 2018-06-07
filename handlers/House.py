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
            area = {
                "area_id": l["ai_area_id"],
                "name": l["ai_name"]
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
                                "from ih_house_info a left join ih_area_info b on a.hi_area_id=b.ai_area_id where "
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

    @required_login
    def post(self):
        """保存"""
        user_id = self.session.data.get("user_id")
        title = self.json_args.get("title")
        price = self.json_args.get("price")
        area_id = self.json_args.get("area_id")
        address = self.json_args.get("address")
        room_count = self.json_args.get("room_count")
        acreage = self.json_args.get("acreage")
        unit = self.json_args.get("unit")
        capacity = self.json_args.get("capacity")
        beds = self.json_args.get("beds")
        deposit = self.json_args.get("deposit")
        min_days = self.json_args.get("min_days")
        max_days = self.json_args.get("max_days")
        facility = self.json_args.get("facility")  # 对一个房屋的设施，是列表类型
        # 校验
        if not all((title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days,
                    max_days)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))
        
        try:
            price = int(price) * 100
            deposit = int(deposit) * 100
        except Exception as e:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))

        # 数据
        try:
            sql = "insert into ih_house_info(hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count," \
                  "hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days) " \
                  "values(%(user_id)s,%(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s," \
                  "%(house_unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s)"
            # 对于insert语句，execute方法会返回最后一个自增id
            house_id = self.db.execute(sql, user_id=user_id, title=title, price=price, area_id=area_id, address=address,
                                       room_count=room_count, acreage=acreage, house_unit=unit, capacity=capacity,
                                       beds=beds, deposit=deposit, min_days=min_days, max_days=max_days)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="save data error"))

        # house_id = 10001
        # facility = ["7", "8", "9", "10"]
        #
        # """
        # hf_id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增id',
        # hf_house_id bigint unsigned NOT NULL COMMENT '房屋id',
        # hf_facility_id int unsigned NOT NULL COMMENT '房屋设施',
        # hf_ctime datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        # """
        # hf_id    hf_house_id    hf_facility_id
        # 1       10001           7
        # 2       10001           8
        # 3       10001           9
        #
        # sql_val = []
        # for facility_id in facility:
        #     sql = "insert into ih_house_facility(hf_house_id, hf_facility_id) " \
        #           "value(%s, %s),(%s, %s),(%s, %s)"
        #     sql_val.append(facility_id)
        #
        # sql_val = tuple(sql_val)
        #     try:
        #         self.db.execute(sql, *sql_val)

        try:
            # for fid in facility:
            #     sql = "insert into ih_house_facility(hf_house_id,hf_facility_id) values(%s,%s)"
            #     self.db.execute(sql, house_id, fid)
            sql = "insert into ih_house_facility(hf_house_id,hf_facility_id) values"
            sql_val = []  # 用来保存条目的(%s, %s)部分  最终的形式 ["(%s, %s)", "(%s, %s)"]
            vals = []  # 用来保存的具体的绑定变量值
            for facility_id in facility:
                # sql += "(%s, %s)," 采用此种方式，sql语句末尾会多出一个逗号
                sql_val.append("(%s, %s)")
                vals.append(house_id)
                vals.append(facility_id)
            sql += ",".join(sql_val)
            vals = tuple(vals)
            logging.debug(sql)
            logging.debug(vals)
            self.db.execute(sql, *vals)
        except Exception as e:
            logging.error(e)
            try:
                self.db.execute("delete from ih_house_info where hi_house_id=%s", house_id)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DBERR, errmsg="delete fail"))
            else:
                return self.write(dict(errcode=RET.DBERR, errmsg="no data save"))
        # 返回
        self.write(dict(errcode=RET.OK, errmsg="OK", house_id=house_id))
