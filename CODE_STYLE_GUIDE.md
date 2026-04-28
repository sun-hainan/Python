# 算法代码规范
> 本规范适用于 `计算机算法/` 目录下所有Python文件

---

## 1. 文件结构

```
# -*- coding: utf-8 -*-
"""
文件名
==========================================

【算法名称】
【一句话描述核心原理】

【时间复杂度】
【空间复杂度】

【应用场景】
【何时使用】
"""

import ...

# ========================================
# 第1部分：核心类/函数
# ========================================

class Algorithm:
    """
    类名

    【类说明】
    【关键属性】
    """
    
    def method(self, param: type) -> return_type:
        """
        方法名

        【功能描述】

        【参数】
        - param: 参数说明

        【返回】
        - 返回值说明
        """
        # 第1步：操作描述
        ...
        # 第2步：操作描述
        ...

# ========================================
# 第2部分：辅助函数
# ========================================

def helper_function():
    """简短说明"""
    pass

# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("算法名称 - 测试")
    print("=" * 50)

    # 测试1：基本功能
    print("\n【测试1】测试名称")
    # 测试代码

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
```

---

## 2. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `BinarySearchTree` |
| 函数名 | snake_case | `binary_search` |
| 变量名 | snake_case | `node_count` |
| 常量 | UPPER_SNAKE | `MAX_SIZE` |
| 私有属性 | _前缀 | `_cache` |
| 类型变量 | PascalCase | `T`, `NodeType` |

---

## 3. 注释规范

### 3.1 文件头注释
```python
"""
文件名
==========================================

【算法原理一句话】
【时间复杂度】O(n log n)
【空间复杂度】O(n)
"""
```

### 3.2 类/函数docstring
```python
class Algorithm:
    """
    算法类名称

    【核心思想】
    2-3句话描述核心原理

    【参数】
    - param1: 参数1说明
    - param2: 参数2说明

    【返回】
    - 返回值说明
    """
```

### 3.3 逐行注释
```python
# -------- 初始化阶段 --------
# 创建根节点，值为None表示空树
self.root = None
# 初始化节点计数
self.size = 0

# -------- 核心操作 --------
# 第1步：找到插入位置
node = self._find_position(value)
```

---

## 4. 示例模板

### 4.1 数据结构类
```python
"""
栈（Stack）
==========================================

【算法原理】
后进先出（LIFO）的线性数据结构。

【时间复杂度】
- push: O(1)
- pop: O(1)
- peek: O(1)

【空间复杂度】O(n)

【应用场景】
- 函数调用栈
- 表达式求值
- 括号匹配
"""

class Stack:
    def __init__(self):
        self._items = []

    def push(self, item) -> None:
        """压栈"""
        self._items.append(item)

    def pop(self):
        """弹栈"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self._items.pop()

    def is_empty(self) -> bool:
        """判断是否为空"""
        return len(self._items) == 0
```

### 4.2 算法类
```python
"""
二分查找（Binary Search）
==========================================

【算法原理】
在有序数组中，每次将搜索范围缩小一半。

【时间复杂度】O(log n)
【空间复杂度】O(1)

【应用场景】
- 有序数组查找
- 单调函数求根
- 搜索空间二分
"""

def binary_search(arr: list, target) -> int:
    """
    二分查找

    【参数】
    - arr: 有序列表
    - target: 目标值

    【返回】
    - 目标索引，若不存在返回-1
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        # -------- 计算中点 --------
        # 防止(left + right)溢出
        mid = left + (right - left) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            # -------- 右半部分搜索 --------
            left = mid + 1
        else:
            # -------- 左半部分搜索 --------
            right = mid - 1

    return -1
```

---

## 5. 禁止事项

| 禁止 | 正确做法 |
|------|----------|
| `# TODO: 请补充` | 删除或填写完整 |
| `"""空docstring"""` | 填写内容或删除docstring |
| `pass  # 占位` | 填写实际实现 |
| 命名 `tmp1, tmp2` | 改为有意义的名称 |
| 行长度 > 120字符 | 拆分为多行 |

---

## 6. 测试代码规范

```python
if __name__ == "__main__":
    print("=" * 50)
    print("算法名称 - 测试")
    print("=" * 50)

    # 测试分组
    print("\n【测试1】基本功能")
    # Arrange
    # Act
    # Assert

    print("\n【测试2】边界情况")
    # ...

    # 性能测试（可选）
    import time
    start = time.time()
    # ...执行...
    print(f"\n性能: {(time.time() - start)*1000:.2f}ms")

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
```

---

## 7. 提交前检查清单

- [ ] 文件头docstring完整
- [ ] 所有类和公共函数有docstring
- [ ] 关键步骤有中文注释
- [ ] 无TODO/占位符
- [ ] `if __name__ == "__main__":` 测试代码存在
- [ ] 变量命名有意义
- [ ] 行长度 < 120字符
