# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / external_sort

本文件实现 external_sort 相关的算法功能。
"""

import os
import tempfile
import heapq
from typing import List, Generator


class ExternalSorter:
    """外部排序器"""

    def __init__(self, chunk_size: int = 10000):
        """
        参数：
            chunk_size: 每块可容纳的元素数
        """
        self.chunk_size = chunk_size
        self.temp_dir = tempfile.mkdtemp(prefix="extsort_")
        self.chunks = []

    def sort_file(self, input_file: str, output_file: str, num_ways: int = 4):
        """
        对文件排序（假设文件每行一个数字或字符串）

        参数：
            input_file: 输入文件路径
            output_file: 输出文件路径
            num_ways: 归并路数
        """
        # 步骤1：分块并排序
        num_chunks = self._split_and_sort(input_file)
        print(f"生成了 {num_chunks} 个有序块")

        # 步骤2：多路归并
        self._merge_chunks(output_file, num_chunks, num_ways)

        # 清理临时文件
        self._cleanup()

    def _split_and_sort(self, input_file: str) -> int:
        """分块并排序，返回块数量"""
        chunk_idx = 0

        with open(input_file, 'r', encoding='utf-8') as f:
            buffer = []

            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    # 尝试转为数字
                    val = int(line)
                except ValueError:
                    val = line

                buffer.append(val)

                if len(buffer) >= self.chunk_size:
                    # 排序并写入临时文件
                    buffer.sort()
                    chunk_file = os.path.join(self.temp_dir, f"chunk_{chunk_idx}.txt")
                    self._write_chunk(chunk_file, buffer)
                    self.chunks.append(chunk_file)
                    chunk_idx += 1
                    buffer = []

            # 处理剩余数据
            if buffer:
                buffer.sort()
                chunk_file = os.path.join(self.temp_dir, f"chunk_{chunk_idx}.txt")
                self._write_chunk(chunk_file, buffer)
                self.chunks.append(chunk_file)
                chunk_idx += 1

        return chunk_idx

    def _write_chunk(self, filename: str, data: List):
        """写入有序块"""
        with open(filename, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(f"{item}\n")

    def _merge_chunks(self, output_file: str, num_chunks: int, num_ways: int):
        """多路归并"""
        # 打开所有块的读取器
        chunk_files = [open(self.chunks[i], 'r', encoding='utf-8') for i in range(num_chunks)]
        readers = []
        for i, cf in enumerate(chunk_files):
            line = cf.readline().strip()
            if line:
                try:
                    val = int(line)
                except ValueError:
                    val = line
                heapq.heappush(readers, (val, i, cf, line))

        with open(output_file, 'w', encoding='utf-8') as out:
            while readers:
                val, idx, cf, line = heapq.heappop(readers)
                out.write(f"{val}\n")

                next_line = cf.readline()
                if next_line:
                    next_line = next_line.strip()
                    if next_line:
                        try:
                            next_val = int(next_line)
                        except ValueError:
                            next_val = next_line
                        heapq.heappush(readers, (next_val, idx, cf, next_line))
                else:
                    cf.close()

        # 关闭所有文件
        for cf in chunk_files:
            try:
                cf.close()
            except:
                pass

    def _cleanup(self):
        """清理临时文件"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass


def sort_in_memory(arr: List) -> List:
    """简单的内存排序（用于验证）"""
    return sorted(arr)


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 外部排序演示 ===\n")

    import tempfile
    import random

    # 创建测试数据文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        input_file = f.name
        test_data = [random.randint(1, 100000) for _ in range(1000)]
        for val in test_data:
            f.write(f"{val}\n")

    print(f"生成了 {len(test_data)} 条测试数据")
    print(f"输入文件: {input_file}")

    # 使用外部排序
    sorter = ExternalSorter(chunk_size=100)
    output_file = tempfile.mktemp(suffix='_sorted.txt')

    import time
    start = time.time()
    sorter.sort_file(input_file, output_file, num_ways=4)
    ext_time = time.time() - start

    # 验证结果
    with open(output_file, 'r', encoding='utf-8') as f:
        sorted_data = [int(line.strip()) for line in f if line.strip()]

    expected = sorted(test_data)
    is_correct = sorted_data == expected

    print(f"\n排序结果: {len(sorted_data)} 条")
    print(f"正确性: {'✅ 通过' if is_correct else '❌ 失败'}")
    print(f"外部排序耗时: {ext_time*1000:.2f}ms")

    # 清理
    os.unlink(input_file)
    os.unlink(output_file)

    print("\n说明：")
    print("  - chunk_size: 每次加载进内存的数据量")
    print("  - num_ways: 多路归并的分支数")
    print("  - 实际应用中数据可能GB级别")
