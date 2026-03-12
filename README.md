# Downloads 資料夾自動整理工具 (AutoFolderOrganization)

這是一個用於自動整理 Windows Downloads 資料夾的 Python 工具，具備檔案分類、重複偵測與大檔案標示功能。透過外部設定檔與兩階段執行邏輯，確保整理過程安全且易於管理。

## 🛠️ 功能特點

1.  **自動檔案分類**：依照預定義（或自訂）的副檔名將檔案移入子資料夾。
2.  **精準重複偵測**：透過比對檔案大小與 **MD5 Hash** 值，精確找出內容相同的重複項目。
3.  **大檔案標示**：自動列出超過指定門檻（預設 100MB）的檔案。
4.  **安全機制**：採兩階段操作，必須先產生報告經人工審核後，才執行執行搬移與刪除。
5.  **全配置化設計**：所有路徑與分類規則均由外部 `config.ini` 控制，程式碼內不含寫死路徑。

## 🚀 快速上手

### 1. 準備設定檔
將專案中的 `config.example.ini` 複製一份並命名為 `config.ini`，然後修改其中的路徑設定：
*   `TargetDir`：您想要整理的下載資料夾路徑。
*   `ReportDir`：存放報告與 log 的路徑。

> [!IMPORTANT]
> 程式碼會強制檢查 `config.ini`，若未設定路徑將無法執行。

### 2. 第一階段：掃描與檢視報告
執行後會產出 `organization_report.txt`，請開啟並確認預計執行的動作。
```bash
python scan_and_report.py
```

### 3. 第二階段：執行整理任務
確認報告無誤後，開發此腳本執行實際的搬移與重複檔案清理。
```bash
python organize_execute.py
```

## 📂 專案結構
*   `scan_and_report.py`：掃描分析與報告產生腳本。
*   `organize_execute.py`：根據報告執行實體整理的腳本。
*   `config.example.ini`：設定檔範本。
*   `.gitignore`：已設定排除私人的 `config.ini` 與產出的報告檔案。

## 🔧 自訂分類
您可以直接在 `config.ini` 的 `[Categories]` 區塊下新增或修改分類標籤與對應的副檔名。
