# -*- coding: utf-8 -*-

"""

算法实现：信息检索 / vector_space_model



本文件实现 vector_space_model 相关的算法功能。

"""



import math

from typing import List, Dict, Tuple





class VectorSpaceModel:

    """向量空间模型"""



    def __init__(self):

        self.doc_vectors = {}  # doc_id -> {term: tfidf}

        self.vocab = set()

        self.idf = {}



    def index(self, doc_id: int, tokens: List[str]):

        """索引文档"""

        # 计算TF

        tf = {}

        for term in tokens:

            tf[term] = tf.get(term, 0) + 1



        # 计算TF-IDF

        tfidf = {}

        for term, count in tf.items():

            tf_val = count / len(tokens) if tokens else 0

            idf_val = self.idf.get(term, 0)

            tfidf[term] = tf_val * idf_val



        self.doc_vectors[doc_id] = tfidf

        self.vocab.update(tokens)



    def compute_idf(self, all_doc_tokens: List[List[str]]):

        """计算IDF"""

        N = len(all_doc_tokens)

        df = {}



        for tokens in all_doc_tokens:

            for term in set(tokens):

                df[term] = df.get(term, 0) + 1



        for term, doc_freq in df.items():

            self.idf[term] = math.log(N / doc_freq)



    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:

        """计算余弦相似度"""

        # 点积

        dot_product = 0.0

        for term in vec1:

            if term in vec2:

                dot_product += vec1[term] * vec2[term]



        # 模长

        norm1 = math.sqrt(sum(v*v for v in vec1.values()))

        norm2 = math.sqrt(sum(v*v for v in vec2.values()))



        if norm1 == 0 or norm2 == 0:

            return 0.0



        return dot_product / (norm1 * norm2)



    def search(self, query_tokens: List[str], top_k: int = 5) -> List[Tuple[int, float]]:

        """搜索最相似的文档"""

        # 构建查询向量

        query_tf = {}

        for term in query_tokens:

            query_tf[term] = query_tf.get(term, 0) + 1



        query_vec = {}

        for term, tf in query_tf.items():

            tf_val = tf / len(query_tokens) if query_tokens else 0

            idf_val = self.idf.get(term, 0)

            query_vec[term] = tf_val * idf_val



        # 计算与所有文档的相似度

        scores = []

        for doc_id, doc_vec in self.doc_vectors.items():

            sim = self.cosine_similarity(query_vec, doc_vec)

            scores.append((doc_id, sim))



        # 排序

        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 向量空间模型测试 ===\n")



    docs = {

        1: ["python", "is", "great", "for", "programming"],

        2: ["java", "is", "popular", "in", "enterprise"],

        3: ["python", "and", "java", "are", "both", "oop"],

        4: ["machine", "learning", "uses", "python"],

    }



    # 构建索引

    vsm = VectorSpaceModel()

    all_tokens = [list(d.values())[0] if d else [] for d in []]  # 简化



    doc_token_lists = [list(d.values())[0] if d else [] for d in []]

    doc_token_lists = [list(d.values())[0] if isinstance(d, dict) else [] for d in []]



    # 重新组织

    doc_tokens = {1: ["python", "is", "great", "for", "programming"],

                  2: ["java", "is", "popular", "in", "enterprise"],

                  3: ["python", "and", "java", "are", "both", "oop"],

                  4: ["machine", "learning", "uses", "python"]}



    all_tokens_list = list(doc_tokens.values())

    vsm.compute_idf(all_tokens_list)



    for doc_id, tokens in doc_tokens.items():

        vsm.index(doc_id, tokens)



    # 搜索

    query = ["python", "programming"]

    results = vsm.search(query)



    print(f"查询: {query}")

    print(f"结果:")

    for doc_id, score in results:

        print(f"  文档{doc_id}: {score:.4f} ({' '.join(doc_tokens[doc_id])})")



    print("\n说明：")

    print("  - VSM是经典的信息检索模型")

    print("  - TF-IDF + 余弦相似度是标准配置")

    print("  - 现代系统更多用词向量（Word2Vec/BERT）")

