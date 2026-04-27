# -*- coding: utf-8 -*-

"""

算法实现：信息检索 / query_expansion



本文件实现 query_expansion 相关的算法功能。

"""



from typing import List, Set, Dict





class QueryExpander:

    """查询扩展器"""



    def __init__(self):

        # 简化的同义词词典

        self.synonym_dict = {

            '电脑': {'计算机', '笔记本', 'PC', 'desktop'},

            '程序': {'编程', '代码', 'software'},

            '网络': {'互联网', 'web', 'internet'},

            '数据': {'数据', 'database', '数据'},

            '学习': {'学习', '机器学习', 'ai'},

        }



    def expand(self, query: List[str], method: str = 'synonym') -> List[str]:

        """

        扩展查询



        参数：

            query: 原始查询词列表

            method: 'synonym' 或 'all'



        返回：扩展后的查询词列表

        """

        expanded = set(query)



        for term in query:

            if term in self.synonym_dict:

                expanded.update(self.synonym_dict[term])



        return list(expanded)





class PseudoRelevanceExpander:

    """伪相关反馈查询扩展"""



    def __init__(self, index, searcher):

        self.index = index

        self.searcher = searcher



    def expand(self, query: List[str], top_k: int = 10, num_feedback: int = 5) -> List[str]:

        """

        伪相关反馈扩展



        1. 用原查询检索top-k文档

        2. 取前num_feedback个文档的高频词加入查询

        3. 重新检索

        """

        # 第一次检索

        results = self.searcher.search(query, top_k=top_k)



        # 统计前num_feedback个文档的词频

        term_freq = {}

        for doc_id, _ in results[:num_feedback]:

            for term, tfidf in self.index.doc_vectors.get(doc_id, {}).items():

                term_freq[term] = term_freq.get(term, 0) + tfidf



        # 取高频词加入查询

        expanded = query.copy()

        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)



        for term, _ in sorted_terms[:num_feedback]:

            if term not in query:

                expanded.append(term)



        return expanded





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 查询扩展测试 ===\n")



    expander = QueryExpander()



    queries = [

        ["电脑"],

        ["程序", "代码"],

        ["机器", "学习"],

    ]



    print("同义词扩展：")

    for query in queries:

        expanded = expander.expand(query)

        print(f"  {query} -> {expanded}")



    print("\n说明：")

    print("  - 同义词扩展是最简单的方法")

    print("  - 伪相关反馈(Rocchio)更智能")

    print("  - 实际搜索引擎综合多种方法")

