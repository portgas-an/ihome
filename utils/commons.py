# coding:utf-8

import functools

from utils.session import Session
from utils.response_code import RET


def required_login(fun):
    # 保证被装饰的函数对象的__name__不变
    @functools.wraps(fun)
    def wrapper(request_handler_obj, *args, **kwargs):
        # 调用get_current_user方法判断用户是否登录
        if not request_handler_obj.get_current_user():
            # session = Session(request_handler_obj)
            # if not session.data:
            request_handler_obj.write(dict(errcode=RET.SESSIONERR, errmsg="用户未登录"))
        else:
            fun(request_handler_obj, *args, **kwargs)


    return wrapper

#
# def dec(f):
#     @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         print("hello")
#         f(*args, **kwargs)
#     return wrapper
#
#
# @dec
# def add_two(num1, num2):
#     return num1 + num2
#
#
# @dec
# def add_three(num1, num2, num3):
#     return num1 + num2 + num3
#
#
# def main():
#     a, b, c = 1, 2, 3
#     add_two(a, b)
#     add_three(a, b, c)
#
#
# if __name__ == '__main__':
#     main()


