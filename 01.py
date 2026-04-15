import streamlit as st
import pandas as pd
import json
import hashlib
import datetime
from pathlib import Path

# ── 1. 頁面配置 ─────────────────────────────────────
st.set_page_config(
    page_title="SOLIDWIZARD | 業務技術資源庫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 2. 核心樣式 (CSS) ──────────────────────────────────
st.markdown("""
<style>
/* 側邊欄：專業深色主題 */
[data-testid="stSidebar"] { background: #0f172a; border-right: 1px solid #1e3a5f; }
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebar"] h3 { 
    color: #e2e8f0 !important; font-size: 11px !important; 
    text-transform: uppercase; letter-spacing: .12em; 
    margin: 18px 0 8px !important; border-bottom: 1px solid #1e3a5f;
    padding-bottom: 4px;
}

/* 文件卡片 */
.doc-card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 16px; margin-bottom: 12px;
    transition: all 0.2s ease-in-out; cursor: pointer;
}
.doc-card:hover { 
    transform: translateY(-3px); 
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); 
    border-color: #3b82f6; 
}
.doc-card-title { font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }

/* 標籤設計 */
.tag { font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 4px; text-transform: uppercase; }
.tag-fl { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; }
.tag-sc { background: #f0fdf4; color: #16a34a; border: 1px solid #dcfce7; }
.tag-cat { background: #f1f5f9; color: #475569; }

/* 統計條 */
.stat-bar { display: flex; gap: 15px; margin-bottom: 25px; }
.stat-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 20px; }
.stat-item b { color: #0f172a; font-size: 20px; display: block; line-height: 1; }
.stat-item span { font-size: 12px; color: #64748b; }
</style>
""", unsafe_allow_html=True)

# ── 3. 資料庫管理 ────────────────────────────────────
DB_PATH = Path("doc_db.json")

def load_db():
    if not DB_PATH.exists():
        # 初始化預設資料
        seed = [
            {"id":"fl001","brand":"Formlabs","device":"Form 4","category":"User Manual","title":"Form 4 操作手冊 (ZH)","url":"https://support.formlabs.com","date":"2024-04-01"},
            {"id":"sc001","brand":"Scanology","device":"SIMSCAN30","category":"Datasheet","title":"SIMSCAN 30 完整規格表","url":"https://www.3d-scantech.com","date":"2024-03-15"}
        ]
        DB_PATH.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
    return json.loads(DB_PATH.read_text(encoding="utf-8"))

def save_db(data):
    DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

if "docs" not in st.session_state:
    st.session_state.docs = load_db()

# ── 4. 側邊欄：多層級篩選 (Faceted Navigation) ──────────
with st.sidebar:
    st.image("https://formlabs.com/favicon.ico", width=30)
    st.title("SOLIDWIZARD")
    
    # 關鍵字搜尋
    st.markdown("### 🔍 快速檢索")
    q = st.text_input("搜尋標題、型號...", label_visibility="collapsed")

    # 第一層：品牌
    st.markdown("### 1. 品牌 (Brand)")
    sel_brands = []
    c1, c2 = st.columns(2)
    if c1.checkbox("Formlabs", value=True): sel_brands.append("Formlabs")
    if c2.checkbox("Scanology", value=True): sel_brands.append("Scanology")
    
    # 第二層：設備類型 (隨品牌連動)
    st.markdown("### 2. 設備型號 (Device)")
    dev_dict = {
        "Formlabs": ["Form 4", "Form 4L", "Fuse 1"],
        "Scanology": ["SIMSCAN30", "KSCANX"]
    }
    
    available_devices = []
    for b in sel_brands:
        available_devices.extend(dev_dict[b])
    
    sel_devices = []
    for d in available_devices:
        if st.checkbox(d, value=True, key=f"dev_{d}"):
            sel_devices.append(d)
            
    # 第三層：內容分類
    st.markdown("### 3. 文件分類 (Category)")
    all_cats = ["Datasheet", "White Paper", "Application Note", "User Manual", "Case Study", "教學文件", "比較分析", "材料"]
    sel_cats = []
    for cat in all_cats:
        if st.checkbox(cat, value=True, key=f"cat_{cat}"):
            sel_cats.append(cat)

    st.divider()
    
    # 後台更新按鈕 (取消審核機制，直接加入)
    if st.button("🔄 執行網站抓取更新", use_container_width=True):
        with st.spinner("正在掃描來源網站..."):
            # 模擬爬蟲邏輯：在此處對接實際抓取代碼
            new_id = hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:8]
            new_entry = {
                "id": new_id,
                "brand": "Formlabs",
                "device": "Form 4",
                "category": "Application Note",
                "title": f"自動偵測：新應用案例 - {datetime.date.today()}",
                "url": "https://formlabs.com",
                "date": str(datetime.date.today())
            }
            
            # 檢查是否重複 (以 URL 或標題判斷)
            existing_titles = [d["title"] for d in st.session_state.docs]
            if new_entry["title"] not in existing_titles:
                st.session_state.docs.insert(0, new_entry) # 插在最前面
                save_db(st.session_state.docs)
                st.success(f"已自動更新：{new_entry['title']}")
                st.rerun()
            else:
                st.info("目前無新文件需要更新。")

# ── 5. 主畫面顯示 ─────────────────────────────────────
st.title("📚 技術文件資料中心")

# 統計數據顯示
filtered = [d for d in st.session_state.docs if 
            d["brand"] in sel_brands and 
            d["device"] in sel_devices and 
            d["category"] in sel_cats]

if q:
    filtered = [d for d in filtered if q.lower() in d["title"].lower() or q.lower() in d["device"].lower()]

st.markdown(f"""
<div class="stat-bar">
    <div class="stat-item"><b>{len(filtered)}</b><span>符合條件</span></div>
    <div class="stat-item"><b>{len(st.session_state.docs)}</b><span>總庫存量</span></div>
    <div class="stat-item"><b>{datetime.date.today().strftime('%Y/%m/%d')}</b><span>最後同步</span></div>
</div>
""", unsafe_allow_html=True)

# 文件列表渲染
if not filtered:
    st.info("目前的篩選條件下沒有找到文件。")
else:
    for doc in filtered:
        tag_cls = "tag-fl" if doc["brand"] == "Formlabs" else "tag-sc"
        st.markdown(f"""
        <div class="doc-card" onclick="window.open('{doc['url']}', '_blank')">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div class="doc-card-title">{doc['title']}</div>
                <span style="font-size: 11px; color: #94a3b8;">{doc['date']}</span>
            </div>
            <div style="display: flex; gap: 8px; margin-top: 5px;">
                <span class="tag {tag_cls}">{doc['brand']}</span>
                <span class="tag tag-cat">{doc['device']}</span>
                <span class="tag tag-cat">{doc['category']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 為了保持介面整潔，移除按鈕放在卡片下方
        if st.button("🗑️ 移除", key=f"del_{doc['id']}"):
            st.session_state.docs = [d for d in st.session_state.docs if d["id"] != doc["id"]]
            save_db(st.session_state.docs)
            st.rerun()
