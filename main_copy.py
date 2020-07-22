
import discord  #discord.pyのライブラリ
import os   #環境変数に配置したTOKENを読み込む為の標準ライブラリ
from discord.ext import tasks   #discord.pyでコマンドが利用できるようにするライブラリ
from datetime import datetime   #午後8時に今日の感染者数を見る為に入れた標準ライブラリ
import requests #httpリクエストを送るための標準ライブラリ
from bs4 import BeautifulSoup   #requestsの内容をスクレイピングする為のライブラリ

#オブジェくトの生成
client = discord.Client()

#getでURLに接続しデータを取得(都内感染者数)
res= requests.get("https://stopcovid19.metro.tokyo.lg.jp/cards/number-of-confirmed-cases/")

#先のサイトをlxmlというパーサで解析
soup = BeautifulSoup(res.text,"lxml")

#今日の感染者数はspanタグで囲まれてクラス名は以下の様になっているそれをget_text()でさらに成形
today = soup.find("span",class_="DataView-DataInfo-summary").get_text(strip=True)
#今日の感染者数はsmallタグで囲まれてクラス名は以下の様になっているそれをget_text()でさらに成形
compared_to = soup.find("small",class_="DataView-DataInfo-date").get_text(strip=True)

#getでURLに接続しデータを取得(ヤフーニュース)
res2= requests.get("https://news.yahoo.co.jp/")

#先のサイトをlxmlというパーサで解析
yahoo = BeautifulSoup(res2.text,"lxml")
#class名topicsをtopicsindexに格納
topicsindex = yahoo.find(class_="topics")

#ここから先はdiscord.pyの処理
#60秒に一回のループ
@tasks.loop(seconds=60)
async def loop():   #ループ関数
    # 現在の時刻
    now = datetime.now().strftime('%H:%M')
    #現在時刻が8時3分であれば
    if now == '20:03':
        #discord.pyの準備ができるまで待機
        await client.wait_until_ready()
        #感染者数をメッセージ送信
        await message.channel.send('本日のコロナウィルス感染者は' + today + 'でした')
        #前日比をメッセージ送信
        await message.channel.send(compared_to)

#何らかのアクションを起こした時に処理する
@client.event
#discordサーバに参加者が参加した際にbotもログインする
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

#先と同じ
@client.event
#あるメッセージが送られた時
async def on_message(message):
    #bot自身のメッセージに反応しないように
    if message.author == client.user:
        return
    #感染者数教えてと送られた際に埋め込みメッセージを返す
    if message.content.startswith('感染者数教えて'):
        embed = discord.Embed(title="都内感染者数:",description=today)
        await message.channel.send(embed=embed)
   #ニュースを教えてと送られた際に埋め込みメッセージを返す
    if message.content.startswith('ニュース教えて'):
        #ヤフーのトップニュースが7つあるので7つのニュースについてスクレイピングを行う
        for i in range(1,8):
            #カスタム属性data-ylkのニュースタイトルをget_text()さらに成形
            news_title = topicsindex.find(attrs={"data-ylk":"rsec:tpc_maj;slk:title;pos:" + str(i) + ';'}).get_text(strip=True)
            #カスタム属性data-ylkの中にあるURLのhrefをとってくる
            news_url = topicsindex.find('a',attrs={"data-ylk":"rsec:tpc_maj;slk:title;pos:" + str(i) + ';'}).get("href")

            #先のnews_urlに対してサイトの情報をリクエスト
            res3 = requests.get(news_url)
            #res3をlxmlというパーサで解析
            yahoo_detail = BeautifulSoup(res3.text,"lxml")
            #ニュースの画像URLが欲しいのだが動画の可能性があるのでtry-except文でエラー回避
            try:
                #divタグのclass~を探す
                div = yahoo_detail.find("div",class_="pickupMain_image pickupMain_image-picture")
                #divの内imgタグを探しその中のsrcを取ってくる
                news_img = div.find("img").get("src")
                #ニュースタイトルにURLを入れた埋め込みメッセージ
                embed = discord.Embed(title=news_title,description= "最新ニュース" + str(i),url=news_url,color=discord.Colour.blue())
                #ニュースのサムネイル画像をemdedに追加
                embed.set_image(url=news_img)
                #埋め込みメッセージの送信
                await message.channel.send(embed=embed)
            except AttributeError:  #画像URL又は記述そのものがない場合
                #ニュースタイトルにURLを入れた埋め込みメッセージ
                embed = discord.Embed(title=news_title,description= "最新ニュース" + str(i) + "\nサムネは動画なので無し",url=news_url,color=discord.Colour.blue())
                #埋め込みメッセージの送信
                await message.channel.send(embed=embed)
#ループの開始
loop.start()

#TOKENは平文で書くべきでない為,ラズパイの.bash_profileに環境変数として記述した
client.run(os.environ.get("DISCORD_TOKEN"))
