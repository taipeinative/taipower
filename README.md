# Taipower

使用標案與公開資料整理台電輸電線與變電所資訊。\
Taipower transmission lines and substations information from government tenders and public data.

* [高壓輸電線路](documents/transmission.md)
* [變電所（含大用戶變電所）](documents/substation.md)

## 指令行介面

### 政府電子採購網爬蟲

前往[政府電子採購網](https://web.pcc.gov.tw/pis/)收集標案資訊的自動化程式，發送請求的最小間距為 1.5 秒。\
Python 環境內需安裝：

* [Python](https://www.python.org/downloads/) - *3.11+*
* [Beautiful Soup](https://pypi.org/project/beautifulsoup4/)
* [Pandas](https://pypi.org/project/pandas/)
* [Requests](https://pypi.org/project/requests/)

```shell
# 基本語法
python script/crawler.py "搜尋關鍵字"

# 更改輸出位置（預設在 data 資料夾）
python script/crawler.py "搜尋關鍵字" -o ./results

# 篩選時間範圍（例：民國 99 年至 109 年）
python script/crawler.py "搜尋關鍵字" -t 99 109

# 輸出冗餘日誌
python script/crawler.py "搜尋關鍵字" -v
```

輸出的 CSV 檔案名格式為 `搜尋關鍵字_xxx.csv`，其中 `xxx` 為民國紀年。檔案內包含四個欄位：

* `title`—標案名稱
* `authority`—機關名稱
* `date`—招標／決標／無法決標日期
* `url`—標案連結

## 授權

MIT 授權條款，相關權利與義務詳見 [LICENSE.txt](LICENSE.txt)。
