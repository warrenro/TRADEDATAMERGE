import pandas as pd
import uuid
from tqdm import tqdm

# 註冊 tqdm 到 pandas apply，以便在 apply 操作中顯示進度條
tqdm.pandas()

def clean_numeric_column(series: pd.Series) -> pd.Series:
    """
    清理數值欄位，移除千分位逗號、引號，並轉換為整數。
    - 移除千位數逗號和引號。
    - 移除小數點及其後數字。
    - 將無法轉換的錯誤值填充為0，最後轉換為64位元整數。
    """
    # 移除逗號和引號
    cleaned_series = series.astype(str).str.replace(',', '', regex=False).str.replace('"', '', regex=False)
    # 移除小數點及其後數字
    numeric_series = pd.to_numeric(cleaned_series.str.split('.').str[0], errors='coerce').fillna(0).astype('int64')
    return numeric_series

def find_open_time(row: pd.Series, df_records: pd.DataFrame, search_range: int = 5) -> pd.Timestamp:
    """
    根據平倉紀錄的序號，在《成交紀錄》中查找對應的新倉時間。
    查找範圍為平倉紀錄序號的「前後5筆」。
    """
    # 定義查找範圍
    start_seq = max(0, row['序號'] - search_range)
    # 根據 spec，查找範圍是平倉紀錄的「前後」，但新倉必定發生在平倉之前，
    # 因此我們只查找序號比當前平倉紀錄小的紀錄。
    end_seq = row['序號']

    # 篩選出在序號範圍內的潛在開倉紀錄
    potential_opens = df_records.iloc[start_seq:end_seq]
    
    # 從潛在紀錄中找到符合所有條件的開倉紀錄
    matched_opens = potential_opens[
        (potential_opens['商品名稱'] == row['商品名稱']) & (potential_opens['倉別'] == '新倉') & (potential_opens['成交價'] == row['新倉價'])
    ]

    if not matched_opens.empty:
        # 如果找到多筆，返回時間最接近（即序號最大）的開倉紀錄的成交時間
        return matched_opens.iloc[-1]['成交時間']

    return pd.NaT

def prepare_data(main_file: str, records_file: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    階段一：資料清洗與準備
    """
    print(">> 階段一：資料清洗與準備")
    print("正在載入檔案...")
    try:
        df_main = pd.read_csv(main_file)
        df_records = pd.read_csv(records_file)
    except FileNotFoundError as e:
        print(f"錯誤：找不到檔案 {e.filename}。請確認檔案名稱與路徑是否正確。")
        return None, None

    print("正在進行資料清理與型態轉換...")
    price_cols_main = ['新倉價', '平倉價', '平倉損益淨額']
    for col in price_cols_main:
        if col in df_main.columns:
            df_main[col] = clean_numeric_column(df_main[col])

    price_cols_records = ['成交價', '手續費']
    for col in price_cols_records:
        if col in df_records.columns:
            df_records[col] = clean_numeric_column(df_records[col])

    df_main['成交時間'] = pd.to_datetime(df_main['成交時間'])
    df_records['成交時間'] = pd.to_datetime(df_records['成交時間'])

    df_main['口數'] = pd.to_numeric(df_main['口數'], errors='coerce').fillna(0).astype('int64')
    df_records['成交口數'] = pd.to_numeric(df_records['成交口數'], errors='coerce').fillna(0).astype('int64')

    print("正在為成交紀錄新增 UUID 與序號...")
    df_records = df_records.sort_values(by='成交時間').reset_index(drop=True)
    df_records['序號'] = df_records.index
    df_records['UUID'] = [uuid.uuid4().hex[:16] for _ in range(len(df_records))]

    return df_main, df_records

def merge_and_find(df_main: pd.DataFrame, df_records: pd.DataFrame) -> pd.DataFrame:
    """
    階段二：兩階段合併與新倉時間查找
    """
    print("\n>> 階段二：兩階段合併與新倉時間查找")

    print("步驟 1: 正在比對平倉交易...")
    merged_df = pd.merge(
        df_main,
        df_records,
        left_on=['成交時間', '平倉價', '商品名稱'],
        right_on=['成交時間', '成交價', '商品名稱'],
        how='left'
    )
    merged_df.drop(columns=['成交價', '成交口數', '手續費', '倉別'], inplace=True)

    unmatched_close_trades = merged_df['序號'].isna().sum()
    if unmatched_close_trades > 0:
        print(f"注意：有 {unmatched_close_trades} 筆平倉交易在《成交紀錄》中未找到對應紀錄，將被忽略。")
    merged_df.dropna(subset=['序號'], inplace=True)
    merged_df['序號'] = merged_df['序號'].astype(int)

    print("步驟 2: 正在查找新倉時間 (可能需要一些時間)...")
    merged_df['新倉時間'] = merged_df.progress_apply(
        find_open_time,
        axis=1,
        df_records=df_records,
        search_range=5
    )
    return merged_df

def process_output(merged_df: pd.DataFrame, output_filename: str) -> None:
    """
    階段三：結果輸出與最終型態調整
    """
    print("\n>> 階段三：結果輸出與最終型態調整")

    unmatched_open_trades = merged_df['新倉時間'].isna().sum()
    if unmatched_open_trades > 0:
        print(f"注意：有 {unmatched_open_trades} 筆交易未能成功匹配到新倉時間，將從最終結果中移除。")
    final_df = merged_df.dropna(subset=['新倉時間'])

    output_columns = [
        '成交時間', '新倉時間', '商品名稱', '口數',
        '新倉價', '平倉價', '平倉損益淨額', 'UUID'
    ]
    final_df = final_df[output_columns]

    print(f"正在將結果輸出至 {output_filename}...")
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

    print("\n處理完成！")
    print(f"成功處理並輸出了 {len(final_df)} 筆紀錄。")

def main():
    """
    主執行函數，協調資料處理流程。
    """
    import argparse

    parser = argparse.ArgumentParser(description='合併交易明細與成交紀錄。')
    parser.add_argument(
        '--main-file', 
        default='2021-2025 交易明细 工作表1.csv', 
        help='主要的交易明細檔案路徑 (例如: 2021-2025 交易明细 工作表1.csv)'
    )
    parser.add_argument(
        '--records-file', 
        default='成交紀錄 2021-2025.csv', 
        help='成交紀錄檔案路徑 (例如: 成交紀錄 2021-2025.csv)'
    )
    parser.add_argument(
        '--output-file', 
        default='2021_2025交易與成交合併交易檔.csv', 
        help='合併後的輸出檔案路徑'
    )
    args = parser.parse_args()

    main_file = args.main_file
    records_file = args.records_file
    output_file = args.output_file

    # 階段一
    df_main, df_records = prepare_data(main_file, records_file)
    if df_main is None or df_records is None:
        return

    # 階段二
    merged_data = merge_and_find(df_main, df_records)

    # 階段三
    process_output(merged_data, output_file)

if __name__ == '__main__':
    main()