"""
差异理论相关算法实现。

文件名: __init__.py
"""

# -*- coding: utf-8 -*-
"""
差异理论算法包

本包包含用于文本差异比较和合并的各种算法实现。

主要模块：
- myers_diff: Myers O(ND) diff算法
- lcs_algorithm: 最长公共子序列算法
- patch_generation: 统一diff格式补丁生成
- semantic_diff: 语义级代码差异分析
- tree_diff: AST树形差异算法
- three_way_merge: 三路合并算法
- conflict_detection: 冲突检测与解决
- word_level_diff: 单词级diff
- line_diff: 行级diff
- levenshtein_distance: 编辑距离
- longest_common_substring: 最长公共子串
- text_similarity: 文本相似度计算
- rolling_hash: 滚动哈希算法

使用方法：
    from myers_diff import myers_diff, format_diff
    edits = myers_diff("ABCABBA", "CBABAC")
    print(format_diff(edits))
"""

# 版本信息
__version__ = "1.0.0"
__all__ = [
    "myers_diff",
    "lcs_algorithm", 
    "patch_generation",
    "semantic_diff",
    "tree_diff",
    "three_way_merge",
    "conflict_detection",
    "word_level_diff",
    "line_diff",
    "levenshtein_distance",
    "longest_common_substring",
    "text_similarity",
    "rolling_hash",
]

if __name__ == "__main__":
    # 基础功能测试
    # 请在此添加测试代码
    pass
