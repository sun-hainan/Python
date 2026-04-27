# -*- coding: utf-8 -*-

"""

算法实现：差异理论 / text_similarity



本文件实现 text_similarity 相关的算法功能。

"""



import math

from collections import Counter





def tokenize_text(text):

    """

    将文本拆分为单词（词条化）

    

    参数:

        text: 输入文本

    

    返回:

        单词列表

    """

    # 简单分词：转小写，按空格和标点分割

    import re

    tokens = re.findall(r'\b\w+\b', text.lower())

    return tokens





def jaccard_similarity(text_a, text_b):

    """

    计算Jaccard相似度

    

    Jaccard(A, B) = |A ∩ B| / |A ∪ B|

    

    参数:

        text_a: 第一个文本

        text_b: 第二个文本

    

    返回:

        0到1之间的相似度值

    """

    tokens_a = set(tokenize_text(text_a))

    tokens_b = set(tokenize_text(text_b))

    

    intersection = tokens_a & tokens_b

    union = tokens_a | tokens_b

    

    if len(union) == 0:

        return 1.0  # 两个空文本视为相同

    

    return len(intersection) / len(union)





def jaccard_similarity_ngrams(text, n=2):

    """

    基于N-gram的Jaccard相似度

    

    参数:

        text: 输入文本

        n: N-gram的大小

    

    返回:

        N-gram集合

    """

    tokens = tokenize_text(text)

    ngrams = set()

    

    for i in range(len(tokens) - n + 1):

        ngram = tuple(tokens[i:i+n])

        ngrams.add(ngram)

    

    return ngrams





def dice_coefficient(text_a, text_b, n=2):

    """

    计算Dice系数（基于字符级N-gram）

    

    Dice(A, B) = 2 * |A ∩ B| / (|A| + |B|)

    

    参数:

        text_a: 第一个文本

        text_b: 第二个文本

        n: 字符级N-gram大小

    

    返回:

        0到1之间的相似度值

    """

    def get_ngrams(s, n):

        """获取字符级N-gram集合"""

        return set(s[i:i+n] for i in range(len(s) - n + 1))

    

    ngrams_a = get_ngrams(text_a.lower(), n)

    ngrams_b = get_ngrams(text_b.lower(), n)

    

    intersection = ngrams_a & ngrams_b

    

    if len(ngrams_a) + len(ngrams_b) == 0:

        return 1.0

    

    return 2 * len(intersection) / (len(ngrams_a) + len(ngrams_b))





def cosine_similarity(vec_a, vec_b):

    """

    计算两个向量的余弦相似度

    

    Cosine(θ) = (A · B) / (|A| * |B|)

    

    参数:

        vec_a: 向量A（词频Counter）

        vec_b: 向量B（词频Counter）

    

    返回:

        -1到1之间的相似度值

    """

    # 计算点积

    dot_product = sum(vec_a.get(word, 0) * vec_b.get(word, 0) 

                       for word in set(vec_a) | set(vec_b))

    

    # 计算模长

    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))

    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    

    if norm_a * norm_b == 0:

        return 0.0

    

    return dot_product / (norm_a * norm_b)





def text_to_vector(text):

    """

    将文本转换为词频向量

    

    参数:

        text: 输入文本

    

    返回:

        Counter词频对象

    """

    tokens = tokenize_text(text)

    return Counter(tokens)





def cosine_similarity_text(text_a, text_b):

    """

    计算两个文本的余弦相似度

    

    参数:

        text_a: 第一个文本

        text_b: 第二个文本

    

    返回:

        0到1之间的相似度值

    """

    vec_a = text_to_vector(text_a)

    vec_b = text_to_vector(text_b)

    

    return cosine_similarity(vec_a, vec_b)





def overlap_coefficient(text_a, text_b):

    """

    计算重叠系数（Overlap Coefficient）

    

    Overlap(A, B) = |A ∩ B| / min(|A|, |B|)

    

    参数:

        text_a: 第一个文本

        text_b: 第二个文本

    

    返回:

        0到1之间的相似度值

    """

    tokens_a = set(tokenize_text(text_a))

    tokens_b = set(tokenize_text(text_b))

    

    intersection = tokens_a & tokens_b

    min_size = min(len(tokens_a), len(tokens_b))

    

    if min_size == 0:

        return 0.0

    

    return len(intersection) / min_size





