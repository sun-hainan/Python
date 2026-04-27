# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / optimizer_plan_cache

本文件实现 optimizer_plan_cache 相关的算法功能。
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict


@dataclass
class PlanNode:
    """计划节点"""
    operator: str  # 操作类型
    cost: float  # 代价
    rows: int  # 输出行数
    children: List['PlanNode'] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CachedPlan:
    """缓存的计划"""
    plan: PlanNode  # 执行计划
    created_at: float  # 创建时间
    last_accessed: float  # 最后访问时间
    hit_count: int = 0  # 命中次数
    avg_cost: float = 0.0  # 平均执行代价


@dataclass
class CacheEntry:
    """缓存条目"""
    query_signature: str  # 查询签名
    query_text: str  # 原始查询文本
    cached_plan: CachedPlan  # 缓存的计划
    parameter_values: Tuple = field(default_factory=tuple)  # 参数值


class PlanCache:
    """
    查询计划缓存

    特性:
    1. LRU淘汰策略
    2. 参数化查询支持
    3. 自适应缓存大小
    4. 统计信息收集
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 3600):
        self.max_size = max_size  # 最大缓存条目数
        self.ttl_seconds = ttl_seconds  # 缓存有效期(秒)
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()  # 缓存存储
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0
        }

    def compute_signature(self, query: str, params: tuple = None) -> str:
        """
        计算查询签名

        参数化查询使用参数值和查询结构共同签名
        """
        # 标准化查询(去除多余空格,转小写)
        normalized = " ".join(query.lower().split())

        # 如果有参数,添加参数哈希
        if params:
            param_str = json.dumps(params, sort_keys=True)
            combined = f"{normalized}|{param_str}"
        else:
            combined = normalized

        # SHA256哈希
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def get(self, query: str, params: tuple = None) -> Optional[PlanNode]:
        """
        获取缓存的计划

        参数:
            query: 查询文本
            params: 参数值

        返回:
            缓存的计划,未命中返回None
        """
        self.stats["total_queries"] += 1
        signature = self.compute_signature(query, params)

        if signature not in self.cache:
            self.stats["misses"] += 1
            return None

        entry = self.cache[signature]

        # 检查是否过期
        if time.time() - entry.cached_plan.created_at > self.ttl_seconds:
            self._evict(signature)
            self.stats["misses"] += 1
            return None

        # 命中
        entry.cached_plan.last_accessed = time.time()
        entry.cached_plan.hit_count += 1

        # 移到末尾(最近使用)
        self.cache.move_to_end(signature)

        self.stats["hits"] += 1
        return entry.cached_plan.plan

    def put(self, query: str, plan: PlanNode,
            params: tuple = None, total_cost: float = 0.0):
        """
        缓存执行计划

        参数:
            query: 查询文本
            plan: 执行计划
            params: 参数值
            total_cost: 执行总代价
        """
        signature = self.compute_signature(query, params)

        cached_plan = CachedPlan(
            plan=plan,
            created_at=time.time(),
            last_accessed=time.time(),
            avg_cost=total_cost
        )

        entry = CacheEntry(
            query_signature=signature,
            query_text=query,
            cached_plan=cached_plan,
            parameter_values=params or ()
        )

        # 如果已存在,更新
        if signature in self.cache:
            self.cache.move_to_end(signature)

        self.cache[signature] = entry

        # 检查是否需要淘汰
        if len(self.cache) > self.max_size:
            self._evict_lru()

    def _evict(self, signature: str):
        """驱逐指定条目"""
        if signature in self.cache:
            del self.cache[signature]
            self.stats["evictions"] += 1

    def _evict_lru(self):
        """淘汰最久未使用的条目"""
        if self.cache:
            oldest = next(iter(self.cache))
            self._evict(oldest)

    def invalidate(self, pattern: str = None):
        """
        使缓存失效

        参数:
            pattern: 如果指定,只使匹配的缓存失效
        """
        if pattern is None:
            # 清空所有
            self.cache.clear()
        else:
            # 只删除匹配的
            to_remove = [k for k, v in self.cache.items()
                        if pattern.lower() in v.query_text.lower()]
            for k in to_remove:
                self._evict(k)

    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        hit_rate = 0.0
        if self.stats["total_queries"] > 0:
            hit_rate = self.stats["hits"] / self.stats["total_queries"]

        avg_hit_count = 0.0
        if self.cache:
            avg_hit_count = sum(e.cached_plan.hit_count for e in self.cache.values()) / len(self.cache)

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.2%}",
            "avg_hit_count": avg_hit_count,
            "evictions": self.stats["evictions"],
            "total_queries": self.stats["total_queries"]
        }

    def get_top_plans(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取最常用的计划"""
        sorted_entries = sorted(self.cache.values(),
                               key=lambda e: e.cached_plan.hit_count,
                               reverse=True)

        result = []
        for entry in sorted_entries[:n]:
            result.append({
                "query": entry.query_text[:100],  # 截断显示
                "hit_count": entry.cached_plan.hit_count,
                "avg_cost": entry.cached_plan.avg_cost,
                "last_accessed": time.ctime(entry.cached_plan.last_accessed)
            })
        return result


