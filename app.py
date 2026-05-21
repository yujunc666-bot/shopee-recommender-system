import streamlit as st
import pandas as pd
import os

# 1. 網頁基本設定
st.set_page_config(page_title="🛍️ 永久紀錄型混合推薦系統", layout="wide")

tab1, tab2 = st.tabs(["🛒 蝦皮智能推薦牆", "🔬 演算法後台與實驗報告"])

# ==========================================
# 📊 核心技術：實體檔案持久化機制
# ==========================================
COUNTER_FILE = "user_clicks.csv"

# 初始化或讀取雲端實體硬碟裡的次數紀錄
if not os.path.exists(COUNTER_FILE):
    df_init = pd.DataFrame(columns=["brand", "count"])
    df_init.to_csv(COUNTER_FILE, index=False, encoding="utf-8-sig")

def get_permanent_clicks():
    """從實體 CSV 讀取最新的累計次數"""
    try:
        df = pd.read_csv(COUNTER_FILE)
        return df.set_index("brand")["count"].to_dict()
    except:
        return {}

def save_permanent_click(brand_name):
    """將點擊次數永久寫入實體 CSV 檔案"""
    try:
        df = pd.read_csv(COUNTER_FILE)
        if brand_name in df["brand"].values:
            df.loc[df["brand"] == brand_name, "count"] += 1
        else:
            new_row = pd.DataFrame([{"brand": brand_name, "count": 1}])
            df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(COUNTER_FILE, index=False, encoding="utf-8-sig")
    except Exception as e:
        pass

# 將讀取到的實體數據同步
current_clicks = get_permanent_clicks()

# ==========================================
# TAB 1: 真正不笨拙的智能推薦牆
# ==========================================
with tab1:
    st.title("🛍️ 蝦皮電商：永久紀錄行為推薦系統")
    st.caption("本系統已導入實體 CSV 數據持久化技術，所有用戶的集體點擊將被永久保存於雲端伺服器")

    # 讀取外部生成的 200 筆大數據庫
    csv_filename = "product_data.csv"
    if os.path.exists(csv_filename):
        product_db = pd.read_csv(csv_filename)
        st.success(f"📊 成功串接大數據庫！系統內共有 {len(product_db)} 件商品即時進行混合過濾運算。")
    else:
        st.error("找不到商品大數據庫 product_data.csv，請確認檔案已上傳至 GitHub 同一個目錄下。")
        st.stop()

    # 側邊欄控制
    st.sidebar.header("⚙️ 演算法控制台")
    available_tags = product_db['tag'].unique().tolist()
    selected_tag = st.sidebar.selectbox("1. 瀏覽商品大分類", available_tags)

    filtered_df = product_db[product_db['tag'] == selected_tag].copy()

    # 側邊欄呈現全天候累計數據
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 2. 全域用戶群眾畫像 (已寫入雲端硬碟)")
    
    if current_clicks:
        for brand, count in current_clicks.items():
            st.sidebar.text(f"• 歷史集體偏好 【{brand}】：已累積行為 {count} 次")
        
        if st.sidebar.button("🧹 管理員特權：重置雲端資料庫", width='stretch'):
            if os.path.exists(COUNTER_FILE):
                os.remove(COUNTER_FILE)
            st.rerun()
    else:
        st.sidebar.caption("⏳ 雲端資料庫目前為空。")

    # 5. 混合推薦演算法核心
    if not filtered_df.empty:
        # 【支柱一：協同過濾分數】
        max_sales = product_db['sales'].max()
        min_sales = product_db['sales'].min()
        if max_sales != min_sales:
            filtered_df['collaborative_score'] = 1 + 4 * (filtered_df['sales'] - min_sales) / (max_sales - min_sales)
        else:
            filtered_df['collaborative_score'] = 5

        # 【支柱二：內容過濾分數】
        filtered_df['content_weight'] = 1.0
        for brand, count in current_clicks.items():
            filtered_df.loc[filtered_df['brand'] == brand, 'content_weight'] += (count * 0.4)

        # 綜合最終推薦分數
        filtered_df['final_score'] = filtered_df['collaborative_score'] * (filtered_df['rating'] / 5.0) * filtered_df['content_weight']
        recommend_list = filtered_df.sort_values(by='final_score', ascending=False)

        # 6. 渲染精美商品牆 UI
        st.subheader(f"🛒 猜你喜歡推薦名單 (演算法動態重排中)")
        
        cols = st.columns(3)
        for index, row in recommend_list.reset_index().iterrows():
            col_index = index % 3
            with cols[col_index]:
                is_boosted = current_clicks.get(row['brand'], 0) > 0
                
                with st.container(border=True):
                    st.image(row['img'], width='stretch')
                    
                    if is_boosted:
                        st.markdown(f"✨ **[內容過濾：群眾意圖加權 x{filtered_df.loc[filtered_df['brand'] == row['brand'], 'content_weight'].values[0]:.1f}]**")
                    else:
                        st.markdown(f"👥 **[協同過濾推薦：大眾銷量熱推]**")
                        
                    st.markdown(f"#### {row['title']}")
                    st.markdown(f"💰 **活動價：NT$ {int(row['price']):,}**")
                    st.caption(f"🏷️ 品牌：{row['brand']} | ⭐ 評價：{row['rating']}")
                    st.info(f"🧬 綜合預測得分：{row['final_score']:.2f}")
                    
                    button_key = f"final_perm_btn_{row['title']}_{index}"
                    
                    if st.button("🛍️ 查看詳情並前往蝦皮", key=button_key, width='stretch'):
                        # 動作 1：後台立刻寫入實體檔案
                        save_permanent_click(row['brand'])
                        
                        # 動作 2 & 3：用純前端 JS 同時控制「開新分頁」與「原網頁重新載入更新排序」
                        js_combination = f"""
                        <script>
                            window.open('{row['url']}', '_blank');
                            window.parent.location.reload();
                        </script>
                        """
                        st.html(js_combination)
    else:
        st.error("此分類下無商品資料。")

