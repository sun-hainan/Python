# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / statistics_histograms



本文件实现 statistics_histograms 相关的算法功能。

"""



from typing import List, Dict, Tuple, Any, Optional

from dataclasses import dataclass

from collections import Counter

import math



@dataclass

class HistogramBucket:

    """直方图桶"""

    start_value: Any    # 桶起始值（包含）

    end_value: Any      # 桶结束值（不包含）

    count: int          # 桶中的记录数

    distinct_count: int # 桶中不同值的数量

    

    def __repr__(self):

        return f"Bucket({self.start_value}-{self.end_value}, count={self.count})"





class EquiWidthHistogram:

    """

    等宽直方图

    每个桶的宽度相等，桶数量固定

    适用于值域分布均匀的场景

    """

    

    def __init__(self, num_buckets: int):

        self.num_buckets = num_buckets  # 桶数量

        self.buckets: List[HistogramBucket] = []

        self.min_value: Any = None

        self.max_value: Any = None

    

    def build(self, values: List[Any]):

        """从值列表构建直方图"""

        if not values:

            return

        

        self.min_value = min(values)

        self.max_value = max(values)

        

        # 计算桶宽度

        try:

            width = (self.max_value - self.min_value) / self.num_buckets

        except TypeError:

            # 无法计算宽度，使用等深直方图

            return

        

        if width == 0:

            width = 1

        

        # 初始化桶

        self.buckets = []

        for i in range(self.num_buckets):

            bucket = HistogramBucket(

                start_value=self.min_value + i * width,

                end_value=self.min_value + (i + 1) * width,

                count=0,

                distinct_count=0

            )

            self.buckets.append(bucket)

        

        # 填充桶

        counter = Counter(values)

        

        for value, freq in counter.items():

            if isinstance(value, (int, float)):

                bucket_idx = min(

                    int((value - self.min_value) / width),

                    self.num_buckets - 1

                )

            else:

                bucket_idx = 0

            

            if 0 <= bucket_idx < len(self.buckets):

                self.buckets[bucket_idx].count += freq

        

        # 计算不同值数量（简化估计）

        total_distinct = len(counter)

        per_bucket_distinct = total_distinct / self.num_buckets

        

        for bucket in self.buckets:

            bucket.distinct_count = int(per_bucket_distinct * (bucket.count / (len(values) / self.num_buckets)))

            bucket.distinct_count = max(1, bucket.distinct_count)

    

    def estimate_selectivity(self, predicate: Tuple[str, Any]) -> float:

        """

        估算谓词的选择性

        predicate: (operator, value) 如 ("=", 100) 或 (">", 50)

        """

        op, value = predicate

        

        total_count = sum(b.count for b in self.buckets)

        if total_count == 0:

            return 0.0

        

        total_selectivity = 0.0

        

        for bucket in self.buckets:

            if op == "=":

                if bucket.start_value <= value < bucket.end_value:

                    total_selectivity += bucket.count / bucket.distinct_count if bucket.distinct_count > 0 else bucket.count

            elif op == ">":

                if bucket.start_value >= value:

                    total_selectivity += bucket.count

                elif bucket.start_value < value < bucket.end_value:

                    # 部分匹配

                    ratio = (bucket.end_value - value) / (bucket.end_value - bucket.start_value)

                    total_selectivity += bucket.count * ratio

            elif op == "<":

                if bucket.end_value <= value:

                    total_selectivity += bucket.count

                elif bucket.start_value < value < bucket.end_value:

                    ratio = (value - bucket.start_value) / (bucket.end_value - bucket.start_value)

                    total_selectivity += bucket.count * ratio

            elif op == ">=":

                if bucket.start_value >= value:

                    total_selectivity += bucket.count

                elif bucket.start_value < value < bucket.end_value:

                    ratio = (bucket.end_value - value) / (bucket.end_value - bucket.start_value)

                    total_selectivity += bucket.count * ratio

            elif op == "<=":

                if bucket.end_value <= value:

                    total_selectivity += bucket.count

                elif bucket.start_value < value < bucket.end_value:

                    ratio = (value - bucket.start_value) / (bucket.end_value - bucket.start_value)

                    total_selectivity += bucket.count * ratio

        

        return total_selectivity / total_count





class EquiDepthHistogram:

    """

    等深直方图（等高直方图）

    每个桶包含大致相同数量的记录

    适用于值域分布不均匀的场景

    """

    

    def __init__(self, num_buckets: int):

        self.num_buckets = num_buckets

        self.buckets: List[HistogramBucket] = []

    

    def build(self, values: List[Any]):

        """从值列表构建直方图"""

        if not values:

            return

        

        # 排序

        sorted_values = sorted(values)

        total_count = len(sorted_values)

        

        # 每个桶应包含的记录数

        depth = total_count / self.num_buckets

        

        self.buckets = []

        

        for i in range(self.num_buckets):

            start_idx = int(i * depth)

            end_idx = int((i + 1) * depth)

            

            if i == self.num_buckets - 1:

                end_idx = total_count  # 最后一桶包含所有剩余记录

            

            start_value = sorted_values[start_idx]

            end_value = sorted_values[min(end_idx, total_count - 1)]

            

            bucket_values = sorted_values[start_idx:end_idx]

            distinct_count = len(set(bucket_values))

            

            bucket = HistogramBucket(

                start_value=start_value,

                end_value=end_value,

                count=len(bucket_values),

                distinct_count=distinct_count

            )

            self.buckets.append(bucket)

    

    def estimate_selectivity(self, predicate: Tuple[str, Any]) -> float:

        """估算谓词选择性（与等宽类似）"""

        op, value = predicate

        

        total_count = sum(b.count for b in self.buckets)

        if total_count == 0:

            return 0.0

        

        total_selectivity = 0.0

        

        for bucket in self.buckets:

            if op == "=":

                # 对于等深直方图，假设值均匀分布在桶内

                if bucket.start_value <= value <= bucket.end_value:

                    selectivity = bucket.count / bucket.distinct_count if bucket.distinct_count > 0 else 0

                    total_selectivity += selectivity

            elif op in (">", ">="):

                if bucket.start_value >= value:

                    total_selectivity += bucket.count

                elif bucket.start_value < value < bucket.end_value:

                    ratio = (bucket.end_value - value) / (bucket.end_value - bucket.start_value + 1)

                    total_selectivity += bucket.count * ratio

            elif op in ("<", "<="):

                if bucket.end_value <= value:

                    total_selectivity += bucket.count

                elif bucket.start_value < value < bucket.end_value:

                    ratio = (value - bucket.start_value) / (bucket.end_value - bucket.start_value + 1)

                    total_selectivity += bucket.count * ratio

        

        return total_selectivity / total_count





class SkewSensitiveHistogram:

    """

    偏斜敏感直方图

    更好地处理数据倾斜（某些值出现频率极高）

    """

    

    def __init__(self, num_buckets: int, threshold: float = 0.01):

        self.num_buckets = num_buckets

        self.threshold = threshold  # 频率阈值，超过则为高频值

        self.buckets: List[HistogramBucket] = []

        self.frequent_values: Dict[Any, int] = {}  # 高频值及其频率

    

    def build(self, values: List[Any]):

        """构建直方图"""

        if not values:

            return

        

        counter = Counter(values)

        total_count = len(values)

        

        # 识别高频值

        self.frequent_values = {

            value: freq for value, freq in counter.items()

            if freq / total_count >= self.threshold

        }

        

        # 去除高频值后的残差数据

        residual_values = [v for v in values if v not in self.frequent_values]

        

        if residual_values:

            # 用等深直方图处理残差

            residual_histogram = EquiDepthHistogram(self.num_buckets)

            residual_histogram.build(residual_values)

            self.buckets = residual_histogram.buckets

        else:

            self.buckets = []

    

    def estimate_selectivity(self, predicate: Tuple[str, Any]) -> float:

        """估算选择性（考虑高频值）"""

        op, value = predicate

        

        total_count = sum(b.count for b in self.buckets) + sum(self.frequent_values.values())

        

        if total_count == 0:

            return 0.0

        

        selectivity = 0.0

        

        # 检查是否是高频值

        if value in self.frequent_values:

            if op == "=":

                selectivity += self.frequent_values[value]

        

        # 从直方图估算

        for bucket in self.buckets:

            if op in (">", ">=") and bucket.start_value >= value:

                selectivity += bucket.count

            elif op in ("<", "<=") and bucket.end_value <= value:

                selectivity += bucket.count

        

        return selectivity / total_count





class NDVEstimator:

    """

    NDV（Number of Distinct Values）估计器

    使用HyperLogLog算法估计大型数据集中不同值的数量

    """

    

    def __init__(self, error_rate: float = 0.01):

        self.error_rate = error_rate

        self.register_size = int(math.ceil(-math.log(error_rate) / math.log(2)))

        self.registers = [0] * self.register_size

    

    def _hash(self, value: Any) -> int:

        """哈希函数"""

        return hash(str(value)) % (2 ** 32)

    

    def add(self, value: Any):

        """添加值"""

        hash_val = self._hash(value)

        

        # 计算前导零的数量

        leading_zeros = 0

        temp = hash_val

        while (temp & 0x80000000) == 0 and leading_zeros < 32:

            temp <<= 1

            leading_zeros += 1

        

        # 更新对应寄存器的值

        idx = hash_val % self.register_size

        self.registers[idx] = max(self.registers[idx], leading_zeros)

    

    def estimate_ndv(self) -> int:

        """

        估计不同值的数量

        使用HyperLogLog公式

        """

        m = self.register_size

        

        # 计算调和平均

        sum_inv = 0.0

        for count in self.registers:

            sum_inv += 1.0 / (2 ** count if count < 64 else 2 ** 63)

        

        # 估算

        if sum_inv == 0:

            return 0

        

        raw_estimate = m * m / sum_inv

        

        # 小型数据修正

        if raw_estimate < 2.5 * m:

            zero_count = self.registers.count(0)

            if zero_count > 0:

                return int(m * math.log(m / zero_count))

        

        return int(raw_estimate)





class CardinalityEstimator:

    """

    基数估计器

    估计查询返回的行数

    """

    

    def __init__(self):

        self.histogram: Optional[EquiDepthHistogram] = None

        self.ndv_estimator = NDVEstimator()

        self.total_rows = 0

    

    def build_statistics(self, values: List[Any]):

        """构建统计信息"""

        self.total_rows = len(values)

        

        # 构建直方图

        self.histogram = EquiDepthHistogram(num_buckets=10)

        self.histogram.build(values)

        

        # 构建NDV估计器

        for v in values:

            self.ndv_estimator.add(v)

    

    def estimate_cardinality(self, predicate: Tuple[str, Any]) -> int:

        """估计单个谓词的基数"""

        if self.histogram is None:

            return 0

        

        selectivity = self.histogram.estimate_selectivity(predicate)

        return int(selectivity * self.total_rows)

    

    def estimate_join_cardinality(self, left_values: List[Any], 

                                  right_values: List[Any]) -> int:

        """估计Join基数"""

        # 使用独立性和均匀分布假设

        left_ndv = len(set(left_values))

        right_ndv = len(set(right_values))

        

        if left_ndv == 0 or right_ndv == 0:

            return 0

        

        # 小表驱动大表

        smaller = left_values if left_ndv <= right_ndv else right_values

        larger = left_values if left_ndv > right_ndv else right_values

        

        # 估计join后的基数

        smaller_distinct = len(set(smaller))

        larger_distinct = len(set(larger))

        

        # 交集大小估计

        intersection_size = min(smaller_distinct, larger_distinct) * (len(larger) / larger_distinct)

        

        return int(intersection_size * (len(larger) / len(set(larger))))





if __name__ == "__main__":

    import random

    

    print("=" * 60)

    print("统计信息与基数估计演示")

    print("=" * 60)

    

    # 生成测试数据（模拟年龄分布，有倾斜）

    ages = []

    for _ in range(10000):

        if random.random() < 0.3:

            ages.append(30)  # 高频值

        else:

            ages.append(random.randint(18, 80))

    

    # 等宽直方图

    print("\n--- 等宽直方图 ---")

    equi_width = EquiWidthHistogram(num_buckets=5)

    equi_width.build(ages)

    

    for i, bucket in enumerate(equi_width.buckets):

        print(f"  桶{i}: {bucket.start_value:.0f}-{bucket.end_value:.0f}, "

              f"count={bucket.count}, distinct={bucket.distinct_count}")

    

    # 等深直方图

    print("\n--- 等深直方图 ---")

    equi_depth = EquiDepthHistogram(num_buckets=5)

    equi_depth.build(ages)

    

    for i, bucket in enumerate(equi_depth.buckets):

        print(f"  桶{i}: {bucket.start_value:.0f}-{bucket.end_value:.0f}, "

              f"count={bucket.count}, distinct={bucket.distinct_count}")

    

    # 偏斜敏感直方图

    print("\n--- 偏斜敏感直方图 ---")

    skew_hist = SkewSensitiveHistogram(num_buckets=5, threshold=0.01)

    skew_hist.build(ages)

    print(f"  高频值: {skew_hist.frequent_values}")

    

    # 基数估计

    print("\n--- 基数估计 ---")

    estimator = CardinalityEstimator()

    estimator.build_statistics(ages)

    

    print(f"  总行数: {estimator.total_rows}")

    print(f"  估算NDV: {estimator.ndv_estimator.estimate_ndv()}")

    print(f"  实际NDV: {len(set(ages))}")

    

    # 估算谓词选择性

    for predicate in [("=", 30), (">", 50), ("<", 25)]:

        selectivity = estimator.histogram.estimate_selectivity(predicate)

        est_card = int(selectivity * estimator.total_rows)

        actual_card = sum(1 for a in ages if 

            (predicate[0] == "=" and a == predicate[1]) or

            (predicate[0] == ">" and a > predicate[1]) or

            (predicate[0] == "<" and a < predicate[1]))

        print(f"  谓词{predicate}: 估算 selectivity={selectivity:.4f}, "

              f"估算基数={est_card}, 实际基数={actual_card}")

