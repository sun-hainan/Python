# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / columnar_storage

本文件实现 columnar_storage 相关的算法功能。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import bisect


# =============================================================================
# 数据结构定义
# =============================================================================

@dataclass
class ColumnChunk:
    """列数据块：存储单列数据的物理格式"""
    name: str  # 列名
    values: List[Any]  # 原始值列表
    null_mask: List[bool]  # 空值掩码，True表示该位置为空
    statistics: Dict[str, Any] = None  # 列统计信息（min/max/null_count等）

    def __post_init__(self):
        if self.statistics is None:
            self.statistics = self._compute_statistics()

    def _compute_statistics(self) -> Dict[str, Any]:
        """计算列的基本统计信息"""
        non_null = [v for v, n in zip(self.values, self.null_mask) if not n]
        if not non_null:
            return {"min": None, "max": None, "null_count": len(self.null_mask), "distinct_count": 0}
        return {
            "min": min(non_null),
            "max": max(non_null),
            "null_count": sum(self.null_mask),
            "distinct_count": len(set(non_null))
        }


@dataclass
class DictionaryEncoding:
    """字典编码结构：用整数ID替代原始字符串值"""
    dictionary: List[Any]  # 字典：索引->原始值
    encoded: List[int]  # 编码后的整数数组

    def decode_batch(self, indices: List[int]) -> List[Any]:
        """批量解码：将整数ID转回原始值"""
        return [self.dictionary[i] for i in indices]

    def encode_batch(self, values: List[Any]) -> List[int]:
        """批量编码：将原始值转成整数ID"""
        result = []
        for v in values:
            try:
                idx = self.dictionary.index(v)
            except ValueError:
                # 值不在字典中，添加新条目
                idx = len(self.dictionary)
                self.dictionary.append(v)
            result.append(idx)
        return result


# =============================================================================
# RLE压缩
# =============================================================================

@dataclass
class RLEBlock:
    """RLE压缩块：存储[值, 重复次数]对"""
    value: Any  # 压缩的值
    count: int  # 重复次数


class RLECompression:
    """游程编码（Run-Length Encoding）压缩器"""

    @staticmethod
    def encode(values: List[Any]) -> List[RLEBlock]:
        """
        RLE编码：将连续相同的值合并为(值, 次数)对

        参数:
            values: 输入值列表

        返回:
            RLE块列表，每个块包含值和重复次数
        """
        if not values:
            return []

        blocks = []
        current_value = values[0]
        current_count = 1

        for v in values[1:]:
            if v == current_value:
                # 值相同，增加计数
                current_count += 1
            else:
                # 值不同，保存当前块，开始新块
                blocks.append(RLEBlock(current_value, current_count))
                current_value = v
                current_count = 1

        # 保存最后一个块
        blocks.append(RLEBlock(current_value, current_count))
        return blocks

    @staticmethod
    def decode(blocks: List[RLEBlock]) -> List[Any]:
        """RLE解码：将RLE块还原为原始值列表"""
        result = []
        for block in blocks:
            result.extend([block.value] * block.count)
        return result

    @staticmethod
    def compute_ratio(values: List[Any]) -> float:
        """计算压缩率（压缩后大小/原始大小）"""
        if not values:
            return 1.0
        blocks = RLECompression.encode(values)
        # 每个块需要存储：1个值 + 1个整数计数（假设值和计数各占1单位）
        compressed_size = len(blocks) * 2
        original_size = len(values)
        return compressed_size / original_size if original_size > 0 else 1.0


# =============================================================================
# 向量化执行引擎
# =============================================================================

