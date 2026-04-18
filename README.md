# Python 算法大全 🐍

[![原仓库 Stars](https://img.shields.io/github/stars/TheAlgorithms/Python?style=flat-square&label=TheAlgorithms/Python)](https://github.com/TheAlgorithms/Python)
[![Fork Stars](https://img.shields.io/github/stars/sun-hainan/Python?style=flat-square&label=Sun-hainan/Python)](https://github.com/sun-hainan/Python)
[![Repo Size](https://img.shields.io/github/repo-size/sun-hainan/Python?style=flat-square)](https://github.com/sun-hainan/Python)
[![License](https://img.shields.io/github/license/sun-hainan/Python?style=flat-square)](LICENSE.md)

<div align="center">
  <h1>Python 算法实现 - 中文学习版</h1>
  <p>本仓库是 <a href="https://github.com/TheAlgorithms/Python">TheAlgorithms/Python</a> 的中文学习分支，所有算法均以 Python 实现，适合学习与参考。</p>
  <p>⚠️ 本仓库仅供学习目的。算法实现可能不如 Python 标准库高效，请斟酌使用。</p>
</div>

---

## 📚 算法分类目录

### 🔢 排序算法 (sorts)
| 算法 | 文件 | 说明 |
|------|------|------|
| 冒泡排序 | `bubble_sort.py` | 最基础的比较排序，O(n²) |
| 选择排序 | `selection_sort.py` | 每次选择最小元素，O(n²) |
| 插入排序 | `insertion_sort.py` | 适合小规模或近乎有序数据，O(n²) |
| 归并排序 | `merge_sort.py` | 分治思想，稳定排序，O(n log n) |
| 快速排序 | `quick_sort.py` | 原地排序，平均 O(n log n) |
| 堆排序 | `heap_sort.py` | 基于二叉堆，O(n log n) |
| 计数排序 | `counting_sort.py` | 非比较排序，适合整数，O(n+k) |
| 基数排序 | `radix_sort.py` | 按位排序，O(nk) |
| 桶排序 | `bucket_sort.py` | 分桶后再排序 |
| 希尔排序 | `shell_sort.py` | 插入排序的改进版 |
| Tim Sort | `tim_sort.py` | Python 内置排序算法 |
| 拓扑排序 | `topological_sort.py` | 有向无环图排序 |
| 其他 | ... | 详见 `sorts/` 目录 |

### 📊 数据结构 (data_structures)
```
data_structures/
├── arrays/        # 数组操作
├── binary_tree/   # 二叉树
├── disjoint_set/  # 并查集
├── hashing/       # 哈希表
├── heap/          # 堆（二叉堆、斐波那契堆）
├── kd_tree/       # K维树
├── linked_list/   # 链表（单链表、双链表）
├── queues/        # 队列
├── stacks/        # 栈
├── suffix_tree/   # 后缀树
└── trie/          # 前缀树/Trie树
```

### 🔍 搜索算法 (searches)
| 算法 | 文件 | 说明 |
|------|------|------|
| 二分搜索 | `binary_search.py` | 有序数组，O(log n) |
| 线性搜索 | `linear_search.py` | 遍历查找，O(n) |
| 跳跃搜索 | `jump_search.py` | 跳跃 + 线性，O(√n) |
| 插值搜索 | `interpolation_search.py` | 适合均匀分布数据 |
| 指数搜索 | `exponential_search.py` | O(log n) |
| 广度优先搜索 | `breadth_first_search.py` | BFS，图遍历 |
| 深度优先搜索 | `depth_first_search.py` | DFS，图遍历 |

### 📈 动态规划 (dynamic_programming)
| 问题 | 文件 | 说明 |
|------|------|------|
| 斐波那契 | `fibonacci.py` | 最基础的 DP |
| 背包问题 | `knapsack.py` | 0-1背包、完全背包 |
| 最长公共子序列 | `lcs.py` | LCS |
| 最长递增子序列 | `lis.py` | LIS |
| 编辑距离 | `edit_distance.py` | 字符串转换代价 |
| 路径计数 | `count_ways.py` | 爬楼梯问题 |

### 🌲 图算法 (graphs)
| 算法 | 文件 | 说明 |
|------|------|------|
| BFS | `breadth_first_search.py` | 广度优先遍历 |
| DFS | `depth_first_search.py` | 深度优先遍历 |
| Dijkstra | `dijkstra.py` | 单源最短路径 |
| Bellman-Ford | `bellman_ford.py` | 可处理负权边 |
| Floyd-Warshall | `floyd_warshall.py` | 全源最短路径 |
| Kruskal | `minimum_spanning_tree_kruskal.py` | 最小生成树 |
| Prim | `minimum_spanning_tree_prims.py` | 最小生成树 |
| A* | `a_star.py` | 启发式搜索 |
| Kosaraju | `scc_kosaraju.py` | 强连通分量 |
| Tarjan | `tarjans_scc.py` | 强连通分量 |

### 🔐 密码学 (ciphers)
| 算法 | 文件 | 说明 |
|------|------|------|
| Caesar | `caesar.py` | 凯撒密码 |
| Vigenere | `vigenere.py` | 维吉尼亚密码 |
| RSA | `rsa.py` | RSA 非对称加密 |
| AES | `aes.py` | 高级加密标准 |
| Hill | `hill.py` | 希尔密码 |
| 栅栏密码 | `rail_fence_cipher.py` | 栅栏密码 |
| Playfair | `playfair.py` | 普莱费尔密码 |

### 🧬 遗传算法 (genetic_algorithm)
- `basic_genetic_algorithm.py` - 基础遗传算法
- `greedy_genetic_algorithm.py` - 贪婪遗传算法

### 🧠 神经网络 (neural_network)
- `perceptron.py` - 感知机
- `曲 neural_network/` 目录

### 📐 数学运算 (maths)
| 算法 | 文件 | 说明 |
|------|------|------|
| 质数判定 | `prime_check.py` | 素数检测 |
| 最大公约数 | `gcd.py` | 欧几里得算法 |
| 阶乘 | `factorial.py` | 阶乘计算 |
| 排列组合 | `binomial_coefficient.py` | 二项式系数 |
| 矩阵乘法 | `matrix_multiplication.py` | 矩阵运算 |
| 复利/数列 | `...` | 详见 maths/ 目录 |

### 🧮 计算几何 (geometry)
- `line_segment_intersection.py` - 线段相交
- `lattice_points.py` - 格点问题
- `等` 详见 geometry/ 目录

### 🌐 网络流 (networking_flow)
| 算法 | 文件 | 说明 |
|------|------|------|
| 最大流 | `maximal_networkflow.py` | Ford-Fulkerson |
| 最小割 | `min_cut.py` | 最小切割 |
| 二分图匹配 | `bipartite_matching.py` | 二分图最大匹配 |

### 📦 其他分类
| 目录 | 内容 |
|------|------|
| `backtracking/` | 回溯算法（八皇后、数独等）|
| `bit_manipulation/` | 位运算技巧 |
| `blockchain/` | 区块链相关 |
| `boolean_algebra/` | 布尔代数 |
| `cellular_automata/` | 元胞自动机 |
| `conversions/` | 进制转换 |
| `data_compression/` | 数据压缩 |
| `divide_and_conquer/` | 分治法 |
| `electronics/` | 电子学算法 |
| `financial/` | 金融算法 |
| `fractals/` | 分形 |
| `fuzzy_logic/` | 模糊逻辑 |
| `greedy_methods/` | 贪心算法 |
| `hashes/` | 哈希算法 |
| `knapsack/` | 背包问题 |
| `machine_learning/` | 机器学习算法 |
| `physics/` | 物理模拟 |
| `project_euler/` | Project Euler 数学题 |
| `quantum/` | 量子计算 |
| `scheduling/` | 调度算法 |
| `strings/` | 字符串算法 |

---

## 🚀 快速开始

### 1. 浏览代码
直接点击上方的文件目录浏览，或克隆到本地：

```bash
git clone https://github.com/sun-hainan/Python.git
cd Python
```

### 2. 运行示例
```bash
# 运行某个算法
python sorts/bubble_sort.py

# 运行测试
python -m pytest sorts/tests/
```

### 3. 学习路径建议

```
初学者路线：
1. 排序算法 (sorts/) → 理解最基础算法思维
2. 搜索算法 (searches/) → 二分搜索必须掌握
3. 数据结构 (data_structures/) → 计算机基础
4. 动态规划 (dynamic_programming/) → 算法难点
5. 图算法 (graphs/) → 进阶必备
```

---

## 📖 学习资源

| 资源 | 链接 |
|------|------|
| 原仓库 | https://github.com/TheAlgorithms/Python |
| 算法可视化 | https://visualgo.net/ |
| 简体中文教程 | https://github.com/sun-hainan/developer-roadmap-zh-CN |

---

## 🤝 贡献指南

本仓库接受 Pull Request。如需贡献：
1. 阅读 `CONTRIBUTING.md` 了解规范
2. 遵守代码风格（使用 ruff/black）
3. 添加测试用例
4. **建议为新算法添加中文注释**

---

## 📄 License

本仓库继承自 [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python)，采用 MIT License。

---

<div align="center">
  <p>⭐ 如果对你有帮助，欢迎 Star！</p>
  <p>Made with ❤️ by <a href="https://github.com/sun-hainan">sun-hainan</a> | Based on <a href="https://github.com/TheAlgorithms">TheAlgorithms</a></p>
</div>
