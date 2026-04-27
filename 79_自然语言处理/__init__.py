"""

自然语言处理相关算法实现。



文件名: __init__.py

"""



# -*- coding: utf-8 -*-

"""

自然语言处理算法包



本包包含自然语言处理的各种基础算法实现。



主要模块：

- word_segmentation: 分词算法（正向/双向最大匹配）

- pos_tagging: 词性标注（Viterbi HMM）

- tf_idf: TF-IDF向量化

- sentiment_analysis: 情感分析（朴素贝叶斯）



使用方法：

    from word_segmentation import ForwardMaximumMatching

    segmenter = ForwardMaximumMatching(dictionary)

    words = segmenter.segment("我爱中国")

"""



# 版本信息

__version__ = "1.0.0"

__all__ = [

    "word_segmentation",

    "pos_tagging",

    "tf_idf",

    "sentiment_analysis",

]



if __name__ == "__main__":

    # 基础功能测试

    # 请在此添加测试代码

    pass

