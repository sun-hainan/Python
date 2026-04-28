"""
联邦搜索模块 - 多数据源聚合

本模块实现联邦搜索系统，从多个异构数据源并行检索并聚合结果。
支持不同类型的数据源：网络、数据库、API、本地文件等。

核心方法：
1. 多源并行检索：异步并发查询多个数据源
2. 结果归一化：将不同格式的结果转换为统一表示
3. 分数融合：合并多源得分
4. 去重和排序：合并重复结果并排序输出
"""

import asyncio
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import heapq
import time


@dataclass
class SearchResult:
    """统一搜索结果"""
    result_id: str
    title: str
    snippet: str
    url: str = ""
    source: str = ""  # 数据源标识
    score: float = 0.0
    rank: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class SearchQuery:
    """搜索查询"""
    query_text: str
    num_results: int = 10
    filters: Dict = field(default_factory=dict)
    language: str = "en"
    timestamp: float = field(default_factory=time.time)


class SearchSource:
    """搜索数据源基类"""

    def __init__(self, source_name: str):
        self.source_name = source_name

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """执行搜索（子类实现）"""
        raise NotImplementedError

    def normalize_score(self, original_score: float) -> float:
        """归一化原始分数到0-1"""
        return min(1.0, max(0.0, original_score))

    def parse_response(self, raw_response: Any) -> List[SearchResult]:
        """解析数据源响应（子类实现）"""
        raise NotImplementedError


class WebSearchSource(SearchSource):
    """网络搜索源（模拟）"""

    def __init__(self):
        super().__init__("web")

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """模拟网络搜索"""
        # 模拟延迟
        await asyncio.sleep(0.1)

        results = []
        for i in range(min(query.num_results, 5)):
            results.append(SearchResult(
                result_id=f"web_{query.query_text[:10]}_{i}",
                title=f"Web Result {i+1} for '{query.query_text}'",
                snippet=f"This is a web search result snippet about {query.query_text}...",
                url=f"https://example.com/result{i}",
                source="web",
                score=1.0 / (i + 1),
                metadata={"type": "web_page"}
            ))

        return results


class DatabaseSearchSource(SearchSource):
    """数据库搜索源（模拟）"""

    def __init__(self):
        super().__init__("database")

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """模拟数据库搜索"""
        await asyncio.sleep(0.05)

        results = []
        for i in range(min(query.num_results, 3)):
            results.append(SearchResult(
                result_id=f"db_{query.query_text[:10]}_{i}",
                title=f"DB Record {i+1}: {query.query_text}",
                snippet=f"Database record content related to {query.query_text}...",
                source="database",
                score=0.8 / (i + 1),
                metadata={"db": "main_db", "table": "documents"}
            ))

        return results


class APISearchSource(SearchSource):
    """API搜索源（模拟）"""

    def __init__(self, api_name: str):
        super().__init__(f"api_{api_name}")
        self.api_name = api_name

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """模拟API搜索"""
        await asyncio.sleep(0.08)

        results = []
        for i in range(min(query.num_results, 4)):
            results.append(SearchResult(
                result_id=f"api_{self.api_name}_{i}",
                title=f"API Result from {self.api_name}",
                snippet=f"API response for {query.query_text}...",
                source=f"api_{self.api_name}",
                score=0.9 / (i + 1),
                metadata={"api": self.api_name, "version": "v1"}
            ))

        return results


class ScoreFusion:
    """多源分数融合"""

    def __init__(self, method: str = "reciprocal_rank"):
        self.method = method

    def fuse(self, results_by_source: Dict[str, List[SearchResult]],
             source_weights: Optional[Dict[str, float]] = None) -> List[SearchResult]:
        """
        融合多源搜索结果
        :param results_by_source: {source_name: [results]}
        :param source_weights: 各数据源权重
        :return: 融合后的排序结果
        """
        if self.method == "reciprocal_rank":
            return self._reciprocal_rank_fusion(results_by_source, source_weights)
        elif self.method == "score_average":
            return self._score_average_fusion(results_by_source, source_weights)
        elif self.method == "borda_count":
            return self._borda_count_fusion(results_by_source)
        else:
            return self._reciprocal_rank_fusion(results_by_source, source_weights)

    def _reciprocal_rank_fusion(self, results_by_source: Dict[str, List[SearchResult]],
                               source_weights: Optional[Dict[str, float]] = None) -> List[SearchResult]:
        """倒数排名融合 (RRF)"""
        rr_scores = defaultdict(float)

        for source, results in results_by_source.items():
            weight = source_weights.get(source, 1.0) if source_weights else 1.0
            k = 60  # RRF常数

            for rank, result in enumerate(results, 1):
                # 使用result_id作为唯一标识
                rr_scores[result.result_id] += weight / (k + rank)

        # 排序
        fused_results = []
        for source, results in results_by_source.items():
            for result in results:
                result.score = rr_scores[result.result_id]
                if result not in fused_results:
                    fused_results.append(result)

        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results

    def _score_average_fusion(self, results_by_source: Dict[str, List[SearchResult]],
                             source_weights: Optional[Dict[str, float]] = None) -> List[SearchResult]:
        """分数平均融合"""
        combined_scores = defaultdict(list)

        for source, results in results_by_source.items():
            weight = source_weights.get(source, 1.0) if source_weights else 1.0

            for result in results:
                # 归一化分数
                normalized = result.score * weight
                combined_scores[result.result_id].append((result, normalized))

        # 计算平均分数
        averaged_results = []
        seen = set()

        for result_id, items in combined_scores.items():
            result, _ = items[0]
            avg_score = np.mean([score for _, score in items])
            result.score = avg_score
            if result_id not in seen:
                averaged_results.append(result)
                seen.add(result_id)

        averaged_results.sort(key=lambda x: x.score, reverse=True)
        return averaged_results

    def _borda_count_fusion(self, results_by_source: Dict[str, List[SearchResult]]) -> List[SearchResult]:
        """Borda Count融合"""
        borda_scores = defaultdict(float)

        for source, results in results_by_source.items():
            n = len(results)
            for rank, result in enumerate(results):
                # Borda score: n - rank - 1
                borda_scores[result.result_id] += n - rank - 1

        fused_results = []
        seen = set()

        for source, results in results_by_source.items():
            for result in results:
                result.score = borda_scores[result.result_id]
                if result.result_id not in seen:
                    fused_results.append(result)
                    seen.add(result.result_id)

        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results


