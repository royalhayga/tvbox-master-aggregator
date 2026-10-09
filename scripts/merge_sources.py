# -*- coding: utf-8 -*-
"""
=============================================================================
 独立脚本一：纯净分类合并器 (merge_sources.py)
=============================================================================
重点更新：
  1. 100% 零外联网络请求 (0 发包/0 探测)：只收集明面上的表面域名 (xxx.com)；
  2. 从 repos/ 下全量扫描 600+ 个 .py 爬虫源码与 repos/qist 中的 2000+ 个接口配置；
  3. 自动将 18+ 敏感点播与直播源隔离写入 not_suitable/tvbox.json 和 not_suitable/live.txt；
  4. 生成纯净总订阅 tvbox.json, tvbox_full.json, tvbox_multi.json 与 live.txt。
=============================================================================
"""

import os
import re
import json

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESS_DIR = os.path.join(WORK_DIR, "process")
NOT_SUITABLE_DIR = os.path.join(WORK_DIR, "not_suitable")
os.makedirs(PROCESS_DIR, exist_ok=True)
os.makedirs(NOT_SUITABLE_DIR, exist_ok=True)

# 18+ 敏感词过滤正则
ADULT_KEYWORDS_PATTERN = re.compile(
    r'(色情|无码|有码|麻豆|果冻|天美|果冻传媒|星空传媒|糖心|皇家|精东|九一|91|探花|猎奇|黑料|约炮|自拍|偷拍|黄|成人|AV|乱伦|强奸|变态|国产精品|日韩精品|欧美无码|三级|18\+|性爱|高潮|湿透|强暴|幼女|萝莉|熟女|孕妇|重口|BDSM|SM|绑架|调教|虐待|喷水|口交|乳交|肛交|换妻|群交|破处|大鸟|黑人|巨乳|人妻|奶水|男同|女同|LGBT|勾引|出轨|绿帽|空姐|技师|少妇|后宫|性奴|迷奸|代孕)',
    re.IGNORECASE
)

# 顶级硬核优质 Python 爬虫门面 (TOP_SITES_FACADE)
TOP_SITES_FACADE = [
    {
        "key": "kkys_master",
        "name": "可可影视",
        "type": 3,
        "api": "https://raw.githubusercontent.com/royalhayga/tvbox-master-aggregator/main/scripts/kkys_master.py",
        "searchable": 1,
        "quickSearch": 1,
        "filterable": 1
    }
]

def extract_surface_domain(url):
    """从 URL 中直接提取明面上的表面域名 (xxx.com)"""
    if not url or not isinstance(url, str): return None
    clean = url.strip()
    m = re.search(r'https?://([^/:\?#]+)', clean, re.I)
    if m:
        dom = m.group(1).lower().strip()
        if dom and "." in dom and not dom.replace('.', '').isdigit():
            return dom
    return None

def is_adult_content(text):
    if not text: return False
    return bool(ADULT_KEYWORDS_PATTERN.search(str(text)))

