#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloads 資料夾掃描與整理報告產生器
====================================
第一階段：僅掃描、分析、產出報告，**不會搬移或刪除任何檔案**。

功能：
1. 依副檔名分類統計（Images / Documents / Media / Archives / Others）
2. 透過檔案大小 + MD5 找出重複檔案
3. 標示超過 100MB 的大檔案
"""

import os
import hashlib
import json
import configparser
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ============================================================
# 讀取設定 (config.ini)
# ============================================================
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"), encoding="utf-8")

TARGET_DIR = config.get("Settings", "TargetDir", fallback=r"D:\Users\klinlin\Downloads")
REPORT_DIR = config.get("Settings", "ReportDir", fallback=r"f:\Antigravity\AutoFolderOrganization")
REPORT_FILE = os.path.join(REPORT_DIR, "organization_report.txt")
REPORT_JSON = os.path.join(REPORT_DIR, "organization_report.json")

threshold_mb = config.getint("Settings", "LargeFileThresholdMB", fallback=100)
LARGE_FILE_THRESHOLD = threshold_mb * 1024 * 1024

# 分類規則自 config.ini 讀取
CATEGORY_MAP = {}
if "Categories" in config:
    for cat in config["Categories"]:
        exts = [e.strip().lower() for e in config["Categories"][cat].split(",")]
        CATEGORY_MAP[cat.capitalize()] = set(exts)
else:
    # Fallback 預設
    CATEGORY_MAP = {
        "Images": {".jpg", ".jpeg", ".png", ".gif"},
        "Documents": {".pdf", ".doc", ".docx", ".xls", ".xlsx"},
    }


def get_category(ext: str) -> str:
    """依副檔名判斷分類"""
    ext_lower = ext.lower()
    for cat, exts in CATEGORY_MAP.items():
        if ext_lower in exts:
            return cat
    return "Others"


def md5_hash(filepath: str, chunk_size: int = 8192) -> str:
    """分塊計算 MD5 hash"""
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
    except (PermissionError, OSError) as e:
        return f"ERROR:{e}"
    return h.hexdigest()


def format_size(size_bytes: int) -> str:
    """將 bytes 轉為人類可讀格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


def scan_files(target_dir: str):
    """掃描目標目錄下的所有檔案（僅第一層，不含子目錄內檔案）"""
    files = []
    skipped_dirs = []

    for entry in os.scandir(target_dir):
        if entry.is_dir(follow_symlinks=False):
            skipped_dirs.append(entry.name)
            continue
        if entry.is_file(follow_symlinks=False):
            try:
                stat = entry.stat()
                ext = Path(entry.name).suffix
                files.append({
                    "name": entry.name,
                    "path": entry.path,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "ext": ext,
                    "category": get_category(ext),
                })
            except (PermissionError, OSError):
                pass

    return files, skipped_dirs


def find_duplicates(files: list) -> list:
    """
    兩階段重複偵測：
    1. 依檔案大小分組
    2. 同大小檔案計算 MD5 比對
    回傳：[(hash, [file_info, ...]), ...]
    """
    # 第一階段：依大小分組
    size_groups = defaultdict(list)
    for f in files:
        size_groups[f["size"]].append(f)

    # 第二階段：對有重複大小的組計算 MD5
    print("  正在計算 MD5 hash（僅對同大小檔案）...")
    duplicate_groups = []
    candidates = {sz: group for sz, group in size_groups.items()
                  if len(group) >= 2 and sz > 0}

    total_candidates = sum(len(g) for g in candidates.values())
    processed = 0

    hash_groups = defaultdict(list)
    for sz, group in candidates.items():
        for f in group:
            processed += 1
            if processed % 20 == 0:
                print(f"    進度：{processed}/{total_candidates} 個檔案")
            h = md5_hash(f["path"])
            if not h.startswith("ERROR:"):
                hash_groups[(sz, h)].append(f)

    for (sz, h), group in hash_groups.items():
        if len(group) >= 2:
            # 按修改時間排序，最早的保留
            group.sort(key=lambda x: x["mtime"])
            duplicate_groups.append({
                "hash": h,
                "size": sz,
                "keep": group[0],
                "duplicates": group[1:],
            })

    return duplicate_groups


def find_large_files(files: list, threshold: int) -> list:
    """找出超過門檻值的大檔案"""
    large = [f for f in files if f["size"] >= threshold]
    large.sort(key=lambda x: x["size"], reverse=True)
    return large


