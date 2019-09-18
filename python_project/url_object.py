#!/usr/bin/env python-2.7.3
# -*- coding: utf-8 -*-
########################################################################
#
# Copyright (c) 2019 Baidu.com, Inc. All Rights Reserved
#
########################################################################

"""
File: mini_spider.py
功能 ：使用python开发一个迷你定向抓取器 mini_spider.py ，实现对种子链接的广度优先抓取，并把URL格式符合特定pattern的网页保存到磁盘上
Author: liyixiang(liyixiang@baidu.com)
Date: 2019/09/16
"""

class Url(object):
    """
    this class is used for encapsulating url and depth

    Attributes:
        url   : string of url
        depth : depth of the url
    """

    def __init__(self, url, depth=0):
        self.__url = url
        self.__depth = depth

    def get_url(self):
        """
        get Url-object's url
        """
        return self.__url

    def get_depth(self):
        """
        get Url-object's depth
        """
        return self.__depth
