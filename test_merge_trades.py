import unittest
import pandas as pd
from datetime import datetime

# 從主腳本中匯入我們要測試的函數
from merge_trades import find_open_time

class TestFindOpenTime(unittest.TestCase):

    def setUp(self):
        """
        在每個測試方法執行前，設定好共用的測試資料。
        """
        # 模擬一個《成交紀錄》DataFrame (df_records)
        records_data = {
            '序號': range(10),
            '成交時間': pd.to_datetime([
                '2023-01-01 09:00:00', # 0
                '2023-01-01 09:05:00', # 1 (符合商品A, 價格100)
                '2023-01-01 09:10:00', # 2 (符合商品B, 價格200)
                '2023-01-01 09:15:00', # 3 (商品A, 但價格不同)
                '2023-01-01 09:20:00', # 4 (符合商品A, 價格100, 較接近)
                '2023-01-01 09:25:00', # 5 (平倉倉別)
                '2023-01-01 09:30:00', # 6 (平倉紀錄)
                '2023-01-01 09:35:00', # 7
                '2023-01-01 09:40:00', # 8
                '2023-01-01 09:45:00', # 9
            ]),
            '商品名稱': ['商品A', '商品A', '商品B', '商品A', '商品A', '商品A', '商品A', '商品B', '商品C', '商品A'],
            '倉別': ['新倉', '新倉', '新倉', '新倉', '新倉', '平倉', '平倉', '新倉', '新倉', '新倉'],
            '成交價': [90, 100, 200, 101, 100, 105, 105, 200, 300, 100]
        }
        self.df_records = pd.DataFrame(records_data)

    def test_find_open_time_success(self):
        """測試：成功找到新倉時間。"""
        # 模擬一筆平倉交易，序號為6，新倉價為100
        close_trade_row = pd.Series({
            '序號': 6,
            '商品名稱': '商品A',
            '新倉價': 100
        })
        
        # 預期應找到序號為4的紀錄
        expected_time = pd.to_datetime('2023-01-01 09:20:00')
        result_time = find_open_time(close_trade_row, self.df_records, search_range=5)
        
        self.assertEqual(result_time, expected_time)

    def test_find_open_time_multiple_matches(self):
        """測試：當有多筆符合時，應返回時間最接近（序號最大）的一筆。"""
        # 序號6的平倉交易，向前查找5筆 (1~5)，序號1和4都符合。
        # 應返回序號較大的4。
        close_trade_row = pd.Series({
            '序號': 6,
            '商品名稱': '商品A',
            '新倉價': 100
        })
        
        expected_time = pd.to_datetime('2023-01-01 09:20:00') # 序號4的時間
        result_time = find_open_time(close_trade_row, self.df_records, search_range=5)
        
        self.assertEqual(result_time, expected_time)

    def test_find_open_time_no_match(self):
        """測試：在查找範圍內找不到符合條件的紀錄。"""
        # 查找商品C，但範圍內沒有符合的
        close_trade_row = pd.Series({
            '序號': 6,
            '商品名稱': '商品C',
            '新倉價': 300
        })
        
        result_time = find_open_time(close_trade_row, self.df_records, search_range=5)
        self.assertTrue(pd.isna(result_time))

    def test_find_open_time_outside_range(self):
        """測試：符合的紀錄存在，但超出查找範圍。"""
        # 序號6的平倉交易，但查找範圍只設為1。
        # 符合的紀錄在序號1和4，都超出範圍 (6-1=5)。
        close_trade_row = pd.Series({
            '序號': 6,
            '商品名稱': '商品A',
            '新倉價': 100
        })
        
        result_time = find_open_time(close_trade_row, self.df_records, search_range=1)
        self.assertTrue(pd.isna(result_time))

    def test_find_open_time_edge_case_start(self):
        """測試：當平倉紀錄在檔案開頭時的邊界情況。"""
        # 模擬一筆序號為2的平倉交易
        close_trade_row = pd.Series({
            '序號': 2,
            '商品名稱': '商品A',
            '新倉價': 100
        })
        
        # 預期找到序號為1的紀錄
        expected_time = pd.to_datetime('2021-01-01 09:05:00')
        result_time = find_open_time(close_trade_row, self.df_records, search_range=5)
        self.assertEqual(result_time, pd.to_datetime('2023-01-01 09:05:00'))

if __name__ == '__main__':
    unittest.main()