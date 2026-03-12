# Downloads 資料夾自動整理工具 (AutoFolderOrganization)

這是一個用於自動整理 Windows Downloads 資料夾的 Python 工具，具備檔案分類、重複偵測與大檔案標示功能。

## 🛠️ 功能特點

1.  **自動檔案分類**：
    *   `Images` (.jpg, .png, .gif...)
    *   `Documents` (.pdf, .docx, .xlsx, .ppt...)
    *   `Media` (.mp4, .mp3...)
    *   `Archives` (.zip, .rar, .7z...)
    *   `Others` (未分類檔案)
2.  **精準重複偵測**：透過比對檔案大小與 **MD5 Hash** 值，精確找出內容相同的重複檔案。
3.  **大檔案標示**：自動列出超過 **100MB** 的檔案，方便手動清理。
4.  **安全機制**：採兩階段操作，先掃描產出報告，經人工確認後才執行實際搬移。

## 🚀 使用說明

本工具分為兩個主要腳本：

### 第一階段：掃描與報告
執行 `scan_and_report.py`。
此腳本僅進行掃描，**不會搬移或刪除任何檔案**。執行後會產出：
*   `organization_report.txt`：文字版統計報告。
*   `organization_report.json`：供後續執行腳本讀取的數據檔案。

```bash
python scan_and_report.py
```

### 第二階段：執行整理
執行 `organize_execute.py`。
**注意：執行此腳本會實際搬移檔案並刪除重複項。**
*   依照報告內容建立子資料夾並搬移檔案。
*   自動刪除標記為重複的檔案，並保留最早的一份。
*   產出 `execution_log.txt` 紀錄執行結果。

```bash
python organize_execute.py
```

## 📂 專案結構
*   `scan_and_report.py`：掃描分析腳本。
*   `organize_execute.py`：執行整理腳本。
*   `ConversationRecord.txt`：開發過程的對話紀錄。
*   `REMINDER.txt`：操作提醒事項。

## 🔧 設定
請在腳本內修改 `TARGET_DIR` 變數來指定您的 Downloads 路徑。
目前預設為：`D:\Users\klinlin\Downloads`
