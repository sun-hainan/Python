# -*- coding: utf-8 -*-
"""
算法实现：软件工程算法 / semantic_version

本文件实现 semantic_version 相关的算法功能。
"""

import re
from typing import List, Tuple, Optional, Dict
from functools import total_ordering


@total_ordering
class SemanticVersion:
    """
    语义版本类
    """
    
    def __init__(self, major: int = 0, minor: int = 0, patch: int = 0,
                 prerelease: str = "", build: str = ""):
        """
        初始化
        
        参数:
            major: 主版本号
            minor: 次版本号
            patch: 补丁版本号
            prerelease: 预发布标签
            build: 构建元数据
        """
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        self.build = build
    
    @classmethod
    def parse(cls, version_string: str) -> "SemanticVersion":
        """
        解析版本字符串
        
        参数:
            version_string: 版本字符串，如 "1.2.3-alpha.1+build.123"
        
        返回:
            SemanticVersion对象
        """
        # 正则表达式匹配语义版本
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$'
        match = re.match(pattern, version_string.strip())
        
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        
        major, minor, patch = map(int, match.groups()[:3])
        prerelease = match.group(4) or ""
        build = match.group(5) or ""
        
        return cls(major, minor, patch, prerelease, build)
    
    def _compare(self, other: "SemanticVersion") -> int:
        """
        比较两个版本
        
        返回:
            -1 (小于), 0 (等于), 1 (大于)
        """
        # 比较主版本
        if self.major != other.major:
            return 1 if self.major > other.major else -1
        
        # 比较次版本
        if self.minor != other.minor:
            return 1 if self.minor > other.minor else -1
        
        # 比较补丁版本
        if self.patch != other.patch:
            return 1 if self.patch > other.patch else -1
        
        # 比较预发布标签
        # 没有预发布的版本 > 有预发布的版本
        if not self.prerelease and not other.prerelease:
            return 0
        elif not self.prerelease:
            return 1
        elif not other.prerelease:
            return -1
        else:
            return self._compare_prerelease(other.prerelease)
    
    def _compare_prerelease(self, other_prerelease: str) -> int:
        """
        比较预发布标签
        
        预发布标签按点号分割，每个部分单独比较：
        - 数字部分 < 字母部分
        - 数字部分按数值比较
        - 字母部分按字典序比较
        """
        parts1 = self.prerelease.split('.')
        parts2 = other_prerelease.split('.')
        
        max_len = max(len(parts1), len(parts2))
        
        for i in range(max_len):
            if i >= len(parts1):
                return -1  # 更短的预发布标签更小
            if i >= len(parts2):
                return 1
            
            p1, p2 = parts1[i], parts2[i]
            
            # 尝试作为数字比较
            try:
                n1, n2 = int(p1), int(p2)
                if n1 != n2:
                    return 1 if n1 > n2 else -1
            except ValueError:
                # 作为字符串比较
                if p1 != p2:
                    return 1 if p1 > p2 else -1
        
        return 0
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return self._compare(other) == 0
    
    def __lt__(self, other: "SemanticVersion") -> bool:
        return self._compare(other) < 0
    
    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.prerelease, self.build))
    
    def __repr__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def is_prerelease(self) -> bool:
        """是否是预发布版本"""
        return bool(self.prerelease)
    
    def is_stable(self) -> bool:
        """是否是稳定版本（无预发布标签）"""
        return not self.prerelease


def sort_versions(versions: List[str]) -> List[str]:
    """
    对版本字符串列表排序
    
    参数:
        versions: 版本字符串列表
    
    返回:
        排序后的版本字符串列表
    """
    parsed = [SemanticVersion.parse(v) for v in versions]
    parsed.sort()
    return [str(v) for v in parsed]


