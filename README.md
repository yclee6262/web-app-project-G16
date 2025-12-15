# NTU Investment Platform

一個基於 Web 的全端投資組合管理系統。整合了即時資產追蹤、個人化關注清單，以及基於蒙地卡羅模擬的未來財富預測功能。

## 🚀 主要功能

* **使用者管理**: 支援註冊、登入。
* **投資組合管理**: 可建立、編輯、刪除多個投資組合，並追蹤持股損益。
* **關注清單**: 讓使用者追蹤感興趣的股票標的與漲跌幅。
* **資產分析**: 提供個股歷史股價走勢圖。
* **蒙地卡羅模擬**: 運用幾何布朗運動 (GBM) 預測投資組合未來 30 年的價值分佈 (含 10th-90th 百分位數)。
* **智慧投資建議**: 根據夏普比率 (Sharpe Ratio) 與波動率，提供個股買入、賣出或持有的具體建議。
* **API 文件**: 內建 Swagger UI，提供互動式 API 測試介面。

## 🛠 使用技術

* **Frontend**: React, Vite, Recharts
* **Backend**: Python Flask, NumPy, Pandas (Financial Analysis)
* **Database**: MySQL
* **Documentation**: Flasgger (Swagger UI)
* **DevOps**: Docker, Docker Compose

## 🏁 使用說明

本專案使用 Docker 容器化部署，請確保您的電腦已安裝 Docker Desktop。

### 1. 啟動服務
第一次執行或程式碼有修改時，請使用以下指令建置並啟動：

```bash
docker compose up --build
```

啟動後，您可以在瀏覽器訪問以下服務：

- Frontend (網頁介面): `http://localhost:5173`

- Backend API: `http://localhost:5001`

- API 文件 (Swagger): `http://localhost:5001/apidocs/`

### 2. 重建資料庫 (Rebuild Database)
如果修改了 init.sql 資料庫結構，或者想要清空所有資料並重新初始化 (包含 Seed data)，請執行：
```bash
# 1. 停止容器並刪除 Volume (資料庫資料)
docker compose down -v

# 2. 重新建置並啟動
docker compose up --build
```
