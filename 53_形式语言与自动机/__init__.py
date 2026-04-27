# -*- coding: utf-8 -*-
"""
形式语言与自动机算法包

本包包含形式语言与自动机理论的各种算法实现。

主要模块：
- nfa_to_dfa: NFA到DFA转换（子集构造算法）
- regex_to_nfa: 正则表达式到NFA转换（Thompson构造）
- pumping_lemma: 泵引理验证器
- cyk_parser: CYK上下文无关文法分析算法
- ll1_parser: LL(1)语法分析器
- turing_machine: 图灵机模拟器

使用方法：
    from nfa_to_dfa import NFA, nfa_to_dfa
    dfa = nfa_to_dfa(nfa)
"""

# 版本信息
__version__ = "1.0.0"
__all__ = [
    "nfa_to_dfa",
    "regex_to_nfa",
    "pumping_lemma",
    "cyk_parser",
    "ll1_parser",
    "turing_machine",
]

if __name__ == "__main__":
    # 示例测试
    pass
