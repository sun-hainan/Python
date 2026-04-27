# 计算机算法库

> 全面、系统、持续更新的算法学习与实现仓库。覆盖从基础数据结构到前沿AI/安全/系统领域的~2800+个算法实现。

---

## 目录结构

### 基础与数据结构

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 01 | 排序与搜索 | 各类排序算法、二分查找及相关扩展 |
| 02 | 数据结构 | 基础数据结构：栈/队列/链表/哈希表等 |
| 03 | 字符串算法 | KMP/AC自动机/后缀数组/编辑距离等 |
| 08 | 位运算 | 位操作技巧/Bitmap/BloomFilter/CRC |
| 10 | 高级数据结构 | 高级结构：线段树/平衡树/跳表/图结构 |
| 11 | 计算几何 | 凸包/旋转卡壳/Voronoi/三角剖分 |
| 19 | 代数算法 | 多项式/矩阵分解/LU-QR/有限域 |
| 27 | 整数与FFT | 大数乘法/FFT/数论算法 |

### 算法范式

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 04 | 图算法 | BFS/DFS/Dijkstra/并查集/拓扑排序 |
| 05 | 动态规划 | 经典DP/状态压缩/树形DP/区间DP |
| 06 | 网络流与匹配 | 最大流/二分匹配/费用流/Edmonds Blossom |
| 07 | 贪心与分治 | 贪心策略/分治思想/归约 |
| 71 | 约束求解 | SAT求解器/DPLL/CDCL/WalkSAT/AC-3 |
| 72 | 组合优化 | TSP/装箱/调度/近似算法 |
| 86 | 近似算法 | PTAS/FPTAS/随机近似/次模优化 |
| 64 | 次线性算法 | Skiplist/LFU/K-Server/流式算法 |

### 理论计算机科学

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 12 | 密码学与安全 | 对称加密/非对称加密/哈希/数字签名 |
| 14 | 信息论 | 香农熵/互信息/信道容量/Turbo/LDPC |
| 15 | 操作系统与调度 | CFS/实时调度/内存管理/同步原语 |
| 20 | 形式语言与自动机 | NFA→DFA/泵引理/CYK/LL/LR分析器 |
| 22 | 分布式算法 | Raft/Paxos/Gossip/向量时钟/2PC |
| 28 | 博弈论 | Minimax/Alpha-Beta/纳什均衡 |
| 73 | 计算复杂性理论 | 时间层次/P≠NP/PCP/BPP/IP=PSPACE |
| 31 | 参数算法 | FPT/核化/树宽/Branch-and-Bound |
| 74 | 缓存无关算法 | Cache-Oblivious/van Emde Boas/BFPRT |

### 人工智能与机器学习

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 09 | 机器学习 | 监督/无监督/EM/GMM/HMM/CRF/聚类 |
| 38 | 图神经网络 | GCN/GAT/GraphSAGE/GIN/知识图谱嵌入 |
| 47 | 对抗机器学习 | FGSM/PGD/C&W攻击/随机平滑/对抗训练 |
| 52 | 强化学习 | DQN/PPO/A3C/MCTS/模型预测控制 |
| 56 | 模型压缩完整版 | 量化/剪枝/蒸馏/NAS/轻量化网络 |
| 62 | 时间序列分析 | ARIMA/GARCH/DTW/变点检测/卡尔曼 |
| 78 | 联邦学习 | FedAvg/FedProx/差分隐私/MPC聚合 |
| 25 | 深度学习核心算法 | 反向传播/优化器/BatchNorm/Attention |
| 37 | 因果推断算法 | PC/FCI/GES/do-calculus/因果森林 |
| 67 | 知识图谱深度 | TransE/RotatE/CompGCN/KBQA/实体对齐 |

### 安全与隐私

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 30 | 压缩感知 | RIP/CoSaMP/IHT/AMP/TV最小化 |
| 32 | 可信执行环境 | SGX/TrustZone/远程认证/TEE |
| 34 | 可验证计算 | SNARK/STARK/PCP/VRF/TEE证明 |
| 35 | 同态加密 | Paillier/BFV/CKKS/FHEW/TFHE |
| 36 | 后量子密码学 | LWE/Ring-LWE/Kyber/McEliece/SPHINCS+ |
| 44 | 安全多方计算 | GMW/混淆电路/秘密共享/OT |
| 46 | 密码学协议 | DH/SRP/Pedersen/零知识证明/PIR |
| 48 | 局部可解码码 | Reed-Muller/BCH LDC/Goldreich-Levin |
| 49 | 差分隐私 | Laplace/Gaussian机制/隐私预算/PATE |
| 90 | 隐私计算 | zk-SNARK/Groth16/PLONK/差分隐私/联邦学习 |

