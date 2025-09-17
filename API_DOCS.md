# Shin-Her API 文檔

## 概述

此 API 提供學生資訊系統的各種功能，包括登入、獎懲記錄、課表、出勤記錄、成績查詢等。

## 認證

API 使用兩層認證機制：
1. **API Key**: 在 `Authorization` header 中提供
2. **Token**: 在 `token` header 中提供（登入後獲得）

## 基礎 URL

```
/api
```

## 端點列表

### 1. 用戶登入

**POST** `/api/login`

用戶登入並獲取 token。

#### 請求標頭
```
Authorization: {api_key}
Content-Type: application/json
```

#### 請求體
```json
{
    "account": "123456",
    "password": "1234567890"
}
```

#### 請求參數
- `account` (string, required): 6位數帳號
- `password` (string, required): 10位數密碼

#### 成功回應 (200)
```json
{
    "account": "123456",
    "message": "登入成功",
    "status": "success",
    "token": "token_here"
}
```

#### 錯誤回應
- **401 Unauthorized**: API Key 無效
- **400 Bad Request**: 帳號或密碼格式錯誤

### 2. 獎懲記錄

**GET** `/api/rap`

取得學生的功過記錄資料。

#### 請求標頭
```
Authorization: {api_key}
token: {user_token}
```

#### 成功回應 (200)
```json
{
    "status": "success",
    "data": [
        [
            {
                "action": "小功乙次",
                "date_approved": "2025/05/27",
                "date_occurred": "2025/05/27",
                "date_revoked": null,
                "reason": "擔任班長認真負責",
                "year": "1132"
            },
            {
                "action": "嘉獎乙次",
                "date_approved": "2025/06/17",
                "date_occurred": "2025/06/17",
                "date_revoked": null,
                "reason": "週記於抽查當日完成繳交,符合規定繳交篇數,並經導師批閱",
                "year": "1132"
            }
        ],
        [
            {
                "action": "警告貳次",
                "date_approved": "2023/10/16",
                "date_occurred": "2023/09/25",
                "date_revoked": null,
                "reason": "1120919違反行動載具管理規則屢勸不聽",
                "year": "1121"
            },
            {
                "action": "警告貳次",
                "date_approved": "2024/03/11",
                "date_occurred": "2024/03/04",
                "date_revoked": null,
                "reason": "違反行動載具管理規則屢勸不聽(02/27)",
                "year": "1122"
            }
        ]
    ]
}
```

#### 錯誤回應
- **401 Unauthorized**: 未授權或登入已過期
- **500 Internal Server Error**: 無法取得資料

### 3. 課表查詢

**GET** `/api/curriculum`

取得學生的每週課程表資料。

#### 請求標頭
```
Authorization: {api_key}
token: {user_token}
```

#### 成功回應 (200)
```json
{
    "data": {
        "介面電路控制實習": {
            "count": 3,
            "schedule": [
                {
                    "period": "二",
                    "weekday": "五"
                },
                {
                    "period": "三",
                    "weekday": "五"
                },
                {
                    "period": "四",
                    "weekday": "五"
                }
            ]
        },
        "體育": {
            "count": 2,
            "schedule": [
                {
                    "period": "一",
                    "weekday": "四"
                },
                {
                    "period": "三",
                    "weekday": "一"
                }
            ]
        }
    },
    "status": "success"
}
```

### 4. 出勤記錄

**GET** `/api/attendance`

取得學生的出勤狀況記錄。

#### 請求標頭
```
Authorization: {api_key}
token: {user_token}
```

#### 成功回應 (200)
```json
{
    "data": [
        {
            "學年": "上",
            "日期": "2025/9/12",
            "星期": "五",
            "狀態": "公",
            "節次": "3"
        },
        {
            "學年": "上",
            "日期": "2025/9/15",
            "星期": "一",
            "狀態": "遲",
            "節次": "1"
        }
    ],
    "status": "success"
}
```

### 6. 出勤統計

**GET** `/api/attendance-statistics`

取得整體出勤狀況的統計資料。

#### 請求標頭
```
Authorization: {api_key}
token: {user_token}
```

