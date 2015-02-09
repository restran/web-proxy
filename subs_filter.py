# -*- coding: utf-8 -*-
# Created on 2014/11/20
__author__ = 'restran'

import re


class SubsFilterRules():
    """
    页面内字符串替换规则，使用正则表达式匹配源字符串
    """

    def __init__(self, re_uri, re_src, str_dst):
        # . 表示匹配除换行符以外的任意字符
        self.re_uri = re_uri  # 正则表达式，要替换的页面URI
        self.re_src = re_src  # 匹配的正则表达式
        self.str_dst = str_dst  # 替换后的目标字符串


class SubsFilter():
    """
    页面内字符串替换，使用正则表达式匹配源字符串
    """

    @classmethod
    def exec_filter(cls, uri, body, rules):
        for r in rules:
            re_uri, re_src, str_dst = r.re_uri, r.re_src, r.str_dst
            pattern = re.compile(re_uri)
            match = pattern.search(uri)
            if match:
                # 将正则表达式编译成Pattern对象
                pattern = re.compile(re_src)
                body = pattern.sub(str_dst, body)

        return body

