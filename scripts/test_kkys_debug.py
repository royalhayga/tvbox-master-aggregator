#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESS_DIR = os.path.join(WORK_DIR, "process")
os.makedirs(PROCESS_DIR, exist_ok=True)

sys.path.append(os.path.join(WORK_DIR, "scripts"))
from kkys_master import Spider

def debug_kkys():
    print("开始对可可影视 (kkys_master.py) 在 GitHub Actions 云端进行真实网页抓取与数据调试...", flush=True)
    spider = Spider()
    spider.init()

    # 1. 抓取首页真实数据
    home_data = spider.homeContent(True)

    # 2. 抓取分类筛选真实数据
    cate_data = spider.categoryContent("1", "1", True, {"type": "动作"})

    output = {
        "home_classes": home_data.get("class", []),
        "home_video_sample": (home_data.get("list", []) or [])[:10],
        "category_video_sample": (cate_data.get("list", []) or [])[:10]
    }

    out_path = os.path.join(PROCESS_DIR, "kkys_debug_output.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"云端调试抓取完成！真实产出数据已保存至: {out_path}", flush=True)

if __name__ == "__main__":
    debug_kkys()
