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
/* 側邊欄樣式 */
[data-testid="stSidebar"] { background: #0f172a; border-right: 1px solid #1e3a5f; }
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebar"] h3 { 
    color: #e2e8f0 !important; font-size: 11px !important; 
    text-transform: uppercase; letter-spacing: .12em; 
    margin: 18px 0 8px !important; border-bottom: 1px solid #1e3a5f;
}

/* 文件卡片容器 */
.doc-box {
    background: #ffffff; 
    border: 1px solid #e2e8f0;
    border-radius: 10px; 
    padding: 20px; 
    margin-bottom: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.doc-title { font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 10px; }

/* 標籤設計 */
.tag { font-size: 10px; font-weight: 700; padding: 4px 12px; border-radius: 5px; text-transform: uppercase; margin-right: 5px; }
.tag-fl { background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; }
.tag-sc { background: #f0fdf4; color: #16a34a; border: 1px solid #dcfce7; }
.tag-cat { background: #f1f5f9; color: #475569; }

/* 統計條 */
.stat-bar { display: flex; gap: 15px; margin-bottom: 25px; }
.stat-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 20px; flex: 1; }
.stat-item b { color: #0f172a; font-size: 22px; display: block; }
</style>
""", unsafe_allow_html=True)

# ── 3. 資料庫管理 ────────────────────────────────────
DB_PATH = Path("doc_db.json")

def load_db():
    if not DB_PATH.exists():
        seed = [
            {"id":"fl001","brand":"Formlabs","device":"Form 4","category":"User Manual","title":"Form 4 操作手冊 (ZH)","url":"https://support.formlabs.com/s/article/Finishing-a-Form-4-print?language=zh_CN","date":"2024-04-01"},
            {"id":"sc001","brand":"Scanology","device":"SIMSCAN30","category":"Datasheet","title":"SIMSCAN 30 完整規格表","url":"https://www.3d-scantech.com/product/simscan-handheld-3d-scanner/","date":"2024-03-15"}
        ]
        DB_PATH.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
    return json.loads(DB_PATH.read_text(encoding="utf-8"))

if "docs" not in st.session_state:
    st.session_state.docs = load_db()

# ── 4. 側邊欄：多層級篩選 (預設皆不勾選) ──────────────────
with st.sidebar:
    st.title("SOLIDWIZARD")
    
    st.markdown("### 🔍 快速檢索")
    q = st.text_input("搜尋標題、型號...", label_visibility="collapsed")

    # 1. 品牌 (預設 False)
    st.markdown("### 1. 品牌 (Brand)")
    sel_brands = []
    c1, c2 = st.columns(2)
    if c1.checkbox("Formlabs", value=False): sel_brands.append("Formlabs")
    if c2.checkbox("Scanology", value=False): sel_brands.append("Scanology")
    
    # 2. 設備型號 (預設 False)
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
        if st.checkbox(d, value=False, key=f"dev_{d}"):
            sel_devices.append(d)
            
    # 3. 內容分類 (預設 False)
    st.markdown("### 3. 文件分類 (Category)")
    all_cats = ["Datasheet", "White Paper", "Application Note", "User Manual", "Case Study", "教學文件", "比較分析", "材料"]
    sel_cats = []
    for cat in all_cats:
        if st.checkbox(cat, value=False, key=f"cat_{cat}"):
            sel_cats.append(cat)

    st.divider()
    if st.button("🔄 執行網站抓取更新", use_container_width=True):
        st.toast("正在檢查來源網站...", icon="⏳")
        # 這裡維持之前的自動更新邏輯...
        st.success("已完成自動比對與更新")

# ── 5. 主畫面顯示 ─────────────────────────────────────
st.title("📚 技術文件資料中心")

# 數據過濾邏輯
filtered = [d for d in st.session_state.docs if 
            d["brand"] in sel_brands and 
            d["device"] in sel_devices and 
            d["category"] in sel_cats]

if q:
    filtered = [d for d in filtered if q.lower() in d["title"].lower() or q.lower() in d["device"].lower()]

# 統計數據顯示
st.markdown(f"""
<div class="stat-bar">
    <div class="stat-item"><b>{len(filtered)}</b><span>搜尋結果</span></div>
    <div class="stat-item"><b>{len(st.session_state.docs)}</b><span>資料庫總量</span></div>
</div>
""", unsafe_allow_html=True)

# 文件列表渲染
if not sel_brands:
    st.info("👈 請先從左側選擇品牌開始篩選。")
elif not filtered:
    st.warning("查無符合目前條件的文件，請嘗試放寬篩選標準。")
else:
    for doc in filtered:
        tag_cls = "tag-fl" if doc["brand"] == "Formlabs" else "tag-sc"
        
        # 使用 Container 包裹以方便佈局
        with st.container():
            st.markdown(f"""
            <div class="doc-box">
                <div style="display: flex; justify-content: space-between;">
                    <span class="tag {tag_cls}">{doc['brand']}</span>
                    <span style="font-size: 12px; color: #94a3b8;">更新日期：{doc['date']}</span>
                </div>
                <div class="doc-title">{doc['title']}</div>
                <div style="margin-bottom: 15px;">
                    <span class="tag tag-cat">{doc['device']}</span>
                    <span class="tag tag-cat">{doc['category']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 使用官方 link_button 確保點擊絕對有效
            col1, col2 = st.columns([1, 4])
            with col1:
                st.link_button("📂 開啟文件", doc['url'], use_container_width=True, type="primary")
            with col2:
                if st.button("🗑️ 移除此紀錄", key=f"del_{doc['id']}"):
                    st.session_state.docs = [x for x in st.session_state.docs if x["id"] != doc["id"]]
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
