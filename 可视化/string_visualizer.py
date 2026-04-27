# -*- coding: utf-8 -*-
"""
算法实现：可视化 / string_visualizer

本文件实现 string_visualizer 相关的算法功能。
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def compute_prefix(pattern):
    """
    计算前缀函数（失败函数）

    prefix[i] = pattern[0:i+1] 的最长真前缀也是后缀的长度

    算法：递推计算
        - prefix[0] = 0
        - 对于 i>0，找最长的 k 使得 pattern[0:k] = pattern[i-k+1:i+1]
    """
    m = len(pattern)
    prefix = [0] * m
    j = 0  # 当前匹配的前缀长度
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = prefix[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        prefix[i] = j
    return prefix


def kmp_search(text, pattern):
    """
    KMP 字符串匹配

    返回：所有匹配位置的列表
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return []

    prefix = compute_prefix(pattern)
    matches = []
    j = 0  # 在模式串中的位置

    for i in range(n):
        while j > 0 and text[i] != pattern[j]:
            j = prefix[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            matches.append(i - m + 1)
            j = prefix[j - 1]

    return matches


def visualize_kmp(text, pattern):
    """
    可视化 KMP 算法过程

    显示：
    - 文本串和模式串的对齐
    - 前缀函数表
    - 当前匹配/不匹配位置
    - 已找到的匹配位置
    """
    prefix = compute_prefix(pattern)
    matches = kmp_search(text, pattern)

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle('KMP 字符串匹配算法可视化', fontsize=16)

    # ===== 图1：前缀函数表 =====
    ax1 = axes[0]
    ax1.set_xlim(-0.5, len(pattern) - 0.5)
    ax1.set_ylim(-0.5, 2.5)

    # 绘制字符
    for i, c in enumerate(pattern):
        color = 'lightblue' if prefix[i] > 0 else 'white'
        rect = mpatches.FancyBboxPatch((i - 0.4, 0.4), 0.8, 0.8,
                                         boxstyle="round,pad=0.05",
                                         facecolor=color, edgecolor='black')
        ax1.add_patch(rect)
        ax1.text(i, 0.8, c, ha='center', va='center', fontsize=14, fontweight='bold')

    # 绘制 prefix 值
    for i, val in enumerate(prefix):
        ax1.text(i, -0.2, str(val), ha='center', va='center', fontsize=12,
                 color='red' if val > 0 else 'gray')

    ax1.text(len(pattern) // 2, -0.7, '前缀函数 (prefix)', ha='center', fontsize=12)
    ax1.axis('off')
    ax1.set_title('前缀函数表：prefix[i] = pattern[0:i+1] 的最长真前后缀长度', fontsize=11)

    # ===== 图2：字符串匹配过程 =====
    ax2 = axes[1]
    ax2.set_xlim(-0.5, max(len(text), len(pattern) * 3) - 0.5)
    ax2.set_ylim(-0.5, 2.5)

    # 文本串
    for i, c in enumerate(text[:min(20, len(text))]):
        color = 'yellow' if i in matches else 'lightyellow'
        rect = mpatches.FancyBboxPatch((i * 0.5 - 0.2, 1.5), 0.4, 0.6,
                                         boxstyle="round,pad=0.02",
                                         facecolor=color, edgecolor='black')
        ax2.add_patch(rect)
        ax2.text(i * 0.5, 1.8, c, ha='center', va='center', fontsize=10)

    # 模式串（在文本下方）
    j_pos = len(pattern) - 1 if not matches else matches[-1]
    for i, c in enumerate(pattern):
        x_pos = j_pos * 0.5 + i * 0.5
        color = 'lightgreen' if i == j_pos else 'lightcoral'
        rect = mpatches.FancyBboxPatch((x_pos - 0.2, 0.3), 0.4, 0.6,
                                         boxstyle="round,pad=0.02",
                                         facecolor=color, edgecolor='black')
        ax2.add_patch(rect)
        ax2.text(x_pos, 0.6, c, ha='center', va='center', fontsize=10)

    # 标注
    ax2.text(0, 0, f'文本: {text[:min(20, len(text))]}...', fontsize=10)
    ax2.text(0, 2.3, f'模式: {pattern}', fontsize=10, color='red')
    ax2.text(0, 2.0, f'前缀函数: {prefix}', fontsize=10, color='blue')
    ax2.text(0, -0.2, f'已找到匹配: {matches}', fontsize=10, color='green')
    ax2.axis('off')
    ax2.set_title('字符串匹配过程（匹配位置高亮）', fontsize=11)

    # ===== 图3：匹配结果 =====
    ax3 = axes[2]
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)

    result_text = f"KMP 搜索结果：\n\n"
    result_text += f"文本: {text}\n"
    result_text += f"模式: {pattern}\n\n"
    result_text += f"前缀函数: {prefix}\n\n"
    if matches:
        result_text += f"找到 {len(matches)} 个匹配，位置: {matches}\n"
        for pos in matches:
            matched = text[pos:pos+len(pattern)]
            result_text += f"  位置 {pos}: \"{matched}\"\n"
    else:
        result_text += "未找到匹配"

    ax3.text(0.5, 8, result_text, fontsize=12, family='monospace',
             verticalalignment='top')
    ax3.axis('off')
    ax3.set_title('搜索结果', fontsize=11)

    plt.tight_layout()
    plt.savefig('kmp_visualization.png', dpi=150, bbox_inches='tight')
    print("已保存图片: kmp_visualization.png")
    plt.show()


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    # 测试用例1：基本匹配
    print("=== KMP 字符串匹配测试 ===\n")

    text1 = "ABABDABACDABABCABAB"
    pattern1 = "ABAB"
    print(f"文本: {text1}")
    print(f"模式: {pattern1}")
    print(f"前缀函数: {compute_prefix(pattern1)}")
    matches1 = kmp_search(text1, pattern1)
    print(f"匹配位置: {matches1}\n")

    # 测试用例2：多次匹配
    text2 = "AABAACAADAABAABA"
    pattern2 = "AABA"
    print(f"文本: {text2}")
    print(f"模式: {pattern2}")
    print(f"前缀函数: {compute_prefix(pattern2)}")
    matches2 = kmp_search(text2, pattern2)
    print(f"匹配位置: {matches2}\n")

    # 测试用例3：无匹配
    text3 = "ABCDEFGH"
    pattern3 = "XYZ"
    print(f"文本: {text3}")
    print(f"模式: {pattern3}")
    print(f"前缀函数: {compute_prefix(pattern3)}")
    matches3 = kmp_search(text3, pattern3)
    print(f"匹配位置: {matches3}\n")

    # 可视化
    print("正在生成可视化...")
    visualize_kmp(text1, pattern1)