# ==========================================
# TAB 2: 聯網實驗報告
# ==========================================
with tab2:
    st.header("🔬 蝦皮平台實時聯網可行性實驗報告")
    st.code("【伺服器回應狀態碼】: 403\n❌ 觸發蝦皮防禦機制 (403 Forbidden)！\n原因：蝦皮防火牆偵測到此連線為自動化 Python 腳本，已直接封鎖您的 IP 請求。", language="bash")    filtered_df = product_db[product_db['tag'] == selected_tag].copy()

    # 側邊欄呈現全天候累計數據
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 2. 全域用戶群眾畫像 (已寫入雲端硬碟)")
    
    if current_clicks:
        for brand, count in current_clicks.items():
            st.sidebar.text(f"• 歷史集體偏好 【{brand}】：已累積行為 {count} 次")
        
        if st.sidebar.button("🧹 管理員特權：重置雲端資料庫", width='stretch'):
            if os.path.exists(COUNTER_FILE):
                os.remove(COUNTER_FILE)
            st.rerun()
    else:
        st.sidebar.caption("⏳ 雲端資料庫目前為空。")

    # 5. 混合推薦演算法核心
    if not filtered_df.empty:
        # 【支柱一：協同過濾分數】
        max_sales = product_db['sales'].max()
        min_sales = product_db['sales'].min()
        if max_sales != min_sales:
            filtered_df['collaborative_score'] = 1 + 4 * (filtered_df['sales'] - min_sales) / (max_sales - min_sales)
        else:
            filtered_df['collaborative_score'] = 5

        # 【支柱二：內容過濾分數】
        filtered_df['content_weight'] = 1.0
        for brand, count in current_clicks.items():
            filtered_df.loc[filtered_df['brand'] == brand, 'content_weight'] += (count * 0.4)

        # 綜合最終推薦分數
        filtered_df['final_score'] = filtered_df['collaborative_score'] * (filtered_df['rating'] / 5.0) * filtered_df['content_weight']
        recommend_list = filtered_df.sort_values(by='final_score', ascending=False)

        # 6. 渲染精美商品牆 UI
        st.subheader(f"🛒 猜你喜歡推薦名單 (演算法動態重排中)")
        
        cols = st.columns(3)
        for index, row in recommend_list.reset_index().iterrows():
            col_index = index % 3
            with cols[col_index]:
                is_boosted = current_clicks.get(row['brand'], 0) > 0
                
                with st.container(border=True):
                    st.image(row['img'], width='stretch')
                    
                    if is_boosted:
                        st.markdown(f"✨ **[內容過濾：群眾意圖加權 x{filtered_df.loc[filtered_df['brand'] == row['brand'], 'content_weight'].values[0]:.1f}]**")
                    else:
                        st.markdown(f"👥 **[協同過濾推薦：大眾銷量熱推]**")
                        
                    st.markdown(f"#### {row['title']}")
                    st.markdown(f"💰 **活動價：NT$ {int(row['price']):,}**")
                    st.caption(f"🏷️ 品牌：{row['brand']} | ⭐ 評價：{row['rating']}")
                    st.info(f"🧬 綜合預測得分：{row['final_score']:.2f}")
                    
                    button_key = f"final_perm_btn_{row['title']}_{index}"
                    
                    if st.button("🛍️ 查看詳情並前往蝦皮", key=button_key, width='stretch'):
                        # 動作 1：後台立刻寫入實體檔案（永久紀錄）
                        save_permanent_click(row['brand'])
                        
                        # 💡 動作 2 & 3（神修正）：用純前端 JS 同時控制「開新分頁」與「原網頁重新載入更新排序」，避開 Python rerun 衝突！
                        js_combination = f"""
                        <script>
                            // 1. 打開外部蝦皮網站
                            window.open('{row['url']}', '_blank');
                            // 2. 讓原本的 Streamlit 網頁自己重新整理更新排序，不跟後台撞車
                            window.parent.location.reload();
                        </script>
                        """
                        st.html(js_combination)
    else:
        st.error("此分類下無商品資料。")

