# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / genome_assembly



本文件实现 genome_assembly 相关的算法功能。

"""



def eulerian_path_finder(

    graph: Dict[str, List[str]],

    multiplicity: Dict[str, int]

) -> List[str]:

    """

    寻找欧拉路径进行组装



    定理：基因组组装问题等价于在De Bruijn图中找欧拉路径



    参数:

        graph: De Bruijn图

        multiplicity: k-mer出现次数



    返回:

        组装序列

    """

    # 计算入度和出度

    in_degree = defaultdict(int)

    out_degree = defaultdict(int)



    for node, neighbors in graph.items():

        out_degree[node] = len(neighbors)

        for neighbor in neighbors:

            in_degree[neighbor] += 1



    # 找起点（出度=入度+1）或普通点（出度=入度）

    start_nodes = []

    for node in set(list(graph.keys()) + [n for neighbors in graph.values() for n in neighbors]):

        if out_degree[node] - in_degree[node] == 1:

            start_nodes.append(node)

        elif out_degree[node] > 0 and in_degree[node] == 0:

            start_nodes.append(node)



    if not start_nodes:

        start_nodes = list(graph.keys())[:1]



    # Hierholzer算法找欧拉路径

    def hierholzer(start):

        stack = [start]

        path = []

        while stack:

            v = stack[-1]

            if graph.get(v, []):

                w = graph[v].pop()

                stack.append(w)

            else:

                path.append(stack.pop())

        return path[::-1]



    euler_path = hierholzer(start_nodes[0])



    # 转换为基因组序列

    if len(euler_path) <= 1:

        return euler_path[0] if euler_path else ''



    genome = euler_path[0]

    for kmer in euler_path[1:]:

        genome += kmer[-1]



    return genome





def overlap_layout_consensus(

    reads: List[str],

    min_overlap: int = 20

) -> str:

    """

    Overlap-Layout-Consensus组装



    1. 计算overlap

    2. 构建layout图

    3. 找路径获取共识序列



    参数:

        reads: 测序reads

        min_overlap: 最小重叠长度



    返回:

        组装序列

    """

    n = len(reads)

    if n == 0:

        return ''

    if n == 1:

        return reads[0]



    # 计算重叠

    overlaps = {}

    for i in range(n):

        for j in range(n):

            if i != j:

                overlap_len = compute_overlap(reads[i], reads[j], min_overlap)

                if overlap_len >= min_overlap:

                    overlaps[(i, j)] = overlap_len



    # 构建重叠图

    # 简化：使用最长路径

    order = []

    used = set()

    current = 0

    order.append(current)

    used.add(current)



    while len(order) < n:

        best_next = -1

        best_overlap = 0

        for j in range(n):

            if j not in used and (current, j) in overlaps:

                if overlaps[(current, j)] > best_overlap:

                    best_overlap = overlaps[(current, j)]

                    best_next = j



        if best_next < 0:

            break



        order.append(best_next)

        used.add(best_next)

        current = best_next



    # 构建共识

    consensus = reads[order[0]]

    for i in range(1, len(order)):

        idx = order[i]

        overlap = overlaps.get((order[i-1], idx), 0)

        consensus += reads[idx][overlap:]



    return consensus





def compute_overlap(s1: str, s2: str, min_overlap: int) -> int:

    """

    计算两个序列的最大重叠长度



    参数:

        s1, s2: 序列

        min_overlap: 最小重叠



    返回:

        最大重叠长度

    """

    max_ol = min(len(s1), len(s2))

    for ol in range(max_ol, min_overlap - 1, -1):

        if s1.endswith(s2[:ol]):

            return ol

    return 0





def error_correction(reads: List[str], k: int = 21) -> List[str]:

    """

    测序错误校正（基于k-mer频数）



    低频k-mer可能是错误



    参数:

        reads: 原始reads

        k: k-mer大小

        threshold: 频数阈值



    返回:

        校正后的reads

    """

    # 统计k-mer频数

    kmer_counts = defaultdict(int)

    for read in reads:

        for i in range(len(read) - k + 1):

            kmer = read[i:i+k]

            kmer_counts[kmer] += 1



    # 校正reads

    threshold = 2

    corrected = []



    for read in reads:

        new_read = list(read)

        for i in range(len(read) - k + 1):

            kmer = read[i:i+k]

            if kmer_counts[kmer] < threshold:

                # 尝试修正

                for base in 'ACGT':

                    if base != kmer[0]:

                        new_kmer = base + kmer[1:]

                        if kmer_counts.get(new_kmer, 0) > threshold:

                            new_read[i] = base

                            break

        corrected.append(''.join(new_read))



    return corrected





def assembly_quality(assembled: str, true_genome: str) -> Dict[str, float]:

    """

    评估组装质量



    参数:

        assembled: 组装结果

        true_genome: 真实基因组



    返回:

        质量指标

    """

    # 简化的N50计算

    contigs = assembled.split('N')

    contig_lengths = [len(c) for c in contigs if len(c) > 0]

    contig_lengths.sort(reverse=True)



    total = sum(contig_lengths)

    n50 = 0

    cumsum = 0

    for length in contig_lengths:

        cumsum += length

        if cumsum >= total * 0.5:

            n50 = length

            break



    # 识别率

    if true_genome:

        coverage = 0

        for i in range(len(true_genome) - 10):

            if true_genome[i:i+10] in assembled:

                coverage += 1

        coverage /= len(true_genome)



        identity = sum(1 for a, b in zip(assembled, true_genome) if a == b) / max(len(assembled), len(true_genome))

    else:

        coverage = 0

        identity = 0



    return {

        'n50': n50,

        'total_length': total,

        'num_contigs': len(contig_lengths),

        'coverage': coverage,

        'identity': identity,

    }





if __name__ == '__main__':

    print('=== 基因组组装测试 ===')



    # 测试1: De Bruijn图

    print('\n--- 测试1: De Bruijn图 ---')

    reads = [

        'ATCGATCGA',

        'TCGATCGT',

        'ATCGTACG',

        'GATCGTAC',

    ]

    k = 3

    graph, mult = build_debruijn_graph(reads, k)

    print(f'  k-mer大小: {k}')

    print(f'  节点数: {len(graph)}')

    print(f'  边数: {sum(len(v) for v in graph.values())}')



    # 测试2: 欧拉路径组装

    print('\n--- 测试2: 欧拉路径组装 ---')

    genome = eulerian_path_finder(graph, mult)

    print(f'  组装序列: {genome}')



    # 测试3: OLC组装

    print('\n--- 测试3: Overlap-Layout-Consensus ---')

    olc_reads = [

        'ATCGATCGAT',

        'CGATCGATC',

        'GATCGAT',

    ]

    assembled = overlap_layout_consensus(olc_reads, min_overlap=5)

    print(f'  原始reads: {olc_reads}')

    print(f'  组装: {assembled}')



    # 测试4: 错误校正

    print('\n--- 测试4: 测序错误校正 ---')

    noisy_reads = [

        'ATCGATCGT',

        'ATCAATCGT',  # 有错误

        'TCGATCGAT',

    ]

    corrected = error_correction(noisy_reads, k=3)

    for orig, corr in zip(noisy_reads, corrected):

        print(f'  {orig} -> {corr}')



    # 测试5: 组装质量

    print('\n--- 测试5: 组装质量评估 ---')

    assembled = 'ATCGATCGATCGTACGAT'

    true = 'ATCGATCGATCGTACGAT'

    quality = assembly_quality(assembled, true)

    print(f'  组装序列: {assembled}')

    print(f'  质量指标: {quality}')

