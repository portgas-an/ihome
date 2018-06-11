# coding:utf-8

from .BaseHandler import BaseHandler
from utils.response_code import RET
import logging
import constants
import json
from utils.commons import required_login
import config
from utils.qiniu_storage import storage
import math


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


class HouseImageHandler(BaseHandler):
    @required_login
    def post(self):
        try:
            house_id = self.get_argument("house_id")
            house_id = 2
            house_image = self.request.files["house_image"][0]["body"]
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, msg="参数错误"))
        image_url = storage(house_image)
        if not image_url:
            return self.write(dict(errcode=RET.THIRDERR, msg="七牛存储错误"))
        try:
            # 将上传的七牛图片地址存储到数据库里面去,用户的第一张图片作为房屋的封面
            sql = "insert into ih_house_image(hi_house_id,hi_url) values(%s,%s);" \
                  "update ih_house_info set hi_index_image_url=%s " \
                  "where hi_house_id=%s and hi_index_image_url is null;"
            self.db.execute(sql, house_id, image_url, image_url, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="数据库错误"))
        image_url = config.qiniu_url + image_url
        self.write(dict(errcode=RET.OK, msg="OK", data=image_url))


class HouseInfoHandler(BaseHandler):
    @required_login
    def get(self):
        """获取房屋信息"""
        house_id = self.get_argument("house_id")
        if not house_id:
            return self.write(dict(errcode=RET.PARAMERR, msg="参数错误"))
        # 查询redis
        try:
            ret = self.redis.get("house_info_%s" % house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            ret = ret.decode("utf-8")
            data = json.loads(ret)
            return self.write(dict(errcode=RET.OK, msg="OK", data=data))
        # 查询数据库
        sql = "select hi_title,hi_price,hi_address,hi_room_count,hi_acreage,hi_house_unit,hi_capacity,hi_beds," \
              "hi_deposit,hi_min_days,hi_max_days,up_name,up_avatar,hi_user_id " \
              "from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id where hi_house_id=%s"
        try:
            ret = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="数据库错误"))
        if not ret:
            return self.write(dict(errcode=RET.NODATA, msg="查无此房"))
        data = {
            "hid": house_id,
            "user_id": ret["hi_user_id"],
            "title": ret["hi_title"],
            "price": ret["hi_price"],
            "address": ret["hi_address"],
            "room_count": ret["hi_room_count"],
            "acreage": ret["hi_acreage"],
            "unit": ret["hi_house_unit"],
            "capacity": ret["hi_capacity"],
            "beds": ret["hi_beds"],
            "deposit": ret["hi_deposit"],
            "min_days": ret["hi_min_days"],
            "max_days": ret["hi_max_days"],
            "user_name": ret["up_name"],
            "user_avatar": config.qiniu_url + ret["up_avatar"] if ret.get("up_avatar") else ""
        }
        # 查询房屋的图片信息
        sql = "select hi_url from ih_house_image where hi_house_id=%s"
        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        images = []
        if ret:
            for image in ret:
                images.append(config.qiniu_url + image["hi_url"])
        data["images"] = images

        # 查询房屋基础设施
        sql = "select hf_facility_id from ih_house_facility where hf_house_id =%s"
        try:
            ret = self.db.execute(sql,house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        facilities = []
        if ret:
            for facilitie in facilities:
                facilities.append(facilitie["hf_facility_id"])
        data["facilities"] = facilities
        # 查询评论信息
        sql = "select oi_comment,up_name,oi_utime,up_mobile from ih_order_info inner join ih_user_profile " \
              "on oi_user_id=up_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null"
        try:
            ret = self.db.query(sql,house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        comments = []
        if ret:
            for comment in ret:
                comments.append(dict(
                    user_name=comment["up_name"] if comment["up_name"] != comment["up_mobile"] else "匿名用户",
                    content=comment["oi_comment"],
                    ctime=comment["oi_utime"].strftime("%Y-%m-%d %H:%M:%S")
                ))
        data["comments"] = comments
        json_data = json.dumps(data)
        try:
            self.redis.setex("house_info_%s" % house_id, constants.REDIS_HOUSE_INFO_EXPIRES_SECONDES, json_data)
        except Exception as e:
            logging.error(e)
        self.write(dict(errcode=RET.OK, msg="OK", data=data))

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
            return self.write(dict(errcode=RET.PARAMERR, msg="缺少参数"))

        try:
            price = int(price) * 100
            deposit = int(deposit) * 100
        except Exception as e:
            return self.write(dict(errcode=RET.PARAMERR, msg="参数错误"))

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
            return self.write(dict(errcode=RET.DBERR, msg="save data error"))

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
                return self.write(dict(errcode=RET.DBERR, msg="delete fail"))
            else:
                return self.write(dict(errcode=RET.DBERR, msg="no data save"))
        # 返回
        self.write(dict(errcode=RET.OK, errmsg="OK", house_id=house_id))


class HouseList(BaseHandler):
    """"""

    def get(self):
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        area_id = self.get_argument("aid", "")
        sort_key = self.get_argument("sk", "new")
        page = self.get_argument("p", 1)
        page = int(page)

        # 查询数据库
        sql = "select distinct hi_house_id,hi_title,hi_price,hi_room_count,hi_order_count,hi_index_image_url," \
              "hi_address,up_avatar,hi_ctime,hi_order_count,hi_price from ih_house_info left join ih_order_info " \
              "on hi_house_id = oi_house_id  inner join ih_user_profile on hi_user_id = up_user_id "
        sql_where = []
        sql_params = {}
        if start_date and end_date:
            sql_where.append("(not (oi_begin_date < %(end_date)s and oi_end_date > %(start_date)s))")
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date
        elif start_date:
            sql_where.append("(oi_end_date < %(start_date)s)")
            sql_params["start_date"] = start_date
        elif end_date:
            sql_where.append("(oi_begin_date < %(end_date)s)")
            sql_params["end_date"] = end_date
        if area_id:
            sql_where.append("(hi_area_id = %(area_id)s)")
            sql_params["area_id"] = area_id
        if sql_where:
            sql += "where"
            sql += "and ".join(sql_where)
        if "new" == sort_key:
            sql += "order by hi_ctime desc "
        elif "hot" == sort_key:
            sql += "order by hi_order_count desc "
        elif "pri-inc" == sort_key:
            sql += "order by hi_price asc "
        elif "pri-des" == sort_key:
            sql += "order by hi_price desc "
        if page == 1:
            sql += "limit %s" % constants.HOUSE_LIST_PAGE_CAPACITY
        else:
            sql += "limit %s,%s" % ((page - 1) * constants.HOUSE_LIST_PAGE_CAPACITY, constants.HOUSE_LIST_PAGE_CAPACITY)

        try:
            ret = self.db.query(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, msg="查询出错"))
        houses = []
        if ret:
            for i in ret:
                house = {
                    "house_id": i["hi_house_id"],
                    "title": i["hi_title"],
                    "price": i["hi_price"],
                    "room_count": i["hi_room_count"],
                    "order_count": i["hi_order_count"],
                    "address": i["hi_address"],
                    "image_url": config.qiniu_url + i["hi_index_image_url"] if i["hi_index_image_url"] else "",
                    "avatar": config.qiniu_url + i["up_avatar"] if i["up_avatar"] else ""
                }
                houses.append(house)
        cur_page_data = houses[:constants.HOUSE_LIST_PAGE_CAPACITY]

        i = 1
        while 1:
            data = houses[i * constants.HOUSE_LIST_PAGE_CAPACITY:(i + 1) * constants.HOUSE_LIST_PAGE_CAPACITY]
            if not data:
                break
            i += 1
        sql = "select count(*) counts from ih_house_info left join ih_order_info on hi_house_id = oi_house_id"
        if sql_where:
            sql += "where"
            sql += "and".join(sql_where)
        try:
            ret = self.db.get(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            total_page = -1
        else:
            total_page = int(math.ceil(ret["counts"] / float(constants.HOUSE_LIST_PAGE_CAPACITY)))
        self.write(dict(errcode=RET.OK, msg="OK", data=cur_page_data, total_page=total_page))