### 系统与底层

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 16 | GPU并行算法 | CUDA/并行归约/前缀和/矩阵乘法/排序 |
| 17 | 计算机体系结构 | 分支预测/Tomasulo/MESI/TLB/原子操作 |
| 51 | 并行算法 | Fork-Join/并行归约/scan/Bitonic Sort |
| 53 | 形式验证 | BDD/OBDD/CTL/LTL模型检查/抽象解释 |
| 57 | 操作系统内核 | CFS/Buddy-Slab/COW/VFS/ext4/RCU/OOM |
| 58 | 数据库内核 | 查询优化/Join算法/MVCC/ARIES/列式存储 |
| 76 | 编译器优化 | 活跃分析/寄存器分配/窥孔优化/循环变换 |
| 77 | 编译器内核 | Lexer/Parser/SSA/数据流/Pass架构 |
| 81 | 计算机体系结构 | （基础方向） |
| 83 | 计算机网络算法 | TCP-CUBIC/BBR/QUIC/HTTP2/SDN/DCTCP |

### 图形与信号

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 18 | 信号与图像 | 小波/卡尔曼/FFT/形态学/SIFT/视频压缩 |
| 82 | 计算机图形学 | 光线追踪/BVH/细分曲面/PBR/Deferred Shading |
| 65 | 物理仿真 | 刚体/流体SPH/四元数/积分器/碰撞检测 |

### 应用领域

| 编号 | 目录 | 说明 |
|:---:|------|------|
| 21 | 量子计算 | Shor/Grover/QFT/量子纠错/量子游走 |
| 23 | 区块链算法 | PoW/PoS/Merkle/闪电网络/跨链 |
| 26 | 网页与编程 | 正则/URL解析/JSON处理/ORM |
| 33 | 可视化 | 图形化算法演示 |
| 39 | 在线算法 | Skiplist/LFU/K-Server/FTL/流式统计 |
| 41 | 多智能体系统 | QMIX/COMA/共识/编队/联邦多智能体 |
| 42 | 多目标优化 | NSGA-II/III/MOEA/D/SPEA2/Hypervolume |
| 43 | 多臂老虎机 | UCB/Thompson/EXP3/LinUCB/PAC |
| 50 | 差异理论 | Myers diff/LCS/补丁生成/三路合并 |
| 55 | 推荐系统 | 协同过滤/SVD/DeepFM/序列推荐/ bandits |
| 59 | 数据挖掘 | K-means/FP-Growth/PageRank/LDA |
| 60 | 数据流算法 | Flajolet-Martin/Count-Min/HyperLogLog |
| 63 | 生物信息学 | 序列比对/分子对接/蛋白质折叠/系统生物学 |
| 66 | 知识图谱深度 | TransE/RotatE/TuckER/KBQA/实体对齐 |
| 79 | 自然语言处理 | 分词/HMM/CRF/TF-IDF/依存句法 |
| 85 | 运筹学 | 单纯形/整数规划/Benders/列生成/VRP |
| 88 | 金融算法 | Black-Scholes/Greeks/Monte Carlo/VaR/GARCH |
| 89 | 随机算法 | 随机化算法/概率分析/概率数据结构 |
| 87 | 量子机器学习 | HHL/qSVM/QAOA/VQE/量子PCA |
| 13 | 数学基础 | 数论/概率统计/线性代数/组合数学 |
| 54 | 性质测试 | 图性质测试/数组性质测试/亚线性检测 |
| 61 | 数据流算法 | 数据流统计/滑动窗口/指数直方图 |

---

## 文件规范

所有算法文件均遵循以下规范：

- ✅ **顶部中文docstring**：说明算法功能与核心思想
- ✅ **逐行中文注释**：关键代码行有中文解释
- ✅ **英文变量名**：避免中文变量名
- ✅ **`if __name__ == "__main__":`**：附有可运行的测试代码
- ✅ **真实可运行**：无伪代码，每文件50-150行

---

## 规模统计

| 指标 | 数值 |
|------|------|
| 总目录数 | ~92 |
| 总文件数 | ~2800+ |
| 覆盖率 | 80+算法方向 |

---

## 贡献指南

### 文件命名
- 通用算法：`algorithm_name.py`（英文小写+下划线）
- 变体算法：`algorithm_name_variant.py`
- 题目类：`descriptive_name.py`

### 代码规范
- 模块级docstring：中文，简洁说明算法
- 关键行注释：中文，解释"为什么"而非"是什么"
- 变量名：英文，无需拼音
- 测试：`if __name__ == "__main__":` 块，展示算法效果

### 目录归属
- 不确定归属 → 发散到最相关的已有目录
- 跨领域算法 → 归属核心算法方向
- 新方向 → 新建目录（中文命名）
