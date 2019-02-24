#!/usr/bin/env python
# coding=utf-8

import os
import urllib
import json
import re

import multiprocessing
import requests
from lxml import etree
import fire
from loguru import logger
logger.add("logs/%s.log" % __file__.rstrip('.py'), format="{time:MM-DD HH:mm:ss} {level} {message}")

import aria2p
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6810,
        secret="enter"
    )
)

headers = {
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
}

def list_page(url):
    logger.info('crawling : %s' % url)
    resp = requests.get(url, headers=headers)
    html = etree.HTML(resp.text)
    vkeys = html.xpath('//*[@class="phimage"]/div/a/@href')
    gif_keys = html.xpath('//*[@class="phimage"]/div/a/img/@data-mediabook')
    # jobs = []
    for i in range(len(vkeys)):
        item = {}
        item['vkey'] = vkeys[i].split('=')[-1]
        item['gif_url'] = gif_keys[i]
        try:
            if 'ph' in item['vkey']:
                # jobs.append(gevent.spawn(download, item['gif_url'], item['vkey'],'webm'))
                p = multiprocessing.Process(target=download, args=(item['gif_url'], item['vkey'], 'webm'))
                p.start()
        except Exception as err:
            logger.error(err)
    # gevent.joinall(jobs, timeout=2)


def detail_page(url):
    s = requests.Session()
    resp = s.get(url, headers=headers)
    html = etree.HTML(resp.content)
    title = ''.join(html.xpath('//h1//text()')).strip()

    js = html.xpath('//*[@id="player"]/script/text()')[0]
    tem = re.findall('var\\s+\\w+\\s+=\\s+(.*);\\s+var player_mp4_seek',js)[-1]
    con = json.loads(tem)

    for _dict in con['mediaDefinitions']:
        if 'quality' in _dict.keys() and _dict.get('videoUrl'):
            logger.info('%s %s' % (_dict.get('quality'), _dict.get('videoUrl')))
            try:
                download(_dict.get('videoUrl'), title, 'mp4')
                break  # 如下载了较高分辨率的视频 就跳出循环
            except Exception as err:
                logger.error(err)


def download(url, name, filetype):
    filepath = '%s/%s.%s' % (filetype, name, filetype)
    if os.path.exists(filepath):
        logger.info('this file had been downloaded :: %s' % filepath)
        return
    aria2.add_uris([url], options={
        "out": '%s.%s' % (name, filetype),
        "dir": '%s/%s' % (os.getcwd(), filetype)
    })
    logger.info('download success :: %s' % filepath)


def run(_arg=None):
    paths = ['webm', 'mp4']
    for path in paths:
        if not os.path.exists(path):
            os.mkdir(path)
    if _arg == 'webm':
        # https://www.pornhub.com/categories
        urls = [
            'https://www.pornhub.com/video?o=tr',
            'https://www.pornhub.com/video?o=ht',
            'https://www.pornhub.com/video?o=mv',
            'https://www.pornhub.com/video'
        ]
        # jobs = [gevent.spawn(list_page, url) for url in urls]
        # gevent.joinall(jobs)
        for url in urls:
            p = multiprocessing.Process(target=list_page, args=(url, ))
            p.start()
    elif _arg == 'mp4':
        with open('download.txt', 'r') as file:
            keys = list(set(file.readlines()))
        # jobs = []
        for key in keys:
            if not key.strip():
                continue
            url = 'https://www.pornhub.com/view_video.php?viewkey=%s' % key.strip()
            logger.info('url: {}', url)
            # jobs.append(gevent.spawn(detail_page, url))
            p = multiprocessing.Process(target=detail_page, args=(url, ))
            p.start()
        # gevent.joinall(jobs, timeout=2)
    else:
        _str = """
tips:
    python crawler.py webm
        - 下载热门页面的缩略图，路径为webm文件夹下

    python crawler.py mp4
        - 将下载的webm文件对应的以ph开头的文件名逐行写在download.txt中，运行该命令
        """
        logger.info(_str)
    logger.info('Using multiprocessing, commands send to system, please wait a moment.')
    logger.info('Maybe there is some error, leave it alone.')


if __name__ == '__main__':
    fire.Fire(run)