class VectorizedExecutor:
    """
    向量化执行引擎：批量处理数据，避免逐行迭代的开销
    """

    @staticmethod
    def filter_batch(values: List[Any], mask: List[bool]) -> List[Any]:
        """
        批量过滤：根据布尔掩码筛选数据

        参数:
            values: 输入值列表
            mask: 布尔掩码，True表示保留该位置

        返回:
            过滤后的值列表
        """
        return [v for v, m in zip(values, mask) if m]

    @staticmethod
    def aggregate_sum(values: List[Any]) -> float:
        """批量求和（向量化实现）"""
        return sum(values)

    @staticmethod
    def aggregate_avg(values: List[Any]) -> float:
        """批量求平均（向量化实现）"""
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def aggregate_min(values: List[Any]) -> Any:
        """批量求最小值（向量化实现）"""
        return min(values) if values else None

    @staticmethod
    def aggregate_max(values: List[Any]) -> Any:
        """批量求最大值（向量化实现）"""
        return max(values) if values else None

    @staticmethod
    def batch_compare(values: List[Any], threshold: Any, op: str = ">") -> List[bool]:
        """
        批量比较操作

        参数:
            values: 输入值列表
            threshold: 比较阈值
            op: 比较操作符，">"、"<"、"==">="、"<="

        返回:
            布尔掩码列表
        """
        ops = {
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            "==": lambda a, b: a == b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "!=": lambda a, b: a != b
        }
        return [ops[op](v, threshold) for v in values]


# =============================================================================
# 延迟物化
# =============================================================================

class LateMaterialization:
    """
    延迟物化策略：延迟列拼接，直到真正需要时才组装行

    适用场景：
        - 查询只涉及少数列时，避免读取全部列
        - 减少中间结果的内存占用
        - 优化列式存储的I/O效率
    """

    def __init__(self):
        self.projected_columns: Dict[str, ColumnChunk] = {}  # 仅存储查询需要的列
        self.row_indices: Optional[List[int]] = None  # 满足过滤条件的行索引

    def add_projection(self, column: ColumnChunk):
        """添加需要投影的列"""
        self.projected_columns[column.name] = column

    def set_filter_indices(self, indices: List[int]):
        """设置过滤后的行索引"""
        self.row_indices = indices

    def materialize(self) -> List[Dict[str, Any]]:
        """
        执行物化：将列式数据组装成行式结果

        返回:
            行式数据列表，每行是一个字典
        """
        if not self.row_indices or not self.projected_columns:
            return []

        result = []
        # 获取行数
        num_rows = len(self.row_indices)

        for row_idx in self.row_indices:
            row_data = {}
            for col_name, column in self.projected_columns.items():
                row_data[col_name] = column.values[row_idx] if not column.null_mask[row_idx] else None
            result.append(row_data)

        return result


# =============================================================================
# 列式存储表
# =============================================================================

