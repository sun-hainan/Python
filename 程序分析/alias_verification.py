# -*- coding: utf-8 -*-
"""
别名验证（Alias Verification）
功能：验证两个指针/引用是否必定指向同一对象

别名分析问题：
- May-alias：可能指向同一对象
- Must-alias：必定指向同一对象

验证场景：
1. 编译器优化验证
2. 程序正确性证明
3. 安全分析

作者：Alias Verification Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class AliasRelation:
    """别名关系"""
    def __init__(self, p1: str, p2: str, alias_type: str):
        self.p1 = p1
        self.p2 = p2
        self.type = alias_type  # 'must', 'may', 'no'

    def __repr__(self):
        return f"{self.p1} {self.type}-alias {self.p2}"


class AliasVerifier:
    """
    别名验证器
    
    基于指针分析的别名关系验证
    """

    def __init__(self):
        # points-to关系: ptr → {targets}
        self.points_to: Dict[str, Set[str]] = defaultdict(set)
        # 变量别名
        self.alias_relations: List[AliasRelation] = []

    def add_points_to(self, ptr: str, target: str):
        """添加指向关系 ptr → target"""
        self.points_to[ptr].add(target)

    def add_assignment(self, lhs: str, rhs: str):
        """处理赋值 lhs = rhs"""
        if rhs in self.points_to:
            self.points_to[lhs] = self.points_to[rhs].copy()
        else:
            self.points_to[lhs].add(rhs)

    def check_may_alias(self, p1: str, p2: str) -> bool:
        """
        检查是否可能别名
        
        p1和p2可能指向同一对象当且仅当
        pts(p1) ∩ pts(p2) ≠ ∅
        """
        pts1 = self.points_to.get(p1, set())
        pts2 = self.points_to.get(p2, set())
        return bool(pts1 & pts2)

    def check_must_alias(self, p1: str, p2: str) -> bool:
        """
        检查是否必定别名
        
        p1和p2必定指向同一对象当且仅当
        pts(p1) = pts(p2) = {same_obj}
        """
        pts1 = self.points_to.get(p1, set())
        pts2 = self.points_to.get(p2, set())
        
        if len(pts1) == 1 and len(pts2) == 1:
            return pts1 == pts2
        return False

    def check_no_alias(self, p1: str, p2: str) -> bool:
        """
        检查是否必定不别名
        """
        pts1 = self.points_to.get(p1, set())
        pts2 = self.points_to.get(p2, set())
        return len(pts1) > 0 and len(pts2) > 0 and not (pts1 & pts2)

    def verify_all(self) -> List[AliasRelation]:
        """验证所有可能的别名对"""
        all_ptrs = list(self.points_to.keys())
        results = []
        
        for i in range(len(all_ptrs)):
            for j in range(i + 1, len(all_ptrs)):
                p1, p2 = all_ptrs[i], all_ptrs[j]
                
                if self.check_must_alias(p1, p2):
                    results.append(AliasRelation(p1, p2, 'must'))
                elif self.check_no_alias(p1, p2):
                    results.append(AliasRelation(p1, p2, 'no'))
                elif self.check_may_alias(p1, p2):
                    results.append(AliasRelation(p1, p2, 'may'))
        
        self.alias_relations = results
        return results


def example_simple_alias():
    """简单别名验证"""
    verifier = AliasVerifier()
    
    # p = &a
    verifier.add_points_to('p', 'a')
    # q = p
    verifier.add_assignment('q', 'p')
    
    print(f"p → {verifier.points_to['p']}")
    print(f"q → {verifier.points_to['q']}")
    print(f"p和q must-alias: {verifier.check_must_alias('p', 'q')}")
    print(f"p和q may-alias: {verifier.check_may_alias('p', 'q')}")


def example_no_alias():
    """不别名示例"""
    verifier = AliasVerifier()
    
    # p → a
    verifier.add_points_to('p', 'a')
    # q → b
    verifier.add_points_to('q', 'b')
    
    print(f"p和q may-alias: {verifier.check_may_alias('p', 'q')}")
    print(f"p和q no-alias: {verifier.check_no_alias('p', 'q')}")


def example_indirect():
    """间接引用示例"""
    verifier = AliasVerifier()
    
    # p = &a
    verifier.add_points_to('p', 'a')
    # q = p
    verifier.add_assignment('q', 'p')
    # r = q
    verifier.add_assignment('r', 'q')
    
    print(f"r → {verifier.points_to['r']}")
    print(f"p和r must-alias: {verifier.check_must_alias('p', 'r')}")


if __name__ == "__main__":
    print("=" * 50)
    print("别名验证 测试")
    print("=" * 50)
    
    example_simple_alias()
    print()
    example_no_alias()
    print()
    example_indirect()
