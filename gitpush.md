# 1. 初始化 Git 倉庫 (如果還沒做的話)
git init

# 2. 將您遠端倉庫的 URL 加入 (請替換成您自己的 URL)
# 例如 GitHub, GitLab, Bitbucket
git remote add origin https://github.com/warrenro/TRADEDATAMERGE.git

# 3. 將所有 "非忽略" 的檔案加入到暫存區
git add .

# 4. 提交您的變更，並附上有意義的提交訊息
git commit -m "Initial commit: Add trade data merging script and tests"

# 5. 將您的提交推送到遠端倉庫
# (-u 參數會設定本地 master/main 分支追蹤遠端 origin/master/main 分支)
git push -u origin main