class ColumnarTable:
    """
    列式存储表：管理列式格式的数据

    优势：
        - 列压缩效率高（同类型数据连续存储）
        - 查询只读取需要的列，减少I/O
        - 向量化操作效率高
    """

    def __init__(self, name: str):
        self.name = name  # 表名
        self.columns: Dict[str, ColumnChunk] = {}  # 列名->列数据
        self.dictionaries: Dict[str, DictionaryEncoding] = {}  # 字典编码的列

    def add_column(self, name: str, values: List[Any], null_mask: Optional[List[bool]] = None):
        """
        添加一列数据

        参数:
            name: 列名
            values: 列值列表
            null_mask: 空值掩码（可选）
        """
        if null_mask is None:
            null_mask = [False] * len(values)
        self.columns[name] = ColumnChunk(name, values, null_mask)

    def apply_dictionary_encoding(self, column_name: str):
        """对指定列应用字典编码"""
        if column_name not in self.columns:
            raise ValueError(f"列 {column_name} 不存在")

        col = self.columns[column_name]
        dict_enc = DictionaryEncoding(dictionary=[], encoded=[])

        # 构建字典并编码
        for i, (val, is_null) in enumerate(zip(col.values, col.null_mask)):
            if is_null:
                dict_enc.encoded.append(-1)  # 空值用-1表示
            else:
                if val not in dict_enc.dictionary:
                    dict_enc.dictionary.append(val)
                dict_enc.encoded.append(dict_enc.dictionary.index(val))

        self.dictionaries[column_name] = dict_enc

    def apply_rle_compression(self, column_name: str) -> RLECompression:
        """对指定列应用RLE压缩，返回压缩后的块"""
        if column_name not in self.columns:
            raise ValueError(f"列 {column_name} 不存在")

        col = self.columns[column_name]
        non_null_values = [v for v, n in zip(col.values, col.null_mask) if not n]
        return RLECompression.encode(non_null_values)

    def filter_column(self, column_name: str, predicate) -> List[int]:
        """
        过滤列，返回满足条件的行索引

        参数:
            column_name: 列名
            predicate: 过滤谓词函数

        返回:
            满足条件的行索引列表
        """
        if column_name not in self.columns:
            raise ValueError(f"列 {column_name} 不存在")

        col = self.columns[column_name]
        return [i for i, (v, n) in enumerate(zip(col.values, col.null_mask))
                if not n and predicate(v)]

    def select_columns(self, column_names: List[str]) -> 'ColumnarTable':
        """选择指定的列，创建新的列式表"""
        new_table = ColumnarTable(f"{self.name}_projection")
        for name in column_names:
            if name in self.columns:
                new_table.columns[name] = self.columns[name]
        return new_table


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    # 创建测试数据
    print("=" * 60)
    print("列式存储测试")
    print("=" * 60)

    # 测试1：RLE压缩
    print("\n【测试1：RLE压缩】")
    rle_values = [1, 1, 1, 2, 2, 3, 3, 3, 3, 5]
    blocks = RLECompression.encode(rle_values)
    print(f"原始值: {rle_values}")
    print(f"RLE块: {[(b.value, b.count) for b in blocks]}")
    decoded = RLECompression.decode(blocks)
    print(f"解压后: {decoded}")
    print(f"压缩率: {RLECompression.compute_ratio(rle_values):.2%}")

    # 测试2：字典编码
    print("\n【测试2：字典编码】")
    dict_enc = DictionaryEncoding(dictionary=[], encoded=[])
    test_values = ["apple", "banana", "apple", "cherry", "banana", "apple"]
    encoded = dict_enc.encode_batch(test_values)
    print(f"原始值: {test_values}")
    print(f"字典: {dict_enc.dictionary}")
    print(f"编码: {encoded}")
    decoded = dict_enc.decode_batch(encoded)
    print(f"解码: {decoded}")

    # 测试3：列式表
    print("\n【测试3：列式存储表】")
    table = ColumnarTable("users")
    table.add_column("id", [1, 2, 3, 4, 5])
    table.add_column("name", ["Alice", "Bob", "Carol", "Dave", "Eve"])
    table.add_column("age", [25, 30, 35, 40, 45], null_mask=[False, False, True, False, False])
    table.add_column("city", ["NYC", "LA", "NYC", "NYC", "SF"])

    print(f"表名: {table.name}")
    print(f"列统计: {table.columns['age'].statistics}")

    # 应用字典编码
    table.apply_dictionary_encoding("city")
    print(f"城市字典: {table.dictionaries['city'].dictionary}")
    print(f"城市编码: {table.dictionaries['city'].encoded}")

    # 向量化过滤
    print("\n【测试4：向量化执行】")
    ages = table.columns["age"].values
    mask = VectorizedExecutor.batch_compare(ages, 30, ">")
    filtered = VectorizedExecutor.filter_batch(ages, mask)
    print(f"年龄列表: {ages}")
    print(f"过滤掩码(>30): {mask}")
    print(f"过滤结果: {filtered}")
    print(f"平均年龄: {VectorizedExecutor.aggregate_avg(ages)}")

    # 测试5：延迟物化
    print("\n【测试5：延迟物化】")
    lm = LateMaterialization()
    lm.add_projection(table.columns["id"])
    lm.add_projection(table.columns["name"])
    lm.set_filter_indices([0, 2, 4])
    result = lm.materialize()
    print(f"延迟物化结果（索引0,2,4）: {result}")
