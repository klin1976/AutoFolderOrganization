#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloads 資料夾整理執行器
=========================
第二階段：根據掃描報告，實際執行檔案搬移與重複檔案處理。
"""

import os
import json
import shutil
import configparser
from datetime import datetime

# ============================================================
# 讀取設定 (config.ini)
# ============================================================
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"), encoding="utf-8")

if "Settings" not in config:
    raise ValueError("❌ 找不到 [Settings] 區塊，請檢查 config.ini")

TARGET_DIR = config.get("Settings", "TargetDir")
REPORT_DIR = config.get("Settings", "ReportDir")

if not TARGET_DIR or not REPORT_DIR:
    raise ValueError("❌ config.ini 中的 TargetDir 或 ReportDir 未設定！")

# 從 ini 讀取檔名，並結合目錄
json_filename = config.get("Settings", "ReportJson", fallback="organization_report.json")
log_filename = config.get("Settings", "BackupLog", fallback="execution_log.txt")

REPORT_JSON = os.path.join(REPORT_DIR, json_filename)
BACKUP_LOG = os.path.join(REPORT_DIR, log_filename)

def log(msg, file=None):
    print(msg)
    if file:
        file.write(msg + "\n")

def main():
    if not os.path.exists(REPORT_JSON):
        print(f"❌ 找不到掃描報告：{REPORT_JSON}\n請先執行 scan_and_report.py")
        return

    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(f"🚀 開始執行整理任務...")
    print(f"📂 目標：{TARGET_DIR}")
    
    with open(BACKUP_LOG, "w", encoding="utf-8") as log_file:
        log(f"=== 執行紀錄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===", log_file)
        
        # 1. 建立分類資料夾
        categories = set(f["category"] for f in report["files"])
        for cat in categories:
            cat_path = os.path.join(TARGET_DIR, cat)
            if not os.path.exists(cat_path):
                os.makedirs(cat_path)
                log(f"📁 建立資料夾：{cat}", log_file)

        # 2. 處理重複檔案 (刪除重複的，保留 keep 的)
        deleted_count = 0
        deleted_size = 0
        for group in report["duplicates"]:
            for dup_name in group["delete"]:
                dup_path = os.path.join(TARGET_DIR, dup_name)
                if os.path.exists(dup_path):
                    try:
                        sz = os.path.getsize(dup_path)
                        os.remove(dup_path)
                        deleted_count += 1
                        deleted_size += sz
                        log(f"🗑️  刪除重複：{dup_name}", log_file)
                    except Exception as e:
                        log(f"⚠️  刪除失敗 {dup_name}: {e}", log_file)

        # 3. 搬移檔案
        moved_count = 0
        # 重新整理檔案清單，排除已被刪除的
        for f_info in report["files"]:
            src_path = os.path.join(TARGET_DIR, f_info["name"])
            
            # 如果檔案已不在 (可能是剛刪除的重複檔)
            if not os.path.exists(src_path):
                continue
                
            dest_dir = os.path.join(TARGET_DIR, f_info["category"])
            dest_path = os.path.join(dest_dir, f_info["name"])
            
            # 處理檔名衝突 (雖是搬入子目錄，但預防萬一)
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(f_info["name"])
                counter = 1
                while os.path.exists(os.path.join(dest_dir, f"{base}_{counter}{ext}")):
                    counter += 1
                dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")

            try:
                shutil.move(src_path, dest_path)
                moved_count += 1
                # log(f"📦 搬移：{f_info['name']} -> \{f_info['category']}", log_file)
            except Exception as e:
                log(f"⚠️  搬移失敗 {f_info['name']}: {e}", log_file)

        log(f"\n✨ 任務完成！", log_file)
        log(f"✅ 成功搬移：{moved_count} 個檔案", log_file)
        log(f"🗑️  刪除重複：{deleted_count} 個檔案 (釋放 {deleted_size/1024/1024:.2f} MB)", log_file)
        log(f"📄 詳細紀錄：{BACKUP_LOG}", log_file)

if __name__ == "__main__":
    main()