def edit_distance_similarity(str_a, str_b):

    """

    基于编辑距离的相似度

    

    Similarity = 1 - (编辑距离 / max_len)

    

    参数:

        str_a: 第一个字符串

        str_b: 第二个字符串

    

    返回:

        0到1之间的相似度值

    """

    max_len = max(len(str_a), len(str_b))

    

    if max_len == 0:

        return 1.0

    

    # 简单的Levenshtein距离计算

    n = len(str_a)

    m = len(str_b)

    

    dp = [[0] * (m + 1) for _ in range(n + 1)]

    

    for i in range(n + 1):

        dp[i][0] = i

    for j in range(m + 1):

        dp[0][j] = j

    

    for i in range(1, n + 1):

        for j in range(1, m + 1):

            if str_a[i-1] == str_b[j-1]:

                dp[i][j] = dp[i-1][j-1]

            else:

                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    

    distance = dp[n][m]

    return 1.0 - (distance / max_len)





def combined_similarity(text_a, text_b, weights=None):

    """

    综合多种相似度计算方法

    

    参数:

        text_a: 第一个文本

        text_b: 第二个文本

        weights: 各方法的权重字典

    

    返回:

        加权相似度

    """

    if weights is None:

        weights = {

            'jaccard': 0.3,

            'cosine': 0.3,

            'dice': 0.2,

            'overlap': 0.2

        }

    

    similarities = {

        'jaccard': jaccard_similarity(text_a, text_b),

        'cosine': cosine_similarity_text(text_a, text_b),

        'dice': dice_coefficient(text_a, text_b),

        'overlap': overlap_coefficient(text_a, text_b)

    }

    

    # 计算加权平均

    result = sum(weights.get(method, 0) * sim 

                 for method, sim in similarities.items())

    

    return result, similarities





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本相似度比较

    print("=" * 50)

    print("测试1: 基本相似度比较")

    print("=" * 50)

    

    pairs = [

        ("The quick brown fox", "The quick brown fox"),  # 相同

        ("The quick brown fox", "The slow red fox"),     # 部分相似

        ("Hello world", "Goodbye world"),                # 完全不同

    ]

    

    for text_a, text_b in pairs:

        print(f"文本A: '{text_a}'")

        print(f"文本B: '{text_b}'")

        print(f"  Jaccard: {jaccard_similarity(text_a, text_b):.4f}")

        print(f"  Cosine: {cosine_similarity_text(text_a, text_b):.4f}")

        print(f"  Dice: {dice_coefficient(text_a, text_b):.4f}")

        print(f"  Overlap: {overlap_coefficient(text_a, text_b):.4f}")

        print()

    

    # 测试用例2：句子相似度

    print("=" * 50)

    print("测试2: 句子相似度检测")

    print("=" * 50)

    

    sentences = [

        "The cat sat on the mat",

        "A cat was sitting on the mat",

        "The dog ran in the park",

        "A cat sat on the mat yesterday"

    ]

    

    n = len(sentences)

    print("相似度矩阵:")

    print("     ", end='')

    for i in range(n):

        print(f" S{i+1}   ", end='')

    print()

    

    for i in range(n):

        print(f"S{i+1}  ", end='')

        for j in range(n):

            sim = jaccard_similarity(sentences[i], sentences[j])

            print(f"{sim:.3f}  ", end='')

        print()

    

    # 测试用例3：N-gram Dice系数

    print("\n" + "=" * 50)

    print("测试3: 字符级N-gram Dice系数")

    print("=" * 50)

    

    for n in [2, 3, 4]:

        sim = dice_coefficient("ABAB", "BABA", n)

        print(f"Dice系数 (n={n}): {sim:.4f}")

    

    # 测试用例4：综合相似度

    print("\n" + "=" * 50)

    print("测试4: 综合相似度分析")

    print("=" * 50)

    

    text_a = "Machine learning is a subset of artificial intelligence"

    text_b = "AI includes machine learning and deep learning techniques"

    

    total, details = combined_similarity(text_a, text_b)

    print(f"文本A: '{text_a}'")

    print(f"文本B: '{text_b}'")

    print(f"\n各方法相似度:")

    for method, sim in details.items():

        print(f"  {method}: {sim:.4f}")

    print(f"\n综合相似度: {total:.4f}")

    

    # 测试用例5：编辑距离相似度

    print("\n" + "=" * 50)

    print("测试5: 编辑距离相似度")

    print("=" * 50)

    

    pairs = [

        ("kitten", "sitting"),

        ("saturday", "sunday"),

        ("same", "same"),

    ]

    

    for str_a, str_b in pairs:

        sim = edit_distance_similarity(str_a, str_b)

        print(f"'{str_a}' vs '{str_b}': {sim:.4f}")