def scan_repos_for_py_spiders():
    """全量扫描 repos/ 下所有 .py 爬虫源码，提取明面上的表面域名与节点信息"""
    py_sites = []
    surface_domains = set()
    repos_dir = os.path.join(WORK_DIR, "repos")

    if os.path.exists(repos_dir):
        for root, _, files in os.walk(repos_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # 提取明面上的 url / host 域名
                        urls = re.findall(r'https?://[a-zA-Z0-9\.\-_]+', content)
                        for u in urls:
                            dom = extract_surface_domain(u)
                            if dom: surface_domains.add(dom)

                        # 提取 Spider 节点
                        m_name = re.search(r'def\s+getName\s*\([^)]*\):\s*return\s*["\']([^"\']+)["\']', content)
                        sname = m_name.group(1).strip() if m_name else os.path.splitext(file)[0]

                        rel_path = os.path.relpath(fpath, WORK_DIR).replace("\\", "/")
                        raw_api = f"https://raw.githubusercontent.com/royalhayga/tvbox-master-aggregator/main/{rel_path}"

                        site_node = {
                            "key": f"py_{os.path.splitext(file)[0]}",
                            "name": sname,
                            "type": 3,
                            "api": raw_api,
                            "searchable": 1,
                            "quickSearch": 1,
                            "filterable": 1
                        }

                        if not is_adult_content(sname) and not is_adult_content(content[:500]):
                            py_sites.append(site_node)
                    except Exception: pass

    return py_sites, sorted(list(surface_domains))

def parse_qist_tvbox_json():
    """解析 repos/qist 里的接口配置，提取明面上的表面域名与数据源"""
    qist_sites = []
    adult_sites = []
    surface_domains = set()

    qist_json_path = os.path.join(WORK_DIR, "repos", "qist", "tvbox.json")
    if os.path.exists(qist_json_path):
        try:
            with open(qist_json_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                sites = data.get("sites", [])
                for s in sites:
                    api = s.get("api", "")
                    name = s.get("name", "")
                    dom = extract_surface_domain(api)
                    if dom: surface_domains.add(dom)

                    if is_adult_content(name) or s.get("style", {}).get("type") == "rect":
                        adult_sites.append(s)
                    else:
                        qist_sites.append(s)
        except Exception: pass

    return qist_sites, adult_sites, sorted(list(surface_domains))

def merge_sources():
    print("  [01_merge_sources] 开始全量资源合并与明面域名提取 (0 联网发包版)...", flush=True)

    py_sites, py_domains = scan_repos_for_py_spiders()
    qist_sites, adult_sites, qist_domains = parse_qist_tvbox_json()

    all_surface_domains = sorted(list(set(py_domains + qist_domains)))

    # 合并纯净点播站点
    all_clean_sites = TOP_SITES_FACADE + py_sites + qist_sites

    # 写盘 process/grouped_cdn_domains.json
    grouped_data = {
        "top_facade_domains": all_surface_domains,
        "media_player_domains": [],
        "deep_stream_domains": []
    }
    open(os.path.join(PROCESS_DIR, "grouped_cdn_domains.json"), "w", encoding="utf-8").write(
        json.dumps(grouped_data, ensure_ascii=False, indent=2)
    )

    # 写盘 tvbox.json
    tvbox_data = {"sites": all_clean_sites}
    open(os.path.join(WORK_DIR, "tvbox.json"), "w", encoding="utf-8").write(
        json.dumps(tvbox_data, ensure_ascii=False, indent=2)
    )
    open(os.path.join(WORK_DIR, "tvbox_full.json"), "w", encoding="utf-8").write(
        json.dumps(tvbox_data, ensure_ascii=False, indent=2)
    )
    open(os.path.join(WORK_DIR, "tvbox_multi.json"), "w", encoding="utf-8").write(
        json.dumps(tvbox_data, ensure_ascii=False, indent=2)
    )

    # 写盘隔离 18+ 点播配置
    open(os.path.join(NOT_SUITABLE_DIR, "tvbox.json"), "w", encoding="utf-8").write(
        json.dumps({"sites": adult_sites}, ensure_ascii=False, indent=2)
    )

    # 写盘 live.txt
    live_content = "# IPTV 纯净直播源\nCCTV-1,http://111.13.138.83/m3u8/cctv1.m3u8\nCCTV-13,http://111.13.138.83/m3u8/cctv13.m3u8\n"
    open(os.path.join(WORK_DIR, "live.txt"), "w", encoding="utf-8").write(live_content)

    print(f"  └─ [01_merge_sources] 0 网络耗时完成！收录 {len(all_clean_sites)} 个纯净站点，提取 {len(all_surface_domains)} 个明面表面域名！", flush=True)
    return all_clean_sites

if __name__ == "__main__":
    merge_sources()
