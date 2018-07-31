#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    : 2018/6/5 上午10:58
# @Author  : YouMing
# @Email   : myoueva@gmail.com
# @File    : requests_re_test.py
# @Software: PyCharm
# @license : copyright © 2015-2016

import requests
import sys
import collections
import re
import os
import struct
import sys
import zlib
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from fontTools.ttLib import TTFont


class SpiderMo(object):
    """get movie top from maoyan.com"""
    web_site = 'http://maoyan.com'
    board = ['board']
    section = [7, 6, 1, 2, 4]
    number_dict = {
        '&#xe398;': 0,
        '&#xef64;': 1,
        '&#xe1bb;': 2,
        '&#xe4e6;': 3,
        '&#xf7f1;': 4,
        '&#xf6b5;': 5,
        '&#xf511;': 6,
        '&#xe702;': 7,
        '&#xf76f;': 8,
        '&#xf2ce;': 9
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36'
    }
    def __init__(self, url_section):
        self.end = url_section

    def get_html_text(self, page_index):
        url = '{}/{}/{}?offset={}'.format(SpiderMo.web_site, SpiderMo.board[0], self.end, (int(page_index)-1)*10)
        try:
            response = requests.get(url, headers=SpiderMo.headers)
            html_code = response.text
            return html_code
        except RequestException as e:
            return None

    def font_ttf(self, font_name):
        font_path = os.path.abspath(os.path.join(os.getcwd(), 'fonts'))
        if not os.path.exists(font_path):
            os.makedirs(font_path)
        font_list = os.listdir(font_path)
        font_mac_list = os.listdir('./fonts')
        if font_name not in font_list:
            print('download font-style')
            font_url = 'http://vfile.meituan.net/colorstone/' + font_name + '.woff'
            response = requests.get(font_url, headers=SpiderMo.headers).content
            with open(os.path.join(font_path, font_name + '.woff'), 'wb') as f:
                f.write(response)
            WoffToOtf.convert(os.path.join(font_path, font_name + '.woff'), os.path.join(font_path, font_name + '.otf'))
            base_content = TTFont(os.path.join(font_path, 'base.otf'))
            font_content = TTFont(os.path.join(font_path, font_name + '.otf'))
            nui_list = font_content['cmap'].tables[0].ttFont.getGlyphOrder()
            num_List = []
            baseNumList = ['.', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
            baseUniCode = ['x', 'uniE516', 'uniF64C', 'uniF623', 'uniF866', 'uniF12D', 'uniEE25',
                           'uniF59D', 'uniE3CE', 'uniF15B', 'uniF40C']
            for i in range(1, 12):
                maoyanGlyph = font_content['glyf'][nui_list[i]]
                for j in range(11):
                    baseGlyph = base_content['glyf'][baseUniCode[j]]
                    if maoyanGlyph == baseGlyph:
                        num_List.append(baseNumList[j])
                        break
            return num_List[1:], font_content.glyphOrder[2:]

    def analysis_data(self, page_index):
        # the single movie info class
        attr_name = ['img', 'title', 'roles', 'year', 'index']
        if self.end in [4, 7]:
            attr_name += ['score']
        elif self.end in [1, 2]:
            attr_name += ['real_time', 'total_time']
        elif self.end in [6]:
            attr_name += ['mouth_wish', 'total_wish']

        movie_info = collections.namedtuple('movie_info', attr_name)
        text = self.get_html_text(page_index)
        if not text:
            raise Exception('have no data,pls check page_index')
        font_list = re.findall(r"colorstone/(.*?).woff", text, re.S)[0].split('/')[-1:]
        num, uni = self.font_ttf(font_list[0])
        for key, value in enumerate(uni):
            value = str(value).replace('uni', '&#x').lower()
            text = text.replace(value, num[key])
        soup = BeautifulSoup(text, 'lxml')
        # font_name = soup.select('style')[0].string
        # font_list = re.findall(r"colorstone/(.*?).woff", font_name, re.S)[0].split('/')[-1:]
        # num, uni = self.font_ttf(font_list[0])
        dl_list = soup.select('dl.board-wrapper dd')
        movies = []
        for dd in dl_list:
            borad_dic = dict()
            m_index = dd.select('i.board-index')[0].get_text().strip() if len(dd.select('i.board-index')) != 0 else None
            borad_dic['index'] = m_index
            m_img = dd.select('img.board-img')[0].attrs['data-src'] if len(dd.select('img.board-img')) != 0 else None
            borad_dic['img'] = m_img
            m_title = dd.select('p.name')[0].contents[0].get_text().strip() if len(dd.select('p.name')) != 0 else None
            borad_dic['title'] = m_title
            m_roles = dd.select('p.star')[0].get_text().strip()[3:] if len(dd.select('p.star')) != 0 else None
            borad_dic['roles'] = m_roles
            m_year = dd.select('p.releasetime')[0].get_text().strip()[5:] if len(dd.select('p.releasetime')) != 0 else None
            borad_dic['year'] = m_year
            if self.end in [4, 7]:
                m_h = dd.select('i.integer')[0].get_text().strip()
                m_m = dd.select('i.fraction')[0].get_text().strip()
                m_score = m_h + m_m
                borad_dic['score'] = m_score
            elif self.end in [1, 2]:
                m_real_time = dd.select('p.realtime span span.stonefont')[0].get_text().strip()
                m_total_time = dd.select('p.total-boxoffice span span.stonefont')[0].get_text().strip()
                borad_dic['real_time'] = m_real_time
                borad_dic['total_time'] = m_total_time
            elif self.end in [6]:
                m_mouth_wish = dd.select('p.month-wish span span.stonefont')[0].get_text().strip()
                m_total_wish = dd.select('p.total-wish span span.stonefont')[0].get_text().strip()
                borad_dic['mouth_wish'] = m_mouth_wish
                borad_dic['total_wish'] = m_total_wish
            movies.append(movie_info(**borad_dic))
        return movies


class WoffToOtf(object):
    """woff to otf convert"""
    @staticmethod
    def convert_streams(infile, outfile):
        WOFFHeader = {'signature': struct.unpack(">I", infile.read(4))[0],
                      'flavor': struct.unpack(">I", infile.read(4))[0],
                      'length': struct.unpack(">I", infile.read(4))[0],
                      'numTables': struct.unpack(">H", infile.read(2))[0],
                      'reserved': struct.unpack(">H", infile.read(2))[0],
                      'totalSfntSize': struct.unpack(">I", infile.read(4))[0],
                      'majorVersion': struct.unpack(">H", infile.read(2))[0],
                      'minorVersion': struct.unpack(">H", infile.read(2))[0],
                      'metaOffset': struct.unpack(">I", infile.read(4))[0],
                      'metaLength': struct.unpack(">I", infile.read(4))[0],
                      'metaOrigLength': struct.unpack(">I", infile.read(4))[0],
                      'privOffset': struct.unpack(">I", infile.read(4))[0],
                      'privLength': struct.unpack(">I", infile.read(4))[0]}

        outfile.write(struct.pack(">I", WOFFHeader['flavor']));
        outfile.write(struct.pack(">H", WOFFHeader['numTables']));
        maximum = list(filter(lambda x: x[1] <= WOFFHeader['numTables'], [(n, 2 ** n) for n in range(64)]))[-1];
        searchRange = maximum[1] * 16
        outfile.write(struct.pack(">H", searchRange));
        entrySelector = maximum[0]
        outfile.write(struct.pack(">H", entrySelector));
        rangeShift = WOFFHeader['numTables'] * 16 - searchRange;
        outfile.write(struct.pack(">H", rangeShift));

        offset = outfile.tell()

        TableDirectoryEntries = []
        for i in range(0, WOFFHeader['numTables']):
            TableDirectoryEntries.append({'tag': struct.unpack(">I", infile.read(4))[0],
                                          'offset': struct.unpack(">I", infile.read(4))[0],
                                          'compLength': struct.unpack(">I", infile.read(4))[0],
                                          'origLength': struct.unpack(">I", infile.read(4))[0],
                                          'origChecksum': struct.unpack(">I", infile.read(4))[0]})
            offset += 4 * 4

        for TableDirectoryEntry in TableDirectoryEntries:
            outfile.write(struct.pack(">I", TableDirectoryEntry['tag']))
            outfile.write(struct.pack(">I", TableDirectoryEntry['origChecksum']))
            outfile.write(struct.pack(">I", offset))
            outfile.write(struct.pack(">I", TableDirectoryEntry['origLength']))
            TableDirectoryEntry['outOffset'] = offset
            offset += TableDirectoryEntry['origLength']
            if (offset % 4) != 0:
                offset += 4 - (offset % 4)

        for TableDirectoryEntry in TableDirectoryEntries:
            infile.seek(TableDirectoryEntry['offset'])
            compressedData = infile.read(TableDirectoryEntry['compLength'])
            if TableDirectoryEntry['compLength'] != TableDirectoryEntry['origLength']:
                uncompressedData = zlib.decompress(compressedData)
            else:
                uncompressedData = compressedData
            outfile.seek(TableDirectoryEntry['outOffset'])
            outfile.write(uncompressedData)
            offset = TableDirectoryEntry['outOffset'] + TableDirectoryEntry['origLength'];
            padding = 0
            if (offset % 4) != 0:
                padding = 4 - (offset % 4)
            outfile.write(bytearray(padding));
    @staticmethod
    def convert(infilename, outfilename):
        with open(infilename, mode='rb') as infile:
            with open(outfilename, mode='wb') as outfile:
                WoffToOtf.convert_streams(infile, outfile)


if __name__ == '__main__':
    avg_list = sys.argv
    # avg_list += [6, '/Users/yw/Desktop/smoothpython/20180605/1.txt']
    borad = int(avg_list[1])
    if not borad:
        raise Exception('pls borad must be.option:7, 6, 1, 2, 4')
    path = avg_list[2]
    if not path:
        raise Exception('pls path must be have')
    sp = SpiderMo(borad)
    pages = range(1, 11)
    for index in pages:
        try:
            movies = sp.analysis_data(index)
            with open(path, 'a', encoding='utf-8') as f:
                if borad in [4, 7]:
                    print('进入47')
                    for item in movies:
                        content = '海报：{}，电影名：{}，主演：{}，上映时间：{}，排名：{}，得分：{}'.format(item[0],item[1],item[2],item[3],item[4],item[5])
                        f.write(content + '\n')
                elif borad in [1, 2]:
                    print('进入12')
                    for item in movies:
                        content = '海报：{}，电影名：{}，主演：{}，上映时间：{}，排名：{}，实时票房：{}，总票房：{}'.format(item[0], item[1], item[2], item[3],
                                                                                  item[4], item[5], item[6])
                        f.write(content + '\n')
                elif borad in [6]:
                    print('进入6')
                    for item in movies:
                        content = '海报：{}，电影名：{}，主演：{}，上映时间：{}，排名：{}，本月新增人数：{}，总想看人数：{}'.format(item[0], item[1], item[2], item[3],
                                                                                  item[4], item[5], item[6])
                        f.write(content + '\n')
        except Exception as e:
            raise Exception(e)
    print('OK')