#### 成功回應 (200)
```json
{
    "data": {
        "上學期合計": {
            "事假": "0",
            "事假1": "0",
            "公假": "4",
            "升降午缺": "0",
            "升降午遲": "0",
            "喪假": "0",
            "娩假": "0",
            "早缺": "0",
            "早遲": "0",
            "曠課": "0",
            "流產": "0",
            "生理": "0",
            "產前": "0",
            "病假": "0",
            "病假1": "0",
            "病假2": "0",
            "育嬰": "0",
            "身心": "0",
            "遲到": "2"
        },
        "下學期合計": {
            "事假": "0",
            "事假1": "0",
            "公假": "0",
            "升降午缺": "0",
            "升降午遲": "0",
            "喪假": "0",
            "娩假": "0",
            "早缺": "0",
            "早遲": "0",
            "曠課": "0",
            "流產": "0",
            "生理": "0",
            "產前": "0",
            "病假": "0",
            "病假1": "0",
            "病假2": "0",
            "育嬰": "0",
            "身心": "0",
            "遲到": "0"
        },
        "全部合計": {
            "事假": 0,
            "公假": 4,
            "曠課": 0,
            "病假": 0
        }
    },
    "status": "success"
}
```

### 7. 學年成績

**GET** `/api/score`

根據指定學年返回學生的成績資料。

#### 請求標頭
```
Authorization: {api_key}
token: {user_token}
```

#### 查詢參數
- `year` (string, optional): 年級 (1-4)，預設為 "1"

#### 範例請求
```
GET /api/score?year=2
```

#### 成功回應 (200)
```json
{
    "data": {
        "學生資訊": "XXX│二年級歷年成績總表",
        "日常表現": {
            "上學期": {
                "其他": "",
                "具體建議及評語": "做事很專注，不容易分心，有始有終，又很能掌握情境做適度的表現",
                "日常生活表現": {
                    "描述": "熱誠和藹，開朗合群",
                    "評量": "<td class=\"top\" style=\"width: 144px;\">待人誠信：表現優異<br/>整潔習慣：表現優異<br/>禮  節：表現優異<br/>班級服務：表現優異<br/>社團活動：表現良好<br/>"
                },
                "服務學習": "熱心公務，服務負責完善",
                "校內外特殊表現": "擔任學藝股長認真負責，協助各項活動,認真負責，拾物不昧"
            },
            "下學期": {
                "其他": "",
                "具體建議及評語": "反應敏捷，舉一能反三，能很快的進入各種學習情境，唯求學未盡全力，否則應有更好表現",
                "日常生活表現": {
                    "描述": "心思細膩，技藝優良，熱心盡職",
                    "評量": "<td class=\"top\" style=\"width: 144px;\">待人誠信：表現優異<br/>整潔習慣：表現優異<br/>禮  節：表現優異<br/>班級服務：表現優異<br/>社團活動：表現優異<br/>"
                },
                "服務學習": "擔任校外志工服務態度認真",
                "校內外特殊表現": "擔任班長認真負責，擔任實習工廠管理人，認真負責"
            }
        },
        "科目成績": [
            {
                "上學期": {
                    "學分": "1",
                    "屬性": "選修",
                    "成績": "32"
                },
                "下學期": {
                    "學分": "1",
                    "屬性": "選修",
                    "成績": "0"
                },
                "學年成績": "16",
                "科目": "英文閱讀指導"
            },
            {
                "上學期": {
                    "學分": "2",
                    "屬性": "選修",
                    "成績": "100"
                },
                "下學期": {
                    "學分": "2",
                    "屬性": "選修",
                    "成績": "100"
                },
                "學年成績": "100",
                "科目": "開放源碼網頁設計"
            }
        ],
        "總成績": {
            "學期名次": {
                "上學期": "23",
                "下學期": "22",
                "學年": ""
            },
            "學科平均": {
                "上學期": "57.6",
                "下學期": "54.8",
                "學年": "56.2"
            },
            "實得學分": {
                "上學期": "21",
                "下學期": "25",
                "學年": ""
            },
            "實得累計": {
                "上學期": "65",
                "下學期": "90",
                "學年": ""
            },
            "實習成績": {
                "上學期": "84.6",
                "下學期": "86.5",
                "學年": "85.6"
            },
            "智育成績": {
                "上學期": "47.7",
                "下學期": "43.3",
                "學年": "45.5"
            },
            "補前平均": {
                "上學期": "57.6",
                "下學期": "56.1",
                "學年": "56.9"
            },
            "軍訓成績": {
                "上學期": "",
                "下學期": "",
                "學年": ""
            },
            "體育成績": {
                "上學期": "",
                "下學期": "",
                "學年": ""
            }
        }
    },
    "status": "success"
}
```

