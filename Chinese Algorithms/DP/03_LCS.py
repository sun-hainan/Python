"""
LCS - 最长公共子序列
==========================================

【问题定义】
找出两个序列中最长的公共子序列。
子序列可以不连续，但相对顺序必须保持。

【时间复杂度】O(m * n)
【空间复杂度】O(m * n)

【应用场景】
- DNA序列比对（生物信息学）
- diff文件比较（Git版本控制）
- 论文查重/相似度检测
- 字符串相似度计算

【何时使用】
- 两个序列的相似度分析
- 版本控制diff显示
- 生物信息学DNA分析
- 抄袭检测

【实际案例】
# Git diff - 比较两个版本的代码变化
old_code = "function hello() { return 1; }"
new_code = "function hello() { return 2; }"
lcs(old_code, new_code)  # 找出共同部分，高亮显示差异

# 论文查重
paper1_text = "机器学习是人工智能的重要分支"
paper2_text = "机器学习属于人工智能的范畴"
lcs(paper1_text, paper2_text)  # 计算相似度

# 微信聊天记录相似度分析
msg1 = "今天天气真好"
msg2 = "今天天气不错"
lcs(msg1, msg2)  # 测量两条消息的相似程度
"""

def lcs(x, y):
    """
    最长公共子序列
    
    Args:
        x: 第一个序列
        y: 第二个序列
        
    Returns:
        LCS长度
    """
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]
