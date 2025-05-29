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