# ==========================================
# TAB 2: 聯網實驗報告
# ==========================================
with tab2:
    st.header("🔬 蝦皮平台實時聯網可行性實驗報告")
    st.code("""
    【伺服器回應狀態碼】: 403
    ❌ 觸發蝦皮防禦機制 (403 Forbidden)！
    原因：蝦皮防火牆偵測到此連線為自動化 Python 腳本，已直接封鎖您的 IP 請求。
    """, language="bash")    available_tags = product_db['tag'].unique().tolist()
    selected_tag = st.sidebar.selectbox("1. 瀏覽商品大分類", available_tags)

    filtered_df = product_db[product_db['tag'] == selected_tag].copy()

    # 側邊欄：這時候呈現的就是「全天候所有人」累積的真實用戶畫像數據！
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 2. 全域用戶群眾畫像 (已寫入雲端硬碟)")
    
    if current_clicks:
        for brand, count in current_clicks.items():
            st.sidebar.text(f"• 歷史集體偏好 【{brand}】：已累積行為 {count} 次")
        
        if st.sidebar.button("🧹 管理員特權：重置雲端資料庫", width='stretch'):
            if os.path.exists(COUNTER_FILE):
                os.remove(COUNTER_FILE)
            st.rerun()
    else:
        st.sidebar.caption("⏳ 雲端資料庫目前為空（純大眾協同過濾冷啟動狀態）。")

    # 5. 混合推薦演算法核心
    if not filtered_df.empty:
        # 【支柱一：協同過濾分數（大眾銷量基準）】
        max_sales = product_db['sales'].max()
        min_sales = product_db['sales'].min()
        if max_sales != min_sales:
            filtered_df['collaborative_score'] = 1 + 4 * (filtered_df['sales'] - min_sales) / (max_sales - min_sales)
        else:
            filtered_df['collaborative_score'] = 5

        # 【支柱二：內容過濾分數（從實體檔案讀取全域喜好進行特徵加權）】
        filtered_df['content_weight'] = 1.0
        for brand, count in current_clicks.items():
            filtered_df.loc[filtered_df['brand'] == brand, 'content_weight'] += (count * 0.4)

        # 綜合最終推薦分數
        filtered_df['final_score'] = filtered_df['collaborative_score'] * (filtered_df['rating'] / 5.0) * filtered_df['content_weight']
        recommend_list = filtered_df.sort_values(by='final_score', ascending=False)

        # 6. 渲染精美商品牆 UI
        st.subheader(f"🛒 猜你喜歡推薦名單 (演算法動態重排中)")
        
        cols = st.columns(3)
        for index, row in recommend_list.reset_index().iterrows():
            col_index = index % 3
            with cols[col_index]:
                is_boosted = current_clicks.get(row['brand'], 0) > 0
                
                with st.container(border=True):
                    st.image(row['img'], width='stretch')
                    
                    if is_boosted:
                        st.markdown(f"✨ **[內容過濾：群眾意圖加權 x{filtered_df.loc[filtered_df['brand'] == row['brand'], 'content_weight'].values[0]:.1f}]**")
                    else:
                        st.markdown(f"👥 **[協同過濾推薦：大眾銷量熱推]**")
                        
                    st.markdown(f"#### {row['title']}")
                    st.markdown(f"💰 **活動價：NT$ {int(row['price']):,}**")
                    st.caption(f"🏷️ 品牌：{row['brand']} | ⭐ 評價：{row['rating']}")
                    st.info(f"🧬 綜合預測得分：{row['final_score']:.2f}")
                    
                    # 唯一核心按鈕：點擊時「寫入實體 CSV」+「彈出蝦皮」
                    button_key = f"perm_btn_{row['title']}_{index}"
                    
                    if st.button("🛍️ 查看詳情並前往蝦皮", key=button_key, width='stretch'):
                        # 核心動作 1：直接修改雲端硬碟裡的 CSV 檔案（關掉網頁也不會丟失！）
                        save_permanent_click(row['brand'])
                        
                        # 核心動作 2：100% 成功跨分頁跳轉
                        js_redirect = f"""<script>window.open('{row['url']}', '_blank');</script>"""
                        st.html(js_redirect)
                        
                        # 核心動作 3：即時刷新畫面
                        st.rerun()
    else:
        st.error("此分類下無商品資料。")

# ==========================================
# TAB 2: 聯網實驗報告
# ==========================================
with tab2:
    st.header("🔬 蝦皮平台實時聯網可行性實驗报告")
    st.code("""
    【伺服器回應狀態碼】: 403
    ❌ 觸發蝦皮防禦機制 (403 Forbidden)！
    原因：蝦皮防火牆偵測到此連線為自動化 Python 腳本，已直接封鎖您的 IP 請求。
    """, language="bash")
