import streamlit as st
import pandas as pd
import os

# --- 定数 ---
DATA_DIR = 'data'
MAPPING_FILE = 'mapping_fixed.xlsx'
DISPLAY_ORDER_FILE = '統一データ表示項目.xlsx'
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="案件更新アプリ", layout="wide")
st.title('①案件更新｜クライアント別データ統一アプリ')

# --- 固定マッピングファイル読み込み ---
mapping_dict = {}
unified_cols = []
preferred_order = []

try:
    df_map = pd.read_excel(MAPPING_FILE)
    required_cols = ['クライアント名', '生データ項目', '統一後タイトル']
    if all(col in df_map.columns for col in required_cols):
        for client in df_map['クライアント名'].unique():
            sub_df = df_map[df_map['クライアント名'] == client]
            mapping_dict[client] = dict(zip(sub_df['生データ項目'], sub_df['統一後タイトル']))
        unified_cols = sorted(df_map['統一後タイトル'].unique().tolist())
    else:
        st.error("mapping_fixed.xlsx に必要な列（クライアント名、生データ項目、統一後タイトル）が見つかりません")
except FileNotFoundError:
    st.error("mapping_fixed.xlsx がリポジトリ内に見つかりません。アップロードまたは配置してください。")

# --- 表示順ファイル読み込み ---
try:
    df_order = pd.read_excel(DISPLAY_ORDER_FILE, header=None)
    preferred_order = df_order.iloc[:, 0].dropna().astype(str).tolist()
except FileNotFoundError:
    st.error("統一データ表示項目.xlsx が見つかりません。")

# --- データ更新処理 ---
if mapping_dict and preferred_order:
    st.header('ステップ：案件Excelをドラッグ＆ドロップ')
    uploaded_files = st.file_uploader(
        label='📂 クライアント案件ファイルをアップロード（複数可）',
        type='xlsx',
        accept_multiple_files=True,
        help='ファイル名＝クライアント名、シートは1枚のみとしてください'
    )

    if uploaded_files:
        combined_data = []

        for file in uploaded_files:
            client_name = os.path.splitext(file.name)[0].strip()
            st.subheader(f'▶ {client_name}')

            if client_name not in mapping_dict:
                st.error(f'❌ マッピング定義が見つかりません: {client_name}')
                continue

            try:
                df_raw = pd.read_excel(file, sheet_name=0)
                col_map = mapping_dict[client_name]
                df_renamed = df_raw.rename(columns=col_map)

                # 指定された順序で列を並べる（存在する列のみ）
                ordered_cols = [col for col in preferred_order if col in df_renamed.columns]
                df_final = df_renamed[ordered_cols].copy()
                df_final.insert(0, 'client_name', client_name)

                combined_data.append(df_final)

                save_path = os.path.join(DATA_DIR, f'{client_name}.parquet')
                df_final.to_parquet(save_path, index=False)
                st.success(f'✅ {client_name} データを保存しました')

            except Exception as e:
                st.error(f'⚠️ エラー発生: {e}')

        if combined_data:
            df_all = pd.concat(combined_data, ignore_index=True)
            st.subheader('✅ 統一形式での結合結果（指定順）')
            st.dataframe(df_all)
            csv = df_all.to_csv(index=False, encoding='utf-8-sig')
            st.download_button('📥 CSVダウンロード', data=csv, file_name='案件統一一覧.csv')
