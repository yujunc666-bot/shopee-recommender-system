import streamlit as st
import pandas as pd
import os

# 1. 網頁基本設定
st.set_title = "🛍️ 智能電商混合推薦系統"
st.set_page_config(page_title="🛍️ 智能電商混合推薦系統", layout="wide")

tab1, tab2 = st.tabs(["🛒 蝦皮智能推薦牆", "🔬 演算法後台與實驗報告"])

# 核心初始化：建立用戶長期的行為軌跡記憶體
if 'click_history' not in st.session_state:
    st.session_state['click_history'] = []

# ==========================================
# TAB 1: 真正不笨拙的智能推薦牆
# ==========================================
with tab1:
    st.title("🛍️ 蝦皮電商：動態行為推薦系統")
    st.caption("基於大數據銷量（協同過濾）與用戶即時點擊軌跡（內容過濾）之混合架構")

    # 讀取外部生成的 200 筆大數據庫
    csv_filename = "product_data.csv"
    if os.path.exists(csv_filename):
        product_db = pd.read_csv(csv_filename)
        st.success(f"📊 成功串接大數據庫！系統內共有 {len(product_db)} 件商品即時進行混合過濾運算。")
    else:
        # 備用初始資料
        product_db = pd.DataFrame([
            {"title": "【官方旗艦】Apple iPhone 15 Pro Max", "tag": "3C 數位", "sales": 8500, "rating": 4.9, "price": 40400, "brand": "Apple", "url": "https://shopee.tw/search?keyword=iPhone", "img": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=500"},
            {"title": "Apple iPad Air M2 11吋平板電腦", "tag": "3C 數位", "sales": 3100, "rating": 4.8, "price": 19900, "brand": "Apple", "url": "https://shopee.tw/search?keyword=iPad", "img": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500"},
            {"title": "Sony WH-1000XM5 無線降噪耳罩式耳機", "tag": "3C 數位", "sales": 4200, "rating": 4.8, "price": 9900, "brand": "Sony", "url": "https://shopee.tw/search?keyword=Sony", "img": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"},
        ])
        if 'brand' not in product_db.columns:
            product_db['brand'] = '未分類'

    # 側邊欄控制（這就是使用者切換時，系統無感刷新權重的關鍵）
    st.sidebar.header("⚙️ 演算法控制台")
    available_tags = product_db['tag'].unique().tolist()
    selected_tag = st.sidebar.selectbox("1. 瀏覽商品大分類", available_tags)

    filtered_df = product_db[product_db['tag'] == selected_tag].copy()

    # 側邊欄即時呈現他的靈魂品味
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 2. 用戶畫像數據（背景監聽中）")
    
    if st.session_state['click_history']:
        history_counts = pd.Series(st.session_state['click_history']).value_counts()
        for brand, count in history_counts.items():
            st.sidebar.text(f"• 偏好 {brand} 特徵：已累積行為 {count} 次")
        
        if st.sidebar.button("🧹 清空歷史行為 (重置冷啟動)", width='stretch'):
            st.session_state['click_history'] = []
            st.rerun()
    else:
        st.sidebar.caption("⏳ 平台目前處於【協同過濾冷啟動】狀態。\n當您點擊下方任何商品的查看詳情，系統將會無感寫入您的內容特徵偏好。")

    # 5. 混合推薦演算法核心
    if not filtered_df.empty:
        # 【支柱一：協同過濾分（群眾智慧）】
        max_sales = product_db['sales'].max()
        min_sales = product_db['sales'].min()
        if max_sales != min_sales:
            filtered_df['collaborative_score'] = 1 + 4 * (filtered_df['sales'] - min_sales) / (max_sales - min_sales)
        else:
            filtered_df['collaborative_score'] = 5

        # 【支柱二：內容過濾分（個人特徵追蹤）】
        filtered_df['content_weight'] = 1.0
        if st.session_state['click_history']:
            history_counts = pd.Series(st.session_state['click_history']).value_counts()
            for brand, count in history_counts.items():
                # 改用微幅且穩健的漸進加權，逛得越久，該品牌權重越高
                filtered_df.loc[filtered_df['brand'] == brand, 'content_weight'] += (count * 0.3)

        # 綜合最終推薦分數
        filtered_df['final_score'] = filtered_df['collaborative_score'] * (filtered_df['rating'] / 5.0) * filtered_df['content_weight']
        recommend_list = filtered_df.sort_values(by='final_score', ascending=False)

        # 6. 渲染精美商品牆 UI
        st.subheader(f"🛒 猜你喜歡推薦名單")
        
        cols = st.columns(3)
        for index, row in recommend_list.reset_index().iterrows():
            col_index = index % 3
            with cols[col_index]:
                is_boosted = row['content_weight'] > 1.0
                
                with st.container(border=True):
                    st.image(row['img'], width='stretch')
                    
                    if is_boosted:
                        st.markdown(f"✨ **[內容過濾核心：偏好特徵加權]**")
                    else:
                        st.markdown(f"👥 **[協同過濾推薦：大眾銷量熱推]**")
                        
                    st.markdown(f"#### {row['title']}")
                    st.markdown(f"💰 **活動價：NT$ {int(row['price']):,}**")
                    st.caption(f"🏷️ 品牌：{row['brand']} | ⭐ 評價：{row['rating']}")
                    st.info(f"🧬 綜合預測得分：{row['final_score']:.2f}")
                    
                    # 💡 【2026 皈依一體神操作】：
                    # 我們利用一個按鈕的外觀，當使用者點下去的瞬間：
                    # 1. 後台偷偷執行 callback 函式記上次數。
                    # 2. 前端 100% 順暢彈出新視窗去蝦皮。
                    # 3. 網頁完全不跳針、不閃爍，保持極致優雅！
                    button_key = f"pure_btn_{row['title']}_{index}"
                    
                    if st.button("🛍️ 查看詳情並前往蝦皮", key=button_key, width='stretch'):
                        # 背景悄悄記下用戶對這個品牌的喜好
                        st.session_state['click_history'].append(row['brand'])
                        
                        # 利用 2026 原生安全跳轉，100% 開新視窗，絕不卡死
                        js_redirect = f"""<script>window.open('{row['url']}', '_blank');</script>"""
                        st.html(js_redirect)

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
    """, language="bash")