class AdaptiveCache(PlanCache):
    """
    自适应缓存

    根据查询特征动态调整缓存策略
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 3600):
        super().__init__(max_size, ttl_seconds)
        self.query_frequency: Dict[str, int] = {}  # 查询频率
        self.recent_queries: List[str] = []  # 最近查询(用于去重)
        self.max_recent = 100

    def get(self, query: str, params: tuple = None) -> Optional[PlanNode]:
        """获取缓存,更新频率统计"""
        result = super().get(query, params)

        signature = self.compute_signature(query, params)

        # 更新频率
        self.query_frequency[signature] = self.query_frequency.get(signature, 0) + 1

        # 更新最近查询
        self.recent_queries.append(signature)
        if len(self.recent_queries) > self.max_recent:
            self.recent_queries.pop(0)

        return result

    def should_cache(self, query: str, params: tuple = None) -> bool:
        """
        判断是否应该缓存

        策略:
        1. 频繁查询应该缓存
        2. 最近执行过的查询应该缓存
        """
        signature = self.compute_signature(query, params)

        # 策略1: 频率阈值
        if self.query_frequency.get(signature, 0) < 2:
            return False

        # 策略2: 最近执行过
        if signature in self.recent_queries[-20:]:
            return True

        return True

    def adjust_cache_size(self):
        """
        动态调整缓存大小

        如果命中率低,减少缓存大小
        如果命中率高,增加缓存大小
        """
        hit_rate = 0.0
        if self.stats["total_queries"] > 10:
            hit_rate = self.stats["hits"] / self.stats["total_queries"]

        # 命中率低,减少大小
        if hit_rate < 0.1 and self.max_size > 100:
            new_size = int(self.max_size * 0.8)
            print(f"调整缓存大小: {self.max_size} -> {new_size}")
            self.max_size = new_size

            # 淘汰多余条目
            while len(self.cache) > self.max_size:
                self._evict_lru()


def print_cache_stats(cache: PlanCache):
    """打印缓存统计"""
    stats = cache.get_statistics()
    print("=== 计划缓存统计 ===")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    cache = AdaptiveCache(max_size=100, ttl_seconds=60)

    # 模拟查询
    queries = [
        "SELECT * FROM users WHERE id = ?",
        "SELECT * FROM orders WHERE customer_id = ?",
        "SELECT * FROM users WHERE id = ?",  # 重复
        "SELECT * FROM orders WHERE status = ?",
        "SELECT * FROM users WHERE id = ?",  # 再次重复
    ]

    # 创建模拟计划
    def make_plan(op: str, cost: float) -> PlanNode:
        return PlanNode(operator=op, cost=cost, rows=100)

    params_list = [(1,), (100,), (2,), ("pending",), (3,)]

    print("=== 模拟查询缓存 ===")
    for i, (q, p) in enumerate(zip(queries, params_list)):
        # 检查是否应该缓存
        should = cache.should_cache(q, p)
        print(f"查询{i+1}: {q[:40]}... params={p}, should_cache={should}")

        # 尝试获取
        plan = cache.get(q, p)
        if plan:
            print(f"  命中! 操作: {plan.operator}")
        else:
            print(f"  未命中,缓存计划")
            plan = make_plan("scan", 100.0)
            cache.put(q, plan, p, 100.0)

    print_cache_stats(cache)

    # 自适应调整
    print("\n=== 自适应调整 ===")
    cache.adjust_cache_size()

    # Top计划
    print("\n=== Top 3 计划 ===")
    top = cache.get_top_plans(3)
    for i, t in enumerate(top):
        print(f"{i+1}. {t['query']}")
        print(f"   命中: {t['hit_count']}, 代价: {t['avg_cost']}")
