# 持股回落網

追蹤持股從期間高點回落多少的儀表板。股價每個交易日收盤後由 GitHub Actions 自動更新，網頁由 GitHub Pages 發布，電腦和手機都能看，不需要任何電腦開著。

## 檔案

| 檔案 | 用途 |
|---|---|
| `index.html` | 儀表板網頁 |
| `holdings.json` | 持股清單（代號、名稱），要增減持股就改這裡 |
| `fetch_prices.py` | 從 Yahoo Finance 下載還原除權息收盤價，寫成 `data/prices.json` |
| `.github/workflows/update-prices.yml` | 週一到週五 14:40（台北時間）自動執行下載並提交 |

## 第一次設定（約 5 分鐘）

1. 到 GitHub 建立一個新的 repository，例如 `holdings-drawdown`。
   - 免費帳號要選 **Public** 才能用 GitHub Pages。網頁上看得到持股代號，但沒有張數和金額。
2. 把這個資料夾的所有檔案上傳到 repository（包含 `.github` 資料夾）。
   - 用網頁上傳：在 repository 頁面按 **Add file → Upload files**，把整個資料夾內容拖進去，按 **Commit changes**。
   - 或用 git：
     ```bash
     git init -b main
     git add .
     git commit -m "持股回落網"
     git remote add origin https://github.com/<你的帳號>/holdings-drawdown.git
     git push -u origin main
     ```
3. 允許 Actions 寫入：**Settings → Actions → General → Workflow permissions**，選 **Read and write permissions**，按 Save。
4. 開啟網頁：**Settings → Pages**，Source 選 **Deploy from a branch**，Branch 選 `main`、資料夾 `/ (root)`，按 Save。
5. 先手動跑一次更新：**Actions → Update prices → Run workflow**。完成後 `data/prices.json` 會出現在 repository 裡。
6. 一兩分鐘後打開 `https://<你的帳號>.github.io/holdings-drawdown/`。把這個網址加到手機主畫面，就能像 App 一樣打開。

## 之後

- **增減持股**：在 GitHub 網頁上編輯 `holdings.json` 並提交，Actions 會自動重新下載。代號寫法：
  - 上市股票和 ETF 直接寫代號，例如 `"0050"`（程式會自動加上 `.TW`）。
  - 上櫃的要寫 `.TWO`，例如 `"00679B.TWO"`。
  - 美股寫原本的代號，例如 `"QQQ"`。
- **持股成本**：在網頁的「成本與回落」直接輸入，只存在該裝置的瀏覽器，不會上傳到 GitHub。換手機或電腦要各自輸入一次。
- **改更新時間**：改 `update-prices.yml` 裡的 `cron`，時間是 UTC（台北時間減 8 小時）。GitHub 的排程可能延遲幾分鐘到半小時。
- **更新失敗**：GitHub 會寄信通知。到 Actions 頁面看紀錄，常見原因是 Yahoo Finance 暫時擋住請求，下一次排程通常就恢復。
- **60 天沒動靜會暫停**：公開 repository 若 60 天沒有任何提交，GitHub 會停用排程。這裡每個交易日都會提交新股價，正常情況不會發生；萬一被停用，到 Actions 頁面按 Enable 即可。

## 在自己電腦預覽

```bash
python fetch_prices.py
python -m http.server 8000
```

然後打開 http://localhost:8000 。