class ResultDeduplicator:
    """结果去重器"""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        去重
        :return: 去重后的结果
        """
        if not results:
            return []

        # 按分数排序
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

        unique_results = []
        for result in sorted_results:
            is_duplicate = False

            for unique in unique_results:
                if self._compute_similarity(result, unique) > self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_results.append(result)

        return unique_results

    def _compute_similarity(self, r1: SearchResult, r2: SearchResult) -> float:
        """计算两个结果的相似度"""
        # 简单的词重叠
        words1 = set(r1.title.lower().split() + r1.snippet.lower().split())
        words2 = set(r2.title.lower().split() + r2.snippet.lower().split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        return overlap / min(len(words1), len(words2))


class FederatedSearchEngine:
    """联邦搜索引擎"""

    def __init__(self):
        self.sources: List[SearchSource] = []
        self.fusion = ScoreFusion(method="reciprocal_rank")
        self.deduplicator = ResultDeduplicator()

    def add_source(self, source: SearchSource):
        """添加数据源"""
        self.sources.append(source)

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        并行搜索所有数据源
        """
        # 并发查询所有源
        tasks = [source.search(query) for source in self.sources]
        results_by_source = {}

        for source, task in zip(self.sources, tasks):
            try:
                results = await task
                results_by_source[source.source_name] = results
            except Exception as e:
                print(f"  Source {source.source_name} failed: {e}")
                results_by_source[source.source_name] = []

        # 融合分数
        fused = self.fusion.fuse(results_by_source)

        # 去重
        deduplicated = self.deduplicator.deduplicate(fused)

        # 设置最终排名
        for rank, result in enumerate(deduplicated, 1):
            result.rank = rank

        return deduplicated[:query.num_results]

    def search_sync(self, query: SearchQuery) -> List[SearchResult]:
        """同步搜索接口"""
        return asyncio.run(self.search(query))


class QueryRouter:
    """查询路由器：根据查询类型选择数据源"""

    def __init__(self):
        self.source_keywords = {
            "web": ["what", "who", "how", "latest", "news"],
            "database": ["find", "show", "list", "count", "total"],
            "api_news": ["breaking", "update", "announcement"],
        }

    def route(self, query_text: str) -> Dict[str, float]:
        """
        决定各数据源的权重
        :return: {source_name: weight}
        """
        query_lower = query_text.lower()
        weights = {}

        for source, keywords in self.source_keywords.items():
            weight = 1.0
            for keyword in keywords:
                if keyword in query_lower:
                    weight += 0.5
            weights[source] = weight

        return weights


def evaluate_federated_search(engine: FederatedSearchEngine,
                              test_queries: List[str]) -> Dict[str, Any]:
    """评估联邦搜索"""
    latencies = []
    coverages = []

    for query_text in test_queries:
        query = SearchQuery(query_text=query_text, num_results=10)

        start = time.time()
        results = engine.search_sync(query)
        latency = time.time() - start

        latencies.append(latency)
        sources_covered = len(set(r.source for r in results))
        coverages.append(sources_covered)

    return {
        "avg_latency": np.mean(latencies),
        "avg_coverage": np.mean(coverages),
        "total_queries": len(test_queries)
    }


async def demo_async():
    """异步联邦搜索演示"""
    print("[联邦搜索演示]")

    # 创建搜索引擎
    engine = FederatedSearchEngine()
    engine.add_source(WebSearchSource())
    engine.add_source(DatabaseSearchSource())
    engine.add_source(APISearchSource("news"))
    engine.add_source(APISearchSource("products"))

    # 执行搜索
    query = SearchQuery(query_text="machine learning algorithms", num_results=10)
    results = await engine.search(query)

    print(f"\n  搜索查询: '{query.query_text}'")
    print(f"  总结果数: {len(results)}")

    for i, result in enumerate(results[:5], 1):
        print(f"\n  结果 {i} (rank={result.rank}, score={result.score:.4f}):")
        print(f"    来源: {result.source}")
        print(f"    标题: {result.title}")
        print(f"    摘要: {result.snippet[:60]}...")

    # 查询路由
    router = QueryRouter()
    weights = router.route("latest news about AI")
    print(f"\n  查询路由权重: {weights}")

    # 评估
    test_queries = ["python tutorial", "database records", "news update"]
    eval_result = evaluate_federated_search(engine, test_queries)
    print(f"\n  评估结果:")
    print(f"    平均延迟: {eval_result['avg_latency']:.4f}s")
    print(f"    平均覆盖率: {eval_result['avg_coverage']:.1f}个源")

    print("\n  ✅ 联邦搜索演示通过！")


def demo():
    """联邦搜索演示入口"""
    asyncio.run(demo_async())


if __name__ == "__main__":
    demo()
