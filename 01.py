import streamlit as st
import pandas as pd
import trimesh
import numpy as np
import io
import hashlib
import json
import datetime
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

# --- 1. 專業 UI 配置 ---
st.set_page_config(page_title="SOLIDWIZARD | 報價與技術 Hub", layout="wide")

# 套用整合樣式 (包含 3D 看板與文件卡片)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;600&display=swap');
    
    /* 全域字體與背景 */
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e3a5f; }
    [data-testid="stSidebar"] * { color: #94a3b8 !important; }
    
    /* 3D 報價看板樣式 */
    .price-container { background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .price-result { color: #1e293b; font-size: 32px; font-weight: 800; border-bottom: 2px solid #0081FF; display: inline-block; }
    
    /* 文件卡片樣式 */
    .doc-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; transition: all .2s; cursor: pointer; }
    .doc-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-color: #3b82f6; }
    .tag { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
    .tag-brand-fl { background: #eff6ff; color: #2563eb; }
    .tag-brand-sc { background: #f0fdf4; color: #16a34a; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 資料持久化與狀態初始化 ---
DB_PATH = Path("doc_database.json")
if not DB_PATH.exists():
    DB_PATH.write_text("[]", encoding="utf-8")

if "docs" not in st.session_state:
    st.session_state.docs = json.loads(DB_PATH.read_text(encoding="utf-8"))
if "mesh" not in st.session_state:
    st.session_state.mesh = None

# --- 3. 核心設備與材料數據 ---
PRINTERS = {
    "Form 4": {"w": 200, "d": 125, "h": 210, "brand": "Formlabs"},
    "Form 4L": {"w": 353, "d": 196, "h": 350, "brand": "Formlabs"},
    "Fuse 1+": {"w": 165, "d": 165, "h": 300, "brand": "Formlabs"},
}
SCANNERS = ["SIMSCAN 30", "KSCAN-X", "AXE-B17"]

@st.cache_data
def get_materials():
    return pd.DataFrame({
        "名稱": ["Clear Resin", "Tough 2000", "Rigid 10K", "Grey Pro"],
        "單價": [6900, 8500, 12000, 8500]
    })
df_m = get_materials()

# --- 4. 側邊欄：統一控制中心 ---
with st.sidebar:
    st.title("SOLIDWIZARD")
    
    st.markdown("### 1. 品牌與設備控制")
    sel_brands = []
    c1, c2 = st.columns(2)
    if c1.checkbox("Formlabs", value=True): sel_brands.append("Formlabs")
    if c2.checkbox("Scanology", value=True): sel_brands.append("Scanology")
    
    device_options = []
    if "Formlabs" in sel_brands: device_options += list(PRINTERS.keys())
    if "Scanology" in sel_brands: device_options += SCANNERS
    active_device = st.selectbox("當前操作設備", device_options if device_options else ["請選擇品牌"])

    st.divider()
    
    st.markdown("### 2. 報價參數 (3D專用)")
    m_choice = st.selectbox("選用材料", df_m["名稱"])
    markup = st.slider("報價加成倍率", 1.0, 5.0, 2.0, 0.1)
    qty = st.number_input("生產數量", min_value=1, value=1)

    st.divider()
    
    st.markdown("### 3. 文件分類 (資料庫專用)")
    all_cats = ["Datasheet", "User Manual", "White Paper", "教學文件", "材料"]
    sel_cats = st.multiselect("顯示分類", all_cats, default=all_cats)

# --- 5. 主畫面分頁 ---
tab_quote, tab_docs, tab_admin = st.tabs(["🚀 3D 報價模擬器", "📂 技術文件查詢", "⚙️ 後台管理"])

# --- 5a. 報價分頁邏輯 ---
with tab_quote:
    st.subheader("STL 自動報價分析")
    up_file = st.file_uploader("上傳 STL 檔案", type=["stl"])
    
    if up_file:
        file_bytes = up_file.read()
        mesh = trimesh.load(io.BytesIO(file_bytes), file_type='stl')
        st.session_state.mesh = mesh
        
        vol = abs(mesh.volume) # mm3
        u_price = df_m.loc[df_m["名稱"] == m_choice, "單價"].values[0] / 1000000
        cost = vol * 1.2 * u_price # 預估 20% 支撐消耗
        final_price = cost * markup * qty
        
        st.markdown(f"""
        <div class="price-container">
            <div class="price-result">預估報價 NT$ {final_price:,.0f}</div>
            <p style="color:#64748b; margin-top:10px;">
                設備：{active_device} | 材料：{m_choice} | 總體積：{vol/1000:,.2f} cm³
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.info(f"💡 提示：目前設備 {active_device} 的列印範圍已自動載入參數。")

# --- 5b. 文件查詢分頁 ---
with tab_docs:
    st.subheader("技術文件檢索")
    search_q = st.text_input("🔍 搜尋文件標題或型號...", placeholder="例如：Form 4 操作手冊")
    
    # 篩選邏輯
    docs = st.session_state.docs
    filtered = [d for d in docs if d["brand"] in sel_brands and d["category"] in sel_cats]
    if search_q:
        filtered = [d for d in filtered if search_q.lower() in d["title"].lower()]
    
    if not filtered:
        st.warning("查無相關文件，請調整左側篩選條件。")
    else:
        for d in filtered:
            brand_cls = "tag-brand-fl" if d["brand"] == "Formlabs" else "tag-brand-sc"
            st.markdown(f"""
            <div class="doc-card" onclick="window.open('{d['url']}', '_blank')">
                <div class="doc-card-title">{d['title']}</div>
                <div style="display: flex; gap: 8px;">
                    <span class="tag {brand_cls}">{d['brand']}</span>
                    <span class="tag tag-type">{d['device']}</span>
                    <span class="tag tag-type">{d['category']}</span>
                    <span style="font-size:11px; color:#94a3b8; margin-left:auto;">{d['date']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- 5c. 後台管理 (手動新增與存檔) ---
with tab_admin:
    st.subheader("資料庫管理")
    with st.form("add_doc"):
        st.write("新增單筆文件")
        c1, c2, c3 = st.columns(3)
        nb = c1.selectbox("品牌", ["Formlabs", "Scanology"])
        nd = c2.text_input("適用型號")
        nc = c3.selectbox("類別", all_cats)
        nt = st.text_input("文件名稱")
        nu = st.text_input("URL 連結")
        if st.form_submit_button("確認存入"):
            new_doc = {
                "id": hashlib.md5(nu.encode()).hexdigest()[:8],
                "brand": nb, "device": nd, "category": nc,
                "title": nt, "url": nu, "date": str(datetime.date.today())
            }
            st.session_state.docs.append(new_doc)
            DB_PATH.write_text(json.dumps(st.session_state.docs, ensure_ascii=False), encoding="utf-8")
            st.success("文件已成功加入資料庫！")
            st.rerun()
