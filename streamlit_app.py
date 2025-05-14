import streamlit as st
import pandas as pd
import os

# --- 定数 ---
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

st.title('①案件更新｜クライアント別データ統一アプリ')

# --- マッピングファイルアップロード ---
st.sidebar.header('ステップ1：マッピングファイルをアップロード')
mapping_file = st.sidebar.file_uploader('マッピングファイル（Excel）', type='xlsx')

mapping_dict = {}
unified_cols = []

if mapping_file:
    df_map = pd.read_excel(mapping_file, sheet_name=0, header=None)
    for i in range(0, len(df_map), 2):
        raw = df_map.iloc[i]
        norm = df_map.iloc[i+1]
        client = str(raw.iloc[0]).strip()
        if pd.isna(client): continue
        col_map = {}
        for j in range(2, len(raw)):
            raw_field = raw.iloc[j]
            norm_field = norm.iloc[j]
            if pd.notna(raw_field) and pd.notna(norm_field):
                col_map[raw_field] = norm_field
        mapping_dict[client] = col_map
    unified_cols = sorted({v for d in mapping_dict.values() for v in d.values()})
else:
    st.warning('サイドバーからマッピングファイルをアップロードしてください。')

# --- データ更新処理 ---
if mapping_dict:
    st.header('ステップ2：案件Excelをドラッグ＆ドロップ')
    uploaded_files = st.file_uploader('クライアント案件ファイルをアップロード（複数可）', type='xlsx', accept_multiple_files=True)

    if uploaded_files:
        combined_data = []

        for file in uploaded_files:
            client_name = os.path.splitext(file.name)[0].strip()
            st.subheader(f'▶ {client_name}')

            if client_name not in mapping_dict:
                st.error(f'❌ マッピング定義が見つかりません: {client_name}')
                continue

            try:
                df_raw = pd.read_excel(file, sheet_name=0)  # 1シート限定を前提
                col_map = mapping_dict[client_name]
                df_renamed = df_raw.rename(columns=col_map)
                cols_to_use = [c for c in unified_cols if c in df_renamed.columns]
                df_final = df_renamed[cols_to_use].copy()
                df_final.insert(0, 'client_name', client_name)

                combined_data.append(df_final)

                # 保存
                save_path = os.path.join(DATA_DIR, f'{client_name}.parquet')
                df_final.to_parquet(save_path, index=False)
                st.success(f'✅ {client_name} データを保存しました')

            except Exception as e:
                st.error(f'⚠️ エラー発生: {e}')

        # 全体プレビュー
        if combined_data:
            df_all = pd.concat(combined_data, ignore_index=True)
            st.subheader('✅ 統一形式での結合結果')
            st.dataframe(df_all)
            csv = df_all.to_csv(index=False, encoding='utf-8-sig')
            st.download_button('📥 CSVダウンロード', data=csv, file_name='案件統一一覧.csv')
