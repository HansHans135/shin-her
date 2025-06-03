# 更好的欣河系統
透過爬蟲改善原始系統難用到靠北的問題
- demo(僅限鶯歌工商學生使用)
> https://ykvs.hans0805.me/

# 截圖與對比
https://www.threads.com/@08.hans_/post/DKJvkKZJshr

# 技術架構
> 後端
- Python
- Flask + jinja2
- BeautifulSoup

> 前端
- HTML
- Tailwind CSS
- JavaScript

# 安裝與配置

下載或 Git 此倉庫
```
git clone https://github.com/HansHans135/shin-her.git
cd shin-her
```

複製 `config.example.json` 並重新命名為 `config.json`

|名|值|
|---|---|
|capmonster_key|電腦驗證 API Key|
|capmonster_url|電腦驗證 API 網址|
|base_url|欣河登入首頁網址|
|weeks_per_semester|每學期周數，用於計算缺曠|
|secret_key|隨機亂碼|
|port|運行端口|

安裝依賴套件
```
pip install -r requirements.txt
```

運行軟體
```
python app.py
```

# 特別感謝
[@ivan17lai](https://github.com/ivan17lai) 協助[登入功能](https://github.com/ivan17lai/shinherpro/blob/main/shinherpro1.1%2Fmain.py)
