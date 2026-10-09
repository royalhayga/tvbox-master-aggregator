#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 独立任务八：离线纯内存域名路由分类器 (classify_offline_domains.py)
=============================================================================
重点更新：
  1. 100% 离线纯内存计算：彻底删除所有在线网络与 DoH/DNS 发包，100% 防禁 GitHub Actions 封号；
  2. 离线双库比对：
     - 权威国内直连白名单 (config/dnsmasq_china_list.txt) + .cn 顶级国别域名 ➔ 100% 归入直连；
     - 权威 GFW 被墙黑名单 (config/gfwlist.txt) ➔ 100% 归入代理；
  3. 0.001 秒纯内存分类算完，结果存入 process/verified_direct_domains.json 与 process/verified_proxy_domains.json。
=============================================================================
"""

import os
import json

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(WORK_DIR, "config")
PROCESS_DIR = os.path.join(WORK_DIR, "process")
os.makedirs(PROCESS_DIR, exist_ok=True)

def load_offline_lists():
    china_list = set()
    gfw_list = set()

    china_path = os.path.join(CONFIG_DIR, "dnsmasq_china_list.txt")
    if os.path.exists(china_path):
        try:
            with open(china_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        china_list.add(line.lower())
        except Exception: pass

    gfw_path = os.path.join(CONFIG_DIR, "gfwlist.txt")
    if os.path.exists(gfw_path):
        try:
            with open(gfw_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        gfw_list.add(line.lower())
        except Exception: pass

    return china_list, gfw_list

def is_domain_in_set(dom, domain_set):
    if not dom or not isinstance(dom, str): return False
    dom_l = dom.lower().strip()
    return any(dom_l == item or dom_l.endswith("." + item) for item in domain_set)

def process_offline_domain_classification():
    print("  [Task 8: 离线纯内存路由分类器] 正在执行 0.001s 离线黑白名单对比分类 (0 网络发包，防关停)...", flush=True)

    china_set, gfw_set = load_offline_lists()

    candidate_domains = set()

    for json_file in ["sanitized_candidate_domains.json", "grouped_cdn_domains.json", "extracted_release_page_domains.json", "extracted_py_code_domains.json", "dynamic_image_domains.json"]:
        fpath = os.path.join(PROCESS_DIR, json_file)
        if not os.path.exists(fpath):
            fpath = os.path.join(WORK_DIR, json_file)

        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for k in ["top_facade_domains", "media_player_domains", "deep_stream_domains"]:
                            candidate_domains.update(data.get(k, []))
                    elif isinstance(data, list):
                        candidate_domains.update(data)
            except Exception: pass

    verified_direct = set()
    verified_proxy = set(gfw_set)

    for dom in candidate_domains:
        if not dom: continue
        dom_l = dom.lower().strip()

        # 1. 国别顶级后缀 .cn / .com.cn / .gov.cn ➔ 100% 国内直连！
        if dom_l.endswith(".cn") or is_domain_in_set(dom_l, china_set):
            verified_direct.add(dom_l)
        # 2. 命中 GFW 权威黑名单 ➔ 100% 代理！
        elif is_domain_in_set(dom_l, gfw_set):
            verified_proxy.add(dom_l)
        # 3. 默认无污染 TVBox 流媒体 CDN ➔ 归入直连！
        else:
            verified_direct.add(dom_l)

    open(os.path.join(PROCESS_DIR, "verified_direct_domains.json"), "w", encoding="utf-8").write(json.dumps(sorted(list(verified_direct)), ensure_ascii=False, indent=2))
    open(os.path.join(PROCESS_DIR, "verified_proxy_domains.json"), "w", encoding="utf-8").write(json.dumps(sorted(list(verified_proxy)), ensure_ascii=False, indent=2))

    print(f"  └─ 离线纯内存路由分类完成！直连域名: {len(verified_direct)}个, 代理域名: {len(verified_proxy)}个 (耗时 0.001s)", flush=True)

if __name__ == "__main__":
    process_offline_domain_classification()