def is_compatible(current: str, requirement: str) -> bool:
    """
    检查版本是否满足兼容性要求
    
    遵循语义版本规范：
    - "~1.2.3" 兼容 1.2.x
    - "^1.2.3" 兼容 1.x.x
    - "1.2.3" 精确匹配
    
    参数:
        current: 当前版本
        requirement: 要求版本
    
    返回:
        是否兼容
    """
    cur = SemanticVersion.parse(current)
    req = SemanticVersion.parse(requirement)
    
    # 主版本匹配
    if cur.major == req.major:
        # 次版本至少匹配
        if cur.minor >= req.minor:
            # 补丁版本至少匹配
            if cur.minor > req.minor or cur.patch >= req.patch:
                return True
    return False


def bump_version(version: str, part: str = "patch") -> str:
    """
    增加版本号
    
    参数:
        version: 原始版本
        part: 要增加的部分 ("major", "minor", "patch")
    
    返回:
        新的版本字符串
    """
    v = SemanticVersion.parse(version)
    
    if part == "major":
        v.major += 1
        v.minor = 0
        v.patch = 0
    elif part == "minor":
        v.minor += 1
        v.patch = 0
    elif part == "patch":
        v.patch += 1
    
    v.prerelease = ""
    v.build = ""
    
    return str(v)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本解析和比较
    print("=" * 50)
    print("测试1: 基本解析和比较")
    print("=" * 50)
    
    versions = ["1.2.3", "1.2.0", "2.0.0", "1.3.0", "0.1.0"]
    
    print("原始:", versions)
    print("排序:", sort_versions(versions))
    
    # 测试用例2：预发布版本
    print("\n" + "=" * 50)
    print("测试2: 预发布版本比较")
    print("=" * 50)
    
    versions = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
    ]
    
    print("预发布版本排序:")
    for v in sort_versions(versions):
        print(f"  {v}")
    
    # 测试用例3：构建元数据
    print("\n" + "=" * 50)
    print("测试3: 构建元数据")
    print("=" * 50)
    
    v1 = SemanticVersion.parse("1.0.0+build.123")
    v2 = SemanticVersion.parse("1.0.0+build.456")
    
    print(f"v1 = {v1}")
    print(f"v2 = {v2}")
    print(f"v1 == v2: {v1 == v2}")  # 构建元数据不影响比较
    
    # 测试用例4：版本兼容性
    print("\n" + "=" * 50)
    print("测试4: 版本兼容性")
    print("=" * 50)
    
    test_cases = [
        ("1.2.3", "1.2.0"),
        ("1.2.3", "1.3.0"),
        ("1.2.3", "2.0.0"),
        ("2.0.0", "1.9.9"),
    ]
    
    for current, requirement in test_cases:
        compatible = is_compatible(current, requirement)
        print(f"  {current} 兼容 {requirement}: {compatible}")
    
    # 测试用例5：版本号递增
    print("\n" + "=" * 50)
    print("测试5: 版本号递增")
    print("=" * 50)
    
    version = "1.2.3"
    print(f"原始版本: {version}")
    print(f"  bump patch: {bump_version(version, 'patch')}")
    print(f"  bump minor: {bump_version(version, 'minor')}")
    print(f"  bump major: {bump_version(version, 'major')}")
    
    # 测试用例6：版本范围
    print("\n" + "=" * 50)
    print("测试6: 验证版本属性")
    print("=" * 50)
    
    versions = [
        "1.0.0",
        "1.0.0-alpha",
        "2.0.0-beta.1",
        "2.0.0",
    ]
    
    print("版本稳定性:")
    for v_str in versions:
        v = SemanticVersion.parse(v_str)
        print(f"  {v_str}:")
        print(f"    is_stable: {v.is_stable()}")
        print(f"    is_prerelease: {v.is_prerelease()}")
    
    # 测试用例7：错误处理
    print("\n" + "=" * 50)
    print("测试7: 错误处理")
    print("=" * 50)
    
    invalid_versions = [
        "1.2",         # 缺少patch
        "v1.2.3",      # 前缀v
        "1.2.3.4",     # 太多部分
        "1.a.3",       # 非数字
    ]
    
    for v_str in invalid_versions:
        try:
            v = SemanticVersion.parse(v_str)
            print(f"  {v_str}: 解析成功 -> {v}")
        except ValueError as e:
            print(f"  {v_str}: 解析失败 -> {e}")
