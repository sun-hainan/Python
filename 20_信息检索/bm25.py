# -*- coding: utf-8 -*-

"""

算法实现：信息检索 / bm25



本文件实现 bm25 相关的算法功能。

"""



import math

from typing import List, Dict, Tuple





def calc_idf(df: int, N: int) -> float:

    """

    计算IDF（逆文档频率）



    IDF = log((N - df + 0.5) / (df + 0.5))

    """

    return math.log((N - df + 0.5) / (df + 0.5))





def bm25_score(tf: int, doc_len: int, df: int, N: int,

               k1: float = 1.2, b: float = 0.75) -> float:

    """

    计算单个词的BM25得分



    参数：

        tf: 词在文档中的出现次数

        doc_len: 文档长度

        df: 包含该词的文档数

        N: 总文档数

        k1: 词频饱和参数

        b: 长度归一化参数

    """

    idf = calc_idf(df, N)



    # 分子部分

    numerator = tf * (k1 + 1)

    # 分母部分

    denominator = tf + k1 * (1 - b + b * doc_len / 100)  # avgdl简化取100



    return idf * numerator / denominator





class BM25Searcher:

    """BM25搜索引擎"""



    def __init__(self, k1: float = 1.2, b: float = 0.75):

        self.k1 = k1

        self.b = b

        self.documents = {}

        self.term_doc_freq = {}  # term -> df

        self.N = 0

        self.avgdl = 0



    def index(self, doc_id: int, tokens: List[str]):

        """索引文档"""

        self.documents[doc_id] = tokens



        # 统计文档频率

        for term in set(tokens):

            if term not in self.term_doc_freq:

                self.term_doc_freq[term] = 0

            self.term_doc_freq[term] += 1



        self.N = len(self.documents)

        self.avgdl = sum(len(t) for t in self.documents.values()) / self.N if self.N > 0 else 0



    def search(self, query: List[str], top_k: int = 10) -> List[Tuple[int, float]]:

        """

        搜索查询



        返回：[(doc_id, score), ...] 按得分降序

        """

        scores = {}



        for doc_id, tokens in self.documents.items():

            score = 0.0

            doc_len = len(tokens)



            for term in query:

                tf = tokens.count(term)

                if tf > 0:

                    df = self.term_doc_freq.get(term, 0)

                    term_score = bm25_score(tf, doc_len, df, self.N, self.k1, self.b)

                    score += term_score



            if score > 0:

                scores[doc_id] = score



        # 排序

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_results[:top_k]





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== BM25测试 ===\n")



    docs = {

        1: ["python", "is", "a", "great", "programming", "language"],

        2: ["java", "is", "also", "popular", "for", "enterprise"],

        3: ["python", "and", "java", "both", "support", "oop"],

        4: ["machine", "learning", "uses", "python", "extensively"],

        5: ["deep", "learning", "is", "part", "of", "ai"],

    }



    # 构建索引

    searcher = BM25Searcher()

    for doc_id, tokens in docs.items():

        searcher.index(doc_id, tokens)



    print("文档:")

    for doc_id, tokens in docs.items():

        print(f"  {doc_id}: {' '.join(tokens)}")



    print()



    # 搜索

    queries = [

        ["python"],

        ["python", "learning"],

        ["enterprise", "java"],

    ]



    for query in queries:

        results = searcher.search(query)

        print(f"查询 {query}:")

        for doc_id, score in results:

            print(f"  文档{doc_id}: {score:.4f}")

        print()



    print("说明：")

    print("  - BM25是TF-IDF的改进版")

    print("  - 解决了词频饱和和文档长度偏差问题")

    print("  - Elasticsearch、Solr等使用BM25作为默认算法")

