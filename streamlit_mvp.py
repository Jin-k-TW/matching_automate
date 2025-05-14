import streamlit as st
import pandas as pd
import os

# --- 定数設定 ---
MAPPING_FILE = 'クライアント生データ＆統一フォーマット.xlsx'
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# --- マッピング定義読み込み ---
@st.cache_data
def load_mapping(path: str) -> dict:
    df_map = pd.read_excel(path, sheet_name='Sheet1', header=None)
    mapping = {}
    for i in range(0, len(df_map), 2):
        raw = df_map.iloc[i]
        norm = df_map.iloc[i+1]
        client = raw.iloc[0]
        if pd.isna(client):
            continue
        col_map = {}
        for j in range(2, len(raw)):
            raw_field = raw.iloc[j]
            norm_field = norm.iloc[j]
            if pd.notna(raw_field) and pd.notna(norm_field):
                col_map[raw_field] = norm_field
        mapping[client] = col_map
    return mapping

# マッピングと統一項目をロード
mapping_dict = load_mapping(MAPPING_FILE)
unified_cols = sorted({v for cols in mapping_dict.values() for v in cols.values()})

# アプリタイトル
st.title('①案件更新 & マスタ管理')

# モード選択
mode = st.sidebar.selectbox('モード選択', ['データ更新', 'マスタ確認'])

if mode == 'データ更新':
    st.header('クライアントデータ更新 (ドラッグ＆ドロップ)')
    uploaded_files = st.file_uploader('Excelファイルを選択', type='xlsx', accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            client = os.path.splitext(f.name)[0]
            st.write(f'▶ 更新処理: {client}')
            df_raw = pd.read_excel(f)
            if client not in mapping_dict:
                st.error(f'マッピング定義なし: {client}')
                continue
            df_norm = df_raw.rename(columns=mapping_dict[client])
            cols = [c for c in unified_cols if c in df_norm.columns]
            df_sel = df_norm[cols].copy()
            df_sel.insert(0, 'client_name', client)
            path = os.path.join(DATA_DIR, f'{client}.parquet')
            df_sel.to_parquet(path, index=False)
            st.success(f'{client} を更新しました')

elif mode == 'マスタ確認':
    st.header('全クライアントマスタプレビュー')
    dfs = []
    for fn in os.listdir(DATA_DIR):
        if fn.endswith('.parquet'):
            dfs.append(pd.read_parquet(os.path.join(DATA_DIR, fn)))
    if dfs:
        df_master = pd.concat(dfs, ignore_index=True)
        st.dataframe(df_master)
        csv = df_master.to_csv(index=False, encoding='utf-8-sig')
        st.download_button('CSV ダウンロード', data=csv, file_name='master_jobs.csv')
    else:
        st.info('まだ更新されたデータがありません')
