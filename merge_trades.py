import pandas as pd
import numpy as np
import uuid
from tqdm import tqdm

def clean_numeric(val):
    """清理數值欄位，移除千位數逗號、引號和小數點"""
    if isinstance(val, str):
        # 移除千位數逗號和引號
        val = val.replace(',', '').replace('"', '')
        # 如果有小數點，只取整數部分
        if '.' in val:
            val = val.split('.')[0]
        return int(val)
    elif isinstance(val, float):
        # 如果是浮點數，轉為整數
        return int(val)
    return val

def generate_uuid():
    """產生16碼UUID"""
    return str(uuid.uuid4()).replace('-', '')[:16]

def prepare_data():
    """階段一：資料清洗與準備"""
    print("開始資料準備階段...")
    
    # 載入檔案
    df_main = pd.read_csv('2021-2025 交易明细 工作表1.csv')
    df_records = pd.read_csv('成交紀錄 2021-2025.csv')
    
    # 清理數值欄位
    numeric_columns = ['新倉價', '平倉價', '平倉損益淨額', '成交價', '手續費', '交易稅']
    for col in numeric_columns:
        if col in df_records.columns:
            df_records[col] = df_records[col].apply(clean_numeric)
        if col in df_main.columns:
            df_main[col] = df_main[col].apply(clean_numeric)
    
    # 數值型態轉換
    integer_columns = ['口數', '成交口數']
    for col in integer_columns:
        if col in df_records.columns:
            df_records[col] = df_records[col].astype('int64')
        if col in df_main.columns:
            df_main[col] = df_main[col].astype('int64')
    
    # 時間轉換
    df_records['成交時間'] = pd.to_datetime(df_records['成交時間'])
    df_main['成交時間'] = pd.to_datetime(df_main['成交時間'])
    
    # 新增 UUID 欄位
    df_records['UUID'] = [generate_uuid() for _ in range(len(df_records))]
    
    # 根據成交時間排序並新增序號
    df_records = df_records.sort_values('成交時間').reset_index(drop=True)
    df_records['序號'] = range(1, len(df_records) + 1)
    
    return df_main, df_records

def find_opening_time(row, df_records):
    """尋找新倉時間"""
    # 取得目前記錄的序號
    current_seq = df_records[
        (df_records['商品名稱'] == row['商品名稱']) &
        (df_records['成交時間'] == row['成交時間'])
    ]['序號'].iloc[0]
    
    # 在前後5筆記錄中尋找符合條件的新倉記錄
    mask = (
        (df_records['倉別'] == '新倉') &
        (df_records['商品名稱'] == row['商品名稱']) &
        (df_records['成交價'] == row['新倉價']) &
        (df_records['序號'].between(current_seq - 5, current_seq + 5))
    )
    
    matches = df_records[mask].sort_values('成交時間')
    return matches['成交時間'].iloc[0] if not matches.empty else pd.NaT

def merge_data(df_main, df_records):
    """階段二：兩階段合併與新倉時間查找"""
    print("開始執行合併階段...")
    
    # 步驟1：比對平倉交易
    merged1 = pd.merge(
        df_main,
        df_records[df_records['倉別'] == '平倉'],
        left_on=['成交時間', '平倉價', '商品名稱'],
        right_on=['成交時間', '成交價', '商品名稱'],
        how='inner'
    )
    
    # 步驟2：比對新倉交易
    print("處理新倉時間配對...")
    tqdm.pandas()
    merged1['新倉時間'] = merged1.progress_apply(
        lambda row: find_opening_time(row, df_records), axis=1
    )
    
    return merged1

def process_output(merged_data):
    """階段三：結果輸出與最終型態調整"""
    print("處理輸出資料...")
    
    # 選擇最終欄位
    final_columns = [
        '成交時間',
        '新倉時間', 
        '商品名稱',
        '口數',
        '新倉價',
        '平倉價',
        '平倉損益淨額'
    ]
    
    result = merged_data[final_columns].copy()
    
    # 篩選有新倉時間的記錄
    result = result.dropna(subset=['新倉時間'])
    
    # 確保所有數值欄位為整數型態
    numeric_columns = ['新倉價', '平倉價', '平倉損益淨額', '口數']
    for col in numeric_columns:
        result[col] = result[col].astype('int64')
    
    return result

def main():
    print("開始處理資料...")
    
    # 執行階段一：資料準備
    df_main, df_records = prepare_data()
    
    # 執行階段二：資料合併
    merged_data = merge_data(df_main, df_records)
    
    # 執行階段三：結果處理
    final_result = process_output(merged_data)
    
    # 輸出結果
    output_file = '合併交易紀錄.csv'
    final_result.to_csv(output_file, index=False)
    print(f"處理完成，輸出檔案：{output_file}")
    print(f"共計 {len(final_result)} 筆配對成功的交易紀錄")

if __name__ == "__main__":
    main()