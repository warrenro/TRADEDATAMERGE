# Gemini Code Assist 互動指令全紀錄

本文件記錄了與 Gemini Code Assist 互動以建立和完善 `TRADEDATAMERGE` 專案的主要提示詞與 Git 指令。

---

## 1. 初始程式碼生成

**目標：** 根據 `spec.md` 的需求，產生初版的 Python 程式碼。

#### 提示詞
```
閱讀spec.md產生對應的程式
```

#### Gemini 回應摘要
- 產生了 `merge_trades.py` 腳本。
- 更新了 `Version.md` 文件。
- 提供了初次的 Git 推送指令。

---

## 2. 程式碼邏輯精煉與文件更新

**目標：** 根據 `spec.md` 對於「新倉時間查找」邏輯的精確描述（前後5筆），更新程式碼。

#### 提示詞
```
閱讀spec.md產生對應的程式
```

#### Gemini 回應摘要
- 修改了 `merge_trades.py` 中的 `find_open_time` 函數，將查找範圍調整為更精確的「前後」查找。
- 優化了程式碼結構，將其拆分為多個函數。
- 更新了 `Version.md` 以反映新的查找邏輯。
- 提供了 Git 推送指令。

#### 主要指令
```bash
# 提交變更
git commit -m "refactor: Align open-time search logic with spec and improve code structure"

# 推送至遠端
git push origin main
```

---

## 3. 加入單元測試

**目標：** 為核心的 `find_open_time` 函數建立單元測試，以確保其正確性。

#### 提示詞
```
如何為這個 Python 腳本加入單元測試，以確保 `find_open_time` 函數的正確性？
```

#### Gemini 回應摘要
- 修正了 `find_open_time` 函數中的一個小錯誤。
- 建立了 `test_merge_trades.py` 檔案，其中包含多個測試案例。

#### 主要指令
```bash
# 執行單元測試
python -m unittest test_merge_trades.py
```

---

## 4. 整合 GitHub Actions (CI/CD)

**目標：** 設定自動化工作流程，在每次推送程式碼時自動執行單元測試。

#### 提示詞
```
如何將這個 unittest 整合到 GitHub Actions 中，讓每次推送程式碼時都能自動執行測試？
```

#### Gemini 回應摘要
- 建立了 `requirements.txt` 檔案來管理專案依賴。
- 建立了 `.github/workflows/python-tests.yml` 工作流程設定檔。

---

## 5. Git 推送與問題排查

**目標：** 將所有新檔案推送到 GitHub，並解決過程中遇到的問題。

#### 綜合提示詞
```
幫我推送一版到GITHUB上
現在使用的GIT儲存庫是哪一個
如何查看這個 Git 儲存庫的所有提交歷史？
(貼上 git push 錯誤訊息) 如何解決
重新給我上版的指令
我在git action上看不到相關測試
```

#### 主要指令
```bash
# 重新命名本地分支以匹配遠端 (解決 master/main 名稱不一致問題)
git branch -m master main

# 將所有變更加入暫存區
git add .

# 提交所有變更
git commit -m "feat: Add unit tests and CI workflow"

# 推送到 GitHub
git push origin main
```