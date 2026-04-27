# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / k_mer_counting



本文件实现 k_mer_counting 相关的算法功能。

"""



from collections import Counter

from typing import Counter as CounterType





def get_kmers(sequence: str, k: int) -> CounterType[str]:

    """

    获取序列的所有k-mer及其计数



    参数：

        sequence: 输入序列（DNA/RNA/蛋白质/文本）

        k: k-mer长度



    返回：Counter {kmer: count}

    """

    if k <= 0 or k > len(sequence):

        return Counter()



    kmers = []

    for i in range(len(sequence) - k + 1):

        kmer = sequence[i:i+k]

        kmers.append(kmer)



    return Counter(kmers)





def kmer_similarity(seq1: str, seq2: str, k: int) -> float:

    """

    基于k-mer的序列相似度（Jaccard相似度）



    公式：|K1 ∩ K2| / |K1 ∪ K2|

    """

    kmers1 = set(get_kmers(seq1, k).keys())

    kmers2 = set(get_kmers(seq2, k).keys())



    intersection = len(kmers1 & kmers2)

    union = len(kmers1 | kmers2)



    return intersection / union if union > 0 else 0.0





def gc_content(sequence: str) -> float:

    """计算GC含量（DNA序列中G和C的比例）"""

    gc = sum(1 for c in sequence if c in 'GCgc')

    return gc / len(sequence) if sequence else 0.0





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== K-mer计数测试 ===\n")



    dna = "AGCTAGCTAGCT"



    print(f"DNA序列: {dna}")

    print(f"长度: {len(dna)}")



    for k in [2, 3, 4]:

        kmers = get_kmers(dna, k)

        print(f"\nk={k} 的k-mer:")

        for kmer, count in kmers.most_common():

            print(f"  {kmer}: {count}次")



    # 相似度对比

    print("\n--- 序列相似度对比 ---")

    seq1 = "AGCTAGCTAGCT"

    seq2 = "AGCTAGCTAGCT"  # 完全相同

    seq3 = "GCATGCATGCAT"  # 部分不同



    for k in [2, 3]:

        sim_12 = kmer_similarity(seq1, seq2, k)

        sim_13 = kmer_similarity(seq1, seq3, k)

        print(f"k={k}: seq1-seq2={sim_12:.3f}, seq1-seq3={sim_13:.3f}")



    print("\n说明：")

    print("  - k-mer用于快速估计序列相似性")

    print("  - 常用于基因组组装、宏基因组分析")

    print("  - k通常选择奇数以避免回文问题")

