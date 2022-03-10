import datetime

import feedparser
from bs4 import BeautifulSoup
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

RSS_FEED = {"科技爱好者": 'http://www.ruanyifeng.com/blog/atom.xml',
            "独立开发者社区": 'https://www.bilibili.com/video/BV1ra411b79i?share_source=copy_web',
            "站长之家": 'http://app.chinaz.com/?app=rss',
            "猎云网": 'http://www.lieyunwang.com/feed',
            "极客公园": 'http://www.geekpark.net/rss'
            }

DEFAULTS = {
    'city': '金华',
    'publication': '科技爱好者'
}

import requests
def get_source(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    return response.text

def get_value_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULTS[key]

def get_weather():
    url = "http://www.weather.com.cn/textFC/hd.shtml"
    source = get_source(url)
    # 解决网页乱码，添加'html5lib'，而不是lxml
    soup = BeautifulSoup(source, 'html5lib')  # pip install html5lib
    # 1.进入整体表格
    conMidtab = soup.find('div', class_='conMidtab')
    # 2.进入子表格
    tables = conMidtab.find_all('table')
    # 3.进入每个子表格收集天气信息
    # print(tables)
    info = []
    for table in tables:
        # (1)过滤前两个（城市和时间）
        trs = table.find_all('tr')[2:]  # tr存储了每个城市的天气信息
        # enumerate 返回2个值第一个是下标 第二个下标所对应的元素
        # (2)进入每个城市（每一行），判断是否是省会
        for index, tr in enumerate(trs):
            tds = tr.find_all('td')  # td存储每个城市天气信息的每个具体项目
            # 城市名字判断：因为对于每个省份的第一行的第一列为省名，对应不了省会。爬取会出错，因而要判断修改
            city_td = tds[0]  # 城市
            if index == 0:  # index==0，代表的是第一个tr，第一个城市
                city_td = tds[1]  # 省会
            # (3)获取每个城市的具体天气项目
            city = list(city_td.stripped_strings)[0]  # 城市名字
            # 该城市最高气温
            temp_high_td = tds[-5]
            temp_high = list(temp_high_td.stripped_strings)[0]
            # 该城市最低气温
            temp_low_td = tds[-2]
            temp_low = list(temp_low_td.stripped_strings)[0]
            # print('城市:', city, '最高气温:', temp_high,'最低气温:',temp_low)
            item = city, temp_high, temp_low
            info.append(item)
    return info  # 存储在info内部

def get_news(publication):
    if publication in RSS_FEED:
        feed = feedparser.parse(RSS_FEED[publication])
    else:
        return None
    return feed['entries']

@app.route('/')
def home():
    publication = get_value_fallback('publication')

    weathers = get_weather()
    weather = None
    city = get_value_fallback('city')
    for c in weathers:
        if c[0] == city:
             weather=c

    if get_news(publication) == None:
        news = [{'title': 'B站', 'title_detail': {'type': 'text/plain', 'language': None },  'summary': '没有订阅源，请先订阅源','link': 'https://www.bilibili.com'}]
    else:
        news = get_news(publication)
    response = make_response(render_template('home.html',articles=news,weather=weather))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie('publication',  publication, expires=expires)
    response.set_cookie('city',  city, expires=expires)
    return response

if __name__ == '__main__':
    print(app.url_map)
    app.run(host='0.0.0.0',port=5000)
