# -*- coding: utf-8 -*-

"""

算法实现：编码理论 / turbo_code



本文件实现 turbo_code 相关的算法功能。

"""



import random

from typing import List, Tuple





def random_interleaver(size: int, seed: int = 42) -> List[int]:

    """

    创建随机交织器

    

    Args:

        size: 交织器大小

        seed: 随机种子

    

    Returns:

        交织映射

    """

    random.seed(seed)

    indices = list(range(size))

    random.shuffle(indices)

    return indices





def turbo_encode(data: List[int], interleaver: List[int] = None) -> Tuple[List[int], List[int], List[int]]:

    """

    Turbo码编码

    

    Args:

        data: 信息位

        interleaver: 交织器

    

    Returns:

        (系统位, 校验位1, 校验位2)

    """

    n = len(data)

    

    if interleaver is None:

        interleaver = random_interleaver(n)

    

    # 系统位

    systematic = data.copy()

    

    # 第一个卷积编码器

    parity1 = []

    state = 0

    for bit in data:

        # 简单递归系统卷积码

        out_bit = bit ^ state

        parity1.append(out_bit)

        state = (state + bit) % 2

    

    # 交织后的数据

    interleaved_data = [data[interleaver[i]] for i in range(n)]

    

    # 第二个卷积编码器

    parity2 = []

    state = 0

    for bit in interleaved_data:

        out_bit = bit ^ state

        parity2.append(out_bit)

        state = (state + bit) % 2

    

    return systematic, parity1, parity2





def bcjr_decode(llrs: List[float], parity: List[int], 

                prior: float = 0.0) -> List[float]:

    """

    BCJR译码算法(简化版)

    

    Args:

        llrs: 输入对数似然比

        parity: 校验位

        prior: 先验概率

    

    Returns:

        输出的LLRs

    """

    n = len(llrs)

    output = [0.0] * n

    

    # 简化:使用线性近似

    for i in range(n):

        # 计算软输出

        if llrs[i] > 0:

            output[i] = prior + 0.5 * llrs[i]

        else:

            output[i] = prior + 0.5 * llrs[i]

    

    return output





def turbo_decode(systematic: List[int], parity1: List[int], parity2: List[int],

                num_iterations: int = 10) -> List[int]:

    """

    Turbo码迭代译码

    

    Args:

        systematic: 系统位

        parity1: 第一组校验位

        parity2: 第二组校验位

        num_iterations: 迭代次数

    

    Returns:

        译码后的数据位

    """

    n = len(systematic)

    

    # 初始化LLRs

    llrs = [0.0] * n

    

    # 信道置信度

    channel_llr = 2.0

    

    # 先验

    prior1 = [0.0] * n

    prior2 = [0.0] * n

    

    extrinsic1 = [0.0] * n

    extrinsic2 = [0.0] * n

    

    for iteration in range(num_iterations):

        # 解码器1

        decoder1_input = [systematic[i] * channel_llr + prior1[i] for i in range(n)]

        

        for i in range(n):

            if systematic[i] == 1:

                decoder1_input[i] += 1.0

            else:

                decoder1_input[i] -= 1.0

        

        # BCJR译码(简化)

        decoder1_output = bcjr_decode(decoder1_input, parity1)

        

        # 提取外信息

        for i in range(n):

            extrinsic1[i] = decoder1_output[i] - prior1[i] - systematic[i] * channel_llr

        

        # 交织

        interleaver = random_interleaver(n)

        interleaved_ext1 = [extrinsic1[interleaver[i]] for i in range(n)]

        

        # 先验2 = 外信息1

        prior2 = interleaved_ext1.copy()

        

        # 解码器2

        decoder2_input = [systematic[i] * channel_llr + prior2[i] for i in range(n)]

        

        for i in range(n):

            if systematic[i] == 1:

                decoder2_input[i] += 1.0

            else:

                decoder2_input[i] -= 1.0

        

        decoder2_output = bcjr_decode(decoder2_input, parity2)

        

        # 提取外信息2

        for i in range(n):

            extrinsic2[i] = decoder2_output[i] - prior2[i] - systematic[i] * channel_llr

        

        # 反交织

        deinterleaver = [0] * n

        for i, idx in enumerate(interleaver):

            deinterleaver[idx] = i

        

        interleaved_ext2 = [extrinsic2[deinterleaver[i]] for i in range(n)]

        

        # 先验1 = 外信息2

        prior1 = interleaved_ext2.copy()

        

        # 决策

        if iteration == num_iterations - 1:

            final_llrs = [decoder2_output[i] + prior2[i] for i in range(n)]

            return [1 if llr > 0 else 0 for llr in final_llrs]

    

    return [1 if llr > 0 else 0 for llr in llrs]





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本编码

    print("测试1 - Turbo编码:")

    data = [1, 0, 1, 1, 0, 0, 1, 0]

    

    systematic, parity1, parity2 = turbo_encode(data)

    

    print(f"  信息位: {data}")

    print(f"  系统位: {systematic}")

    print(f"  校验位1: {parity1}")

    print(f"  校验位2: {parity2}")

    

    # 测试2: 译码

    print("\n测试2 - Turbo译码:")

    decoded = turbo_decode(systematic, parity1, parity2)

    

    print(f"  原始: {data}")

    print(f"  译码: {decoded}")

    print(f"  正确: {data == decoded}")

    

    # 测试3: 加噪声

    print("\n测试3 - 加噪声译码:")

    noisy_systematic = systematic.copy()

    noisy_parity1 = parity1.copy()

    noisy_parity2 = parity2.copy()

    

    # 随机翻转一些位

    random.seed(42)

    for i in range(len(systematic)):

        if random.random() < 0.1:  # 10%错误率

            noisy_systematic[i] ^= 1

    

    for i in range(len(parity1)):

        if random.random() < 0.1:

            noisy_parity1[i] ^= 1

        if random.random() < 0.1:

            noisy_parity2[i] ^= 1

    

    decoded_noisy = turbo_decode(noisy_systematic, noisy_parity1, noisy_parity2)

    

    errors = sum(1 for i in range(len(data)) if data[i] != decoded_noisy[i])

    print(f"  10%噪声后译码错误: {errors}/{len(data)}")

    

    # 测试4: 迭代次数影响

    print("\n测试4 - 迭代次数影响:")

    for num_iter in [1, 5, 10, 20]:

        decoded_iter = turbo_decode(noisy_systematic, noisy_parity1, noisy_parity2, num_iter)

        errors = sum(1 for i in range(len(data)) if data[i] != decoded_iter[i])

        print(f"  {num_iter}次迭代: {errors}个错误")

    

    # 测试5: 较大数据

    print("\n测试5 - 较大数据:")

    random.seed(42)

    large_data = [random.randint(0, 1) for _ in range(1000)]

    

    systematic_l, parity1_l, parity2_l = turbo_encode(large_data)

    

    # 添加噪声

    noisy_sys = systematic_l.copy()

    noisy_par1 = parity1_l.copy()

    noisy_par2 = parity2_l.copy()

    

    for i in range(len(large_data)):

        if random.random() < 0.05:

            noisy_sys[i] ^= 1

    

    decoded_large = turbo_decode(noisy_sys, noisy_par1, noisy_par2, num_iterations=10)

    

    errors = sum(1 for i in range(len(large_data)) if large_data[i] != decoded_large[i])

    print(f"  1000位数据, 5%噪声, 10次迭代: {errors}个错误")

    print(f"  误码率: {errors/len(large_data):.4f}")

    

    print("\n所有测试完成!")

