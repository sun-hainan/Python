# -*- coding: utf-8 -*-

"""

算法实现：安全多方计算 / private_search



本文件实现 private_search 相关的算法功能。

"""



import random

import hashlib

from typing import List, Tuple





class PrivacyPreservingSearch:

    """隐私保护搜索"""



    def __init__(self, security_bits: int = 256):

        """

        参数：

            security_bits: 安全参数

        """

        self.security = security_bits



    def build_index(self, documents: List[str], keywords: List[str]) -> dict:

        """

        构建安全索引



        参数：

            documents: 文档列表

            keywords: 关键词列表



        返回：加密索引

        """

        # 关键词到文档的映射

        index = {}



        for kw in keywords:

            # 生成关键词的伪随机标签

            kw_label = hashlib.sha256(kw.encode()).hexdigest()[:16]



            # 找到包含此关键词的文档

            doc_ids = []

            for doc_id, doc in enumerate(documents):

                if kw.lower() in doc.lower():

                    doc_ids.append(doc_id)



            index[kw_label] = doc_ids



        return index



    def trapdoor(self, keyword: str) -> str:

        """

        生成搜索陷门



        参数：

            keyword: 要搜索的关键词



        返回：陷门

        """

        # 陷门 = 关键词的哈希

        return hashlib.sha256(keyword.encode()).hexdigest()[:16]



    def search(self, trapdoor: str, index: dict) -> List[int]:

        """

        搜索



        返回：匹配的文档ID

        """

        # 简化：直接查索引

        return index.get(trapdoor, [])



    def searchable_encryption(self, keyword: str, doc_id: int) -> str:

        """

        可搜索加密



        参数：

            keyword: 关键词

            doc_id: 文档ID



        返回：加密标签

        """

        # 标签 = hash(keyword || doc_id)

        label = hashlib.sha256(f"{keyword}||{doc_id}".encode()).hexdigest()

        return label





def searchable_encryption_applications():

    """可搜索加密应用"""

    print("=== 可搜索加密应用 ===")

    print()

    print("1. 云存储搜索")

    print("   - 在加密文件中搜索")

    print("   - 服务器不知道内容")

    print()

    print("2. 医疗记录")

    print("   - 搜索患者历史")

    print("   - 保护隐私")

    print()

    print("3. 邮件搜索")

    print("   - 加密邮件服务器搜索")

    print("   - 不泄露关键词")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 隐私保护搜索测试 ===\n")



    # 文档集合

    documents = [

        "The quick brown fox jumps over the lazy dog",

        "A man a plan a canal Panama",

        "Openclaw is a great AI assistant",

        "Python is a popular programming language",

        "Machine learning is a subfield of AI"

    ]



    keywords = ["python", "ai", "man", "quick"]



    search = PrivacyPreservingSearch()



    # 构建索引

    index = search.build_index(documents, keywords)



    print(f"文档数: {len(documents)}")

    print(f"关键词: {keywords}")

    print()



    # 搜索

    for kw in keywords:

        trapdoor = search.trapdoor(kw)

        results = search.search(trapdoor, index)



        print(f"搜索 '{kw}':")

        for doc_id in results:

            print(f"  文档 {doc_id}: {documents[doc_id][:50]}...")

        print()



    print()

    searchable_encryption_applications()



    print()

    print("说明：")

    print("  - 可搜索加密保护云数据隐私")

    print("  - 用户可以搜索但服务器不知道关键词")

    print("  - 是云计算安全的重要技术")

