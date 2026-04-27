# -*- coding: utf-8 -*-

"""

算法实现：区块链算法 / hash_chain



本文件实现 hash_chain 相关的算法功能。

"""



import hashlib

from typing import List, Optional





class HashChain:

    """哈希链"""



    def __init__(self, initial_data: str = "Genesis"):

        """

        参数：

            initial_data: 创世块数据

        """

        self.blocks = []

        self.add_block(initial_data, is_genesis=True)



    def _compute_hash(self, data: str, prev_hash: str) -> str:

        """

        计算哈希



        返回：哈希值

        """

        content = data + prev_hash

        return hashlib.sha256(content.encode()).hexdigest()



    def add_block(self, data: str, is_genesis: bool = False) -> None:

        """

        添加块



        参数：

            data: 块数据

            is_genesis: 是否是创世块

        """

        if not self.blocks:

            prev_hash = "0" * 64

        else:

            prev_hash = self.blocks[-1]['hash']



        block = {

            'data': data,

            'prev_hash': prev_hash,

            'hash': self._compute_hash(data, prev_hash),

            'index': len(self.blocks)

        }



        self.blocks.append(block)



    def verify_chain(self) -> bool:

        """

        验证链的完整性



        返回：是否有效

        """

        for i in range(1, len(self.blocks)):

            current = self.blocks[i]

            previous = self.blocks[i - 1]



            # 检查哈希

            recomputed = self._compute_hash(current['data'], previous['hash'])

            if recomputed != current['hash']:

                return False



            # 检查链接

            if current['prev_hash'] != previous['hash']:

                return False



        return True



    def tamper_block(self, index: int, new_data: str) -> None:

        """

        篡改块（用于测试验证）



        参数：

            index: 块索引

            new_data: 新数据

        """

        if 0 < index < len(self.blocks):

            self.blocks[index]['data'] = new_data

            # 注意：不重新计算哈希会导致验证失败





def hash_chain_applications():

    """Hash链应用"""

    print("=== Hash链应用 ===")

    print()

    print("1. 区块链")

    print("   - 比特币使用Hash链")

    print("   - 每个块包含前一个哈希")

    print()

    print("2. Git版本控制")

    print("   - 每个提交有前一个的哈希")

    print("   - 保证历史不可篡改")

    print()

    print("3. 证书透明度")

    print("   - CT日志使用Hash链")

    print("   - 防止证书伪造")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Hash链测试 ===\n")



    # 创建链

    chain = HashChain("Genesis Block")



    # 添加块

    chain.add_block("Alice pays Bob 10 BTC")

    chain.add_block("Bob pays Charlie 5 BTC")

    chain.add_block("Charlie pays Dave 3 BTC")



    print(f"链长度: {len(chain.blocks)}")

    print()



    # 显示链

    print("区块链：")

    for block in chain.blocks:

        print(f"  块 {block['index']}: {block['data'][:30]}...")

        print(f"    哈希: {block['hash'][:20]}...")

        print(f"    前向: {block['prev_hash'][:20]}...")



    print()



    # 验证

    is_valid = chain.verify_chain()

    print(f"链有效: {'✅ 是' if is_valid else '❌ 否'}")



    # 篡改测试

    chain.tamper_block(1, "Alice pays Bob 100 BTC")

    is_valid_after = chain.verify_chain()

    print(f"篡改后有效: {'是' if is_valid_after else '❌ 否 (检测到篡改!)'}")



    print()

    hash_chain_applications()



    print()

    print("说明：")

    print("  - Hash链是区块链的基础")

    print("  - 每个块包含前一个哈希")

    print("  - 篡改任何块都会被检测")