def generate_report(files, skipped_dirs, duplicates, large_files):
    """產生完整報告"""
    sep = "=" * 80
    sep2 = "-" * 80
    lines = []

    lines.append(sep)
    lines.append(f"  Downloads 資料夾整理報告")
    lines.append(f"  掃描路徑：{TARGET_DIR}")
    lines.append(f"  產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(sep)

    # ---- 1. 分類統計 ----
    lines.append("")
    lines.append("📂 一、檔案分類統計")
    lines.append(sep2)

    cat_stats = defaultdict(lambda: {"count": 0, "size": 0, "files": []})
    for f in files:
        cat = f["category"]
        cat_stats[cat]["count"] += 1
        cat_stats[cat]["size"] += f["size"]
        cat_stats[cat]["files"].append(f["name"])

    total_count = len(files)
    total_size = sum(f["size"] for f in files)

    for cat in ["Images", "Documents", "Media", "Archives", "Others"]:
        s = cat_stats[cat]
        pct = (s["count"] / total_count * 100) if total_count > 0 else 0
        lines.append(f"  {cat:12s} : {s['count']:4d} 個檔案  "
                      f"({format_size(s['size']):>10s})  "
                      f"[{pct:5.1f}%]")

    lines.append(sep2)
    lines.append(f"  {'合計':12s} : {total_count:4d} 個檔案  "
                  f"({format_size(total_size):>10s})")

    if skipped_dirs:
        lines.append("")
        lines.append(f"  ⚠️  略過的子目錄（{len(skipped_dirs)} 個）：")
        for d in skipped_dirs:
            lines.append(f"    📁 {d}")

    # ---- 2. 重複檔案 ----
    lines.append("")
    lines.append("")
    lines.append("🔁 二、重複檔案清單")
    lines.append(sep2)

    if not duplicates:
        lines.append("  ✅ 未發現重複檔案")
    else:
        total_dup_count = sum(len(g["duplicates"]) for g in duplicates)
        total_dup_size = sum(
            g["size"] * len(g["duplicates"]) for g in duplicates
        )
        lines.append(f"  發現 {len(duplicates)} 組重複，"
                      f"共 {total_dup_count} 個可刪除的重複檔案，"
                      f"可釋放空間：{format_size(total_dup_size)}")
        lines.append("")

        for i, g in enumerate(duplicates, 1):
            lines.append(f"  ── 第 {i} 組 "
                          f"(MD5: {g['hash'][:12]}... | "
                          f"大小: {format_size(g['size'])}) ──")
            lines.append(f"    ✅ 保留：{g['keep']['name']}")
            for dup in g["duplicates"]:
                lines.append(f"    ❌ 重複：{dup['name']}")
            lines.append("")

    # ---- 3. 超大檔案 ----
    lines.append("")
    lines.append("📦 三、超大檔案清單 (>100MB)")
    lines.append(sep2)

    if not large_files:
        lines.append("  ✅ 無超過 100MB 的檔案")
    else:
        total_large_size = sum(f["size"] for f in large_files)
        lines.append(f"  共 {len(large_files)} 個大檔案，"
                      f"佔用空間：{format_size(total_large_size)}")
        lines.append("")
        for f in large_files:
            lines.append(f"  💾 {format_size(f['size']):>10s}  "
                          f"{f['name']}")

    # ---- 4. 搬移預覽摘要 ----
    lines.append("")
    lines.append("")
    lines.append("📋 四、搬移預覽摘要")
    lines.append(sep2)
    lines.append("  若確認執行，以下動作將被執行：")
    lines.append("")

    for cat in ["Images", "Documents", "Media", "Archives", "Others"]:
        s = cat_stats[cat]
        if s["count"] > 0:
            lines.append(f"    📁 {cat:12s} ← {s['count']:4d} 個檔案搬入")

    if duplicates:
        total_dup_count = sum(len(g["duplicates"]) for g in duplicates)
        lines.append(f"    🗑️  可刪除重複  ← {total_dup_count:4d} 個檔案")

    lines.append("")
    lines.append(sep)
    lines.append("  ⚠️  本次掃描未執行任何搬移或刪除動作")
    lines.append("  ⚠️  請審核上述報告，確認無誤後回覆「確認無誤，請執行」")
    lines.append(sep)

    return "\n".join(lines)


def save_json_report(files, duplicates, large_files):
    """儲存 JSON 格式報告供後續腳本使用"""
    data = {
        "scan_time": datetime.now().isoformat(),
        "target_dir": TARGET_DIR,
        "files": [{
            "name": f["name"],
            "path": f["path"],
            "size": f["size"],
            "category": f["category"],
            "ext": f["ext"],
        } for f in files],
        "duplicates": [{
            "hash": g["hash"],
            "size": g["size"],
            "keep": g["keep"]["name"],
            "delete": [d["name"] for d in g["duplicates"]],
        } for g in duplicates],
        "large_files": [{
            "name": f["name"],
            "size": f["size"],
        } for f in large_files],
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n📄 JSON 報告已儲存至：{REPORT_JSON}")


def main():
    print("🔍 開始掃描 Downloads 資料夾...")
    print(f"   路徑：{TARGET_DIR}")
    print()

    # 掃描
    files, skipped_dirs = scan_files(TARGET_DIR)
    print(f"  找到 {len(files)} 個檔案，{len(skipped_dirs)} 個子目錄（略過）")

    # 重複偵測
    print("\n🔁 偵測重複檔案...")
    duplicates = find_duplicates(files)

    # 大檔案
    print("\n📦 掃描超大檔案...")
    large_files = find_large_files(files, LARGE_FILE_THRESHOLD)

    # 產出報告
    print("\n📝 產生報告...")
    report = generate_report(files, skipped_dirs, duplicates, large_files)

    # 輸出到終端
    print()
    print(report)

    # 儲存到檔案
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📄 報告已儲存至：{REPORT_FILE}")

    # JSON 報告
    save_json_report(files, duplicates, large_files)

    print("\n✅ 掃描完成！請審核報告後決定是否執行整理。")


if __name__ == "__main__":
    main()
