import streamlit as st
import pandas as pd
import json
import hashlib
import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

# ── 1. 頁面配置 ─────────────────────────────────────
st.set_page_config(page_title="SOLIDWIZARD | 技術資源庫", layout="wide")

# ── 2. 核心 CSS 樣式 ──────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0f172a; }
    [data-testid="stSidebar"] * { color: #94a3b8 !important; }
    .doc-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin-bottom: 15px; }
    .doc-title { font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 10px; }
    .tag { font-size: 10px; font-weight: 700; padding: 4px 12px; border-radius: 5px; text-transform: uppercase; margin-right: 5px; }
    .tag-fl { background: #eff6ff; color: #2563eb; }
    .tag-sc { background: #f0fdf4; color: #16a34a; }
    .tag-cat { background: #f1f5f9; color: #475569; }
</style>
""", unsafe_allow_html=True)

# ── 3. 搜尋資料庫邏輯 ──────────────────────────────────
DB_PATH = Path("doc_db.json")

def load_db():
    if not DB_PATH.exists():
        return []
    return json.loads(DB_PATH.read_text(encoding="utf-8"))

def save_db(data):
    DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

if "docs" not in st.session_state:
    st.session_state.docs = load_db()

# ── 4. 關鍵字過濾引擎 (解決搜尋不準確的核心) ────────────────
def classify_doc(title, url):
    """根據關鍵字自動歸類，確保搜尋準確度"""
    title_l = title.lower()
    
    # A. 判斷品牌
    brand = "Formlabs" if "formlabs" in url or "formlabs" in title_l else "Scanology"
    
    # B. 判斷型號 (字典匹配)
    device = "通用/其他"
    dev_map = {
        "Form 4": ["form 4", "form4"],
        "Form 4L": ["form 4l", "form4l"],
        "Fuse 1": ["fuse 1", "fuse1", "sift"],
        "SIMSCAN30": ["simscan", "simscan30"],
        "KSCANX": ["kscan", "kscanx"]
    }
    for dev, keywords in dev_map.items():
        if any(k in title_l for k in keywords):
            device = dev
            break
            
    # C. 判斷分類
    category = "教學文件"
    cat_map = {
        "Datasheet": ["datasheet", "spec", "規格", "參數"],
        "User Manual": ["manual", "guide", "操作手冊", "指南", "使用說明"],
        "White Paper": ["white paper", "白皮書"],
        "Application Note": ["application", "應用案例", "case"],
        "材料": ["resin", "powder", "樹脂", "粉末", "material"]
    }
    for cat, keywords in cat_map.items():
        if any(k in title_l for k in keywords):
            category = cat
            break
            
    return brand, device, category

# ── 5. 側邊欄：多層級篩選 (預設皆不勾選) ──────────────────
with st.sidebar:
    st.title("SOLIDWIZARD")
    q = st.text_input("🔍 搜尋標題、型號...", placeholder="輸入文字...")

    st.markdown("### 1. 品牌")
    sel_brands = []
    if st.checkbox("Formlabs"): sel_brands.append("Formlabs")
    if st.checkbox("Scanology"): sel_brands.append("Scanology")
    
    st.markdown("### 2. 設備型號")
    dev_dict = {
        "Formlabs": ["Form 4", "Form 4L", "Fuse 1", "通用/其他"],
        "Scanology": ["SIMSCAN30", "KSCANX", "通用/其他"]
    }
    selectable_devs = []
    for b in sel_brands: selectable_devs.extend(dev_dict[b])
    
    sel_devices = [d for d in selectable_devs if st.checkbox(d, key=f"dev_{d}")]
            
    st.markdown("### 3. 文件分類")
    all_cats = ["Datasheet", "White Paper", "Application Note", "User Manual", "教學文件", "材料"]
    sel_cats = [c for c in all_cats if st.checkbox(c, key=f"cat_{c}")]

    st.divider()
    
    # 自動抓取更新按鈕
    if st.button("🔄 執行網站抓取更新", use_container_width=True):
        urls_to_scan = [
            "https://www.3d-scantech.com/resource/",
            "https://formlabs.com/resources/",
            "https://support.formlabs.com/s/?language=zh_CN"
        ]
        new_docs = []
        with st.spinner("掃描中..."):
            for root_url in urls_to_scan:
                try:
                    res = requests.get(root_url, timeout=10)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        link = urljoin(root_url, a['href'])
                        title = a.get_text().strip()
                        
                        # 過濾噪音：必須有標題且是特定路徑
                        if len(title) > 5 and any(x in link for x in ['article', 'product', 'pdf', 'guide']):
                            b, d, c = classify_doc(title, link)
                            doc_id = hashlib.md5(link.encode()).hexdigest()[:8]
                            
                            if not any(item['url'] == link for item in st.session_state.docs):
                                new_docs.append({
                                    "id": doc_id, "brand": b, "device": d, 
                                    "category": c, "title": title, "url": link, 
                                    "date": str(datetime.date.today())
                                })
                except: continue
            
            if new_docs:
                st.session_state.docs.extend(new_docs)
                save_db(st.session_state.docs)
                st.success(f"更新完成！新增 {len(new_docs)} 筆資料")
                st.rerun()
            else:
                st.info("暫無新文件")

# ── 6. 主畫面：搜尋結果 ──────────────────────────────────
st.title("📚 技術文件檢索中心")

# 數據過濾
filtered = [d for d in st.session_state.docs if 
            d["brand"] in sel_brands and 
            d["device"] in sel_devices and 
            d["category"] in sel_cats]

if q:
    filtered = [d for d in filtered if q.lower() in d["title"].lower() or q.lower() in d["device"].lower()]

# 顯示介面
if not sel_brands:
    st.info("👈 請從左側勾選「品牌」開始搜尋。")
elif not filtered:
    st.warning("查無符合條件的文件。")
else:
    st.write(f"📊 找到 {len(filtered)} 份文件")
    for doc in filtered:
        tag_cls = "tag-fl" if doc["brand"] == "Formlabs" else "tag-sc"
        with st.container():
            st.markdown(f"""
            <div class="doc-box">
                <div style="display: flex; justify-content: space-between;">
                    <span class="tag {tag_cls}">{doc['brand']}</span>
                    <span style="font-size: 12px; color: #94a3b8;">{doc['date']}</span>
                </div>
                <div class="doc-title">{doc['title']}</div>
                <div style="margin-bottom: 15px;">
                    <span class="tag tag-cat">{doc['device']}</span>
                    <span class="tag tag-cat">{doc['category']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([1, 5])
            col1.link_button("📂 開啟文件", doc['url'], type="primary")
            if col2.button("🗑️ 移除", key=f"del_{doc['id']}"):
                st.session_state.docs = [x for x in st.session_state.docs if x["id"] != doc["id"]]
                save_db(st.session_state.docs)
                st.rerun()