#### 錯誤回應
- **400 Bad Request**: 年級參數錯誤

### 8. 考試成績

**GET** `/api/all_score`

返回考試選單與指定考試的詳細成績資料。

#### 請求標頭
```
Authorization: {api_key}
token: {user_token}
```

#### 查詢參數
- `name` (string, optional): 考試名稱

#### 範例請求
```
GET /api/all_score?name=[113上] 113上學期第期末考
```

#### 成功回應 (200)
```json
{
    "data": {
        "menu": [
            {
                "full_url": "https://eschool.ykvs.ntpc.edu.tw/Online/selection_student/student_subjects_number.asp?action=%A6U%A6%A1%A6%A8%C1Z&thisyear=113&thisterm=1&number=1312&exam%5Fname=113%A4W%BE%C7%B4%C1%B2%C4%A4G%A6%B8%ACq%A6%D2",
                "name": "[113上] 113上學期第二次段考",
                "number": "1312",
                "thisterm": "1",
                "thisyear": "113",
                "url": "student_subjects_number.asp?action=%A6U%A6%A1%A6%A8%C1Z&thisyear=113&thisterm=1&number=1312&exam%5Fname=113%A4W%BE%C7%B4%C1%B2%C4%A4G%A6%B8%ACq%A6%D2"
            },
            {
                "full_url": "https://eschool.ykvs.ntpc.edu.tw/Online/selection_student/student_subjects_number.asp?action=%A6U%A6%A1%A6%A8%C1Z&thisyear=113&thisterm=1&number=1313&exam%5Fname=113%A4W%BE%C7%B4%C1%B2%C4%B4%C1%A5%BD%A6%D2",
                "name": "[113上] 113上學期第期末考",
                "number": "1313",
                "thisterm": "1",
                "thisyear": "113",
                "url": "student_subjects_number.asp?action=%A6U%A6%A1%A6%A8%C1Z&thisyear=113&thisterm=1&number=1313&exam%5Fname=113%A4W%BE%C7%B4%C1%B2%C4%B4%C1%A5%BD%A6%D2"
            }
        ],
        "scores": {
            "exam_info": "【訊二孝】[113上] 113上學期第期末考成績",
            "student_info": {
                "class": "訊二孝",
                "name": "洪碩亨班級：訊二孝",
                "student_id": "215215"
            },
            "subjects": [
                {
                    "class_average": "63.61",
                    "personal_score": "61",
                    "subject": "公民與社會"
                },
                {
                    "class_average": "49.79",
                    "personal_score": "42",
                    "subject": "數位邏輯設計"
                }
            ],
            "summary": {
                "average_score": "31.05",
                "class_rank": "25",
                "department_rank": "87",
                "total_score": "621"
            }
        }
    },
    "status": "success"
}
```

## 錯誤碼說明

| 狀態碼 | 說明 |
|--------|------|
| 200 | 成功 |
| 400 | 請求參數錯誤 |
| 401 | 未授權或登入已過期 |
| 500 | 伺服器內部錯誤 |

## 使用範例

### Python 範例

```python
import requests

# 設定 API Key
api_key = "your_api_key_here"
headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}

# 登入
login_data = {
    "account": "123456",
    "password": "1234567890"
}
response = requests.post("http://localhost:5000/api/login", 
                        json=login_data, headers=headers)
token = response.json()["token"]

# 使用 token 查詢資料
headers["token"] = token
response = requests.get("http://localhost:5000/api/", headers=headers)
print(response.json())
```

### JavaScript 範例

```javascript
const apiKey = "your_api_key_here";
const baseUrl = "http://localhost:5000/api";

// 登入
const loginResponse = await fetch(`${baseUrl}/login`, {
    method: "POST",
    headers: {
        "Authorization": apiKey,
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        "account": "123456",
        "password": "1234567890"
    })
});
const loginData = await loginResponse.json();
const token = loginData.token;

// 查詢獎懲記錄
const meritResponse = await fetch(`${baseUrl}/`, {
    headers: {
        "Authorization": apiKey,
        "token": token
    }
});
const meritData = await meritResponse.json();
console.log(meritData);
```

## 注意事項

1. 所有需要認證的端點都必須提供有效的 API Key 和 Token
2. 帳號格式必須為 6 位數，密碼必須為 10 位數
3. Token 在登入成功後取得，用於後續 API 呼叫
4. 如果登入過期，需要重新登入取得新的 Token