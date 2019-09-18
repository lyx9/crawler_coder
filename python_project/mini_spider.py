#!/usr/bin/env python
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


import Queue
import threading

import os
import logging
import re

import termcolor

import url_object
import config_args
import crawl_thread

import argparse
import logging

import termcolor

import mini_spider
import log


class MiniSpider(object):
    """
    This class is a crawler-master-class for operating serveral threads

    Attributes:
    checking_url        : urls queue to craw
    check_url           : craled queue url
    config_file_path    : file config_file_path
    error_url           : error urls saved
    self.locl           : threading lock
    """

    def __init__(self,config_file_path='spider.conf'):
        """
        initialize spider variables

        """
        self.checking_url = Queue.Queue(0)
        self.checked_url = set()
        self.error_url = set()
        self.config_file_path = config_file_path
        self.lock = threading.Lock()


    def initialize(self):
        """
        initialize ConfigArgs parameters

        Return:
            True / False :
        """
        config_arg = config_args.ConfigArgs(self.config_file_path)
        is_load = config_arg.initialize()
        if not is_load:
            self.program_end('there is no conf file !')
            return False

        self.url_list_file = config_arg.get_url_list_file()
        self.output_dir = config_arg.get_output_dir()
        self.max_depth = config_arg.get_max_depth()
        self.crawl_interval = config_arg.get_crawl_interval()
        self.crawl_timeout = config_arg.get_crawl_timeout()
        self.target_url = config_arg.get_target_url()
        self.thread_count = config_arg.get_thread_count()
        self.tag_dict = config_arg.get_tag_dict()
        self.url_pattern = re.compile(self.target_url)

        seedfile_is_exist = self.get_seed_url()
        return seedfile_is_exist

    def pre_print(self):
        """
        MiniSpider 创建时显示配置信息
        """
        print termcolor.colored('* MiniSpider Configurations list as follows:', 'green')
        print termcolor.colored('* %-25s : %s' % ('url_list_file   :',
                                                   self.url_list_file),
                                                   'green'
                                                   )

        print termcolor.colored('* %-25s : %s' % ('output_directory:',
                                                   self.output_dir),
                                                   'green'
                                                   )

        print termcolor.colored('* %-25s : %s' % ('max_depth       :',
                                                  self.max_depth),
                                                  'green'
                                                  )

        print termcolor.colored('* %-25s : %s' % ('crawl_interval  :',
                                                  self.crawl_interval),
                                                  'green'
                                                  )

        print termcolor.colored('* %-25s : %s' % ('crawl_timeout   :',
                                                  self.crawl_timeout),
                                                  'green'
                                                  )

        print termcolor.colored('* %-25s : %s' % ('target_url      :',
                                                   self.target_url),
                                                   'green'
                                                   )

        print termcolor.colored('* %-25s : %s' % ('thread_count    :',
                                                  self.thread_count),
                                                  'green'
                                                  )

    def get_seed_url(self):
        """
        get seed url from seedUrlFile

        Returns:
            True / False : 存在种子文件返回True, 否则返回 False
        """
        if not os.path.isfile(self.url_list_file):
            logging.error(' * seedfile is not existing !!!')
            self.program_end('there is no seedfile !')
            return False

        with open(self.url_list_file, 'rb') as f:
            lines = f.readlines()

        for line in lines:
            if line.strip() == '':
                continue

            url_obj = url_object.Url(line.strip(), 0)
            self.checking_url.put(url_obj)
        return True

    def program_end(self, info):
        """
        退出程序的后续信息输出函数

        Args:
            info : 退出原因信息

        Returns:
            none
        """
        print termcolor.colored('* crawled page num : {}'.format(len(self.checked_url)), 'green')
        logging.info('crawled  pages  num : {}'.format(len(self.checked_url)))
        print termcolor.colored('* error page num : {}'.format(len(self.error_url)), 'green')
        logging.info('error page num : {}'.format(len(self.error_url)))
        print termcolor.colored('* finish_reason  :' + info, 'green')
        logging.info('reason of ending :' + info)
        print termcolor.colored('* program is ended ... ', 'green')
        logging.info('program is ended ... ')

    def run_threads(self):
        """
        设置线程池，并启动线程
        """
        args_dict = {}
        args_dict['output_dir'] = self.output_dir
        args_dict['crawl_interval'] = self.crawl_interval
        args_dict['crawl_timeout'] = self.crawl_timeout
        args_dict['url_pattern'] = self.url_pattern
        args_dict['max_depth'] = self.max_depth
        args_dict['tag_dict'] = self.tag_dict

        for index in xrange(self.thread_count):
            thread_name = 'thread - %d' % index
            thread = crawl_thread.CrawlerThread(thread_name,
                                                self.process_request,
                                                self.process_response,
                                                args_dict)

            thread.setDaemon(True)
            thread.start()
            print termcolor.colored(("第%s个线程开始工作") % index, 'yellow')
            logging.info(("第%s个线程开始工作") % index)

        self.checking_url.join()
        self.program_end('normal exits ')

    def is_visited(self, url_obj):
        """
        check new url_obj if visited (including Checked_Url and Error_Url)

        Args:
            url_obj : Url 对象

        Returns:
            True / False  -  若访问过则返回 True ，否则返回 False
        """
        checked_url_list = self.checked_url.union(self.error_url)

        for checked_url_ in checked_url_list:
            if url_obj.get_url() == checked_url_.get_url():
                return True

        return False

    def process_request(self):
        """
        线程任务前期处理的回调函数：
            负责从任务队列checking_url中取出url对象

        Returns:
            url_obj : 取出的url-object 对象
        """
        url_obj = self.checking_url.get()
        return url_obj

    def process_response(self, url_obj, flag, extract_url_list=None):
        """
        线程任务后期回调函数：
            解析HTML源码，获取下一层URLs 放入checking_url

        Args:
            extract_url_list : 返回抽取出的urls集合
            url_obj  : 被下载页面所处的url链接对象
            flag     : 页面下载具体情况的返回标志
                     - 0  : 表示下载成功且为非pattern页面
                     - 1  : 表示下载成功且为符合pattern的图片
                     - -1 : 表示页面下载失败
                     - 2  : depth >= max_depth 的非target - URL
        """
        if self.lock.acquire():
            if flag == -1:
                self.error_url.add(url_obj)

            elif flag == 0:
                self.checked_url.add(url_obj)
                    # link add into Checking_Url
                for ex_url in extract_url_list:
                    next_url_obj = url_object.Url(ex_url, int(url_obj.get_depth()) + 1)
                    if not self.is_visited(next_url_obj):
                        self.checking_url.put(next_url_obj)

            elif flag == 1:
                self.checked_url.add(url_obj)
            self.checking_url.task_done()
        self.lock.release()


if __name__ == '__main__':
    """
    主程序,程序入口
    """

    log.init_log('./log/mini_spider')
    logging.info('%-35s' % ' * miniSpider is starting ... ')
    red_on_cyan = lambda x: termcolor.colored(x, 'red', 'on_cyan')
    # *********************************  start  ***********************
    # set args for the program
    parser = argparse.ArgumentParser(description = 'This is a mini spider program!')
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version='%(prog)s 1.0.0')

    parser.add_argument('-c',
                        '--config_file',
                        action='store',
                        dest='CONF_PATH',
                        default='spider.conf',
                        help='Set configuration file path')

    args = parser.parse_args()

    # create an instance of miniSpider and start crawling
    print red_on_cyan('* MiniSpider is Staring ... ')
    mini_spider_inst = mini_spider.MiniSpider(args.CONF_PATH)
    init_success = mini_spider_inst.initialize()
    if init_success:
        mini_spider_inst.pre_print()
        mini_spider_inst.run_threads()

    # *********************************** end  **************************
    logging.info('%-35s' % ' * miniSpider is ending ...')
    print red_on_cyan('* MiniSpider is ending ... ')
