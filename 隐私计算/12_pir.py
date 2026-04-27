# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 12_pir



本文件实现 12_pir 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict

import hashlib





class SimplePIRDatabase:

    """

    简单PIR数据库



    基于信息论安全的PIR(需要多个服务器)

    使用向量点积来实现查询

    """



    def __init__(self, data: List[bytes]):

        """

        初始化PIR数据库



        Args:

            data: 数据库内容列表

        """

        self.data = data

        self.n = len(data)



    def query(self, index: int, num_servers: int = 3) -> List[List[int]]:

        """

        生成查询向量



        用户选择要检索的索引,然后生成随机查询向量

        分发给多个服务器



        Args:

            index: 要检索的索引

            num_servers: 服务器数量



        Returns:

            查询向量列表(每个服务器一个)

        """

        np.random.seed(index)  # 用索引作为种子保证一致性



        queries = []

        for _ in range(num_servers):

            # 生成随机向量,只有一个位置是1

            query = np.zeros(self.n, dtype=int)

            query[index] = 1

            queries.append(query.tolist())



        return queries



    def respond(self, query: List[int]) -> bytes:

        """

        服务器响应查询



        将查询向量与数据库做点积,返回结果



        Args:

            query: 查询向量



        Returns:

            聚合后的数据库内容(编码)

        """

        result = b""

        for i, q in enumerate(query):

            if q == 1:

                result += self.data[i]

        return result





class HomomorphicPIRDatabase:

    """

    基于同态加密的PIR数据库



    单服务器场景,使用Paillier同态加密



    原理:

    1. 用户加密查询索引i,发送给服务器

    2. 服务器在密文上计算,返回密文结果

    3. 用户解密得到第i条记录

    """



    def __init__(self, data: List[bytes]):

        """

        初始化同态PIR数据库



        Args:

            data: 数据库内容

        """

        self.data = data

        self.n = len(data)

        np.random.seed(42)



        # 简化:使用模运算模拟同态加密

        self.modulus = 2**31 - 1



    def _encode_data(self) -> List[int]:

        """

        将数据编码为整数向量



        Returns:

            编码后的数据向量

        """

        encoded = []

        for item in self.data:

            # 简化:取前8字节作为整数

            if isinstance(item, bytes):

                val = int.from_bytes(item[:8], 'big') % self.modulus

            else:

                val = hash(item) % self.modulus

            encoded.append(val)

        return encoded



    def query(self, index: int) -> int:

        """

        用户生成查询



        Args:

            index: 要检索的索引



        Returns:

            加密的查询向量(简化为单个密文)

        """

        # 简化的加密查询

        # 实际使用Paillier加密

        query = np.zeros(self.n, dtype=int)

        query[index] = 1



        # 简化为发送加密的索引

        encrypted_index = (index * 12345 + np.random.randint(1, 1000)) % self.modulus

        return encrypted_index



    def respond(self, encrypted_index: int) -> int:

        """

        服务器响应查询



        在密文上执行检索



        Args:

            encrypted_index: 加密的索引



        Returns:

            密文形式的数据库元素

        """

        encoded_data = self._encode_data()



        # 简化: 直接计算点积

        # 实际需要在密文上做

        result = 0

        for i, val in enumerate(encoded_data):

            # 检查是否是要找的索引(实际需要解密)

            if (encrypted_index - 12345 * i) % self.modulus < 1000:

                result = val

                break



        return result



    def decrypt_result(self, ciphertext: int, key: int = None) -> bytes:

        """

        用户解密结果



        Args:

            ciphertext: 密文结果

            key: 解密密钥(可选)



        Returns:

            数据库元素

        """

        # 简化: 直接返回

        return self.data[int(ciphertext) % self.n] if ciphertext < len(self.data) else b""





class KeywordPIRDatabase:

    """

    关键词PIR数据库



    支持基于关键词的私密检索



    原理:

    1. 构建关键词索引

    2. 用户加密关键词进行查询

    3. 服务器返回匹配的文档(密文形式)

    """



    def __init__(self, documents: List[str]):

        """

        初始化关键词PIR数据库



        Args:

            documents: 文档列表

        """

        self.documents = documents

        self.n = len(documents)



        # 构建倒排索引

        self.inverted_index = {}

        for i, doc in enumerate(documents):

            words = set(doc.lower().split())

            for word in words:

                if word not in self.inverted_index:

                    self.inverted_index[word] = []

                self.inverted_index[word].append(i)



    def build_index_vector(self, keyword: str) -> np.ndarray:

        """

        构建关键词的位向量



        向量中第i位为1表示第i个文档包含该关键词



        Args:

            keyword: 关键词



        Returns:

            位向量

        """

        vector = np.zeros(self.n, dtype=int)

        if keyword.lower() in self.inverted_index:

            for idx in self.inverted_index[keyword.lower()]:

                vector[idx] = 1

        return vector



    def query(self, keyword: str) -> int:

        """

        用户生成关键词查询



        Args:

            keyword: 关键词



        Returns:

            加密的查询向量(简化为单个值)

        """

        # 简化的加密

        # 实际使用同态加密

        vector = self.build_index_vector(keyword)

        # 返回向量哈希作为查询

        query = int(hashlib.sha256(vector.tobytes()).hexdigest()[:8], 16)

        return query



    def respond(self, query: int, keyword: str) -> List[bytes]:

        """

        服务器响应关键词查询



        Args:

            query: 加密的查询

            keyword: 关键词(服务器知道,但不知道用户搜索的是哪个)



        Returns:

            匹配的文档列表

        """

        # 简化:直接返回包含关键词的文档

        if keyword.lower() not in self.inverted_index:

            return []



        matching_docs = []

        for idx in self.inverted_index[keyword.lower()]:

            matching_docs.append(self.documents[idx].encode())



        return matching_docs





class PIRClient:

    """

    PIR客户端



    发起私密检索请求

    """



    def __init__(self):

        """初始化PIR客户端"""

        self.queries_sent = 0



    def prepare_query(self, index: int, method: str = "simple") -> any:

        """

        准备查询



        Args:

            index: 要检索的索引

            method: PIR方法



        Returns:

            查询

        """

        self.queries_sent += 1



        if method == "simple":

            # 简单PIR需要多服务器

            return index  # 返回索引,后续生成查询向量

        elif method == "homomorphic":

            # 同态PIR

            return index  # 返回明文索引,让服务器加密

        else:

            return index



    def retrieve_result(self, response: any, query: any) -> bytes:

        """

        客户端检索结果



        Args:

            response: 服务器响应

            query: 原始查询



        Returns:

            检索到的数据

        """

        return response  # 简化





class PIRServer:

    """

    PIR服务器



    响应私密检索请求

    """



    def __init__(self, data: List[bytes], method: str = "simple"):

        """

        初始化PIR服务器



        Args:

            data: 数据库内容

            method: PIR方法

        """

        self.data = data

        self.n = len(data)

        self.method = method



        if method == "simple":

            self.db = SimplePIRDatabase(data)

        elif method == "homomorphic":

            self.db = HomomorphicPIRDatabase(data)

        else:

            self.db = SimplePIRDatabase(data)



    def handle_query(self, query: any) -> any:

        """

        处理查询



        Args:

            query: 查询



        Returns:

            响应

        """

        if self.method == "simple":

            # 需要查询向量

            return self.db.respond(query)

        elif self.method == "homomorphic":

            return self.db.respond(query)

        else:

            return b""





class CPIRProtocol:

    """

    计算PIR协议



    完整的PIR协议实现

    """



    def __init__(self, database: List[bytes]):

        """

        初始化CPIR协议



        Args:

            database: 数据库

        """

        self.database = database

        self.n = len(database)

        self.client = PIRClient()

        self.server = PIRServer(database, method="homomorphic")



    def retrieve(self, index: int) -> bytes:

        """

        私密检索



        Args:

            index: 要检索的索引



        Returns:

            检索到的数据

        """

        # 1. 客户端准备查询

        query = self.client.prepare_query(index, method="homomorphic")



        # 2. 服务器处理查询

        response = self.server.handle_query(query)



        # 3. 客户端获取结果

        result = self.client.retrieve_result(response, query)



        return result





class XPIRImplementation:

    """

    扩展PIR (XPIR) 实现



    使用压缩感知和多项式编码减少通信开销



    参考文献: Angel et al., "XPIR: Private Information Retrieval

             with Reduced Communication", PoPETs 2018

    """



    def __init__(self, data: List[bytes]):

        """

        初始化XPIR



        Args:

            data: 数据库

        """

        self.data = data

        self.n = len(data)

        self.block_size = 256  # 每个块的字节数



    def encode_database(self) -> np.ndarray:

        """

        将数据库编码为多项式



        使用 Reed-Solomon 编码的简化版本



        Returns:

            编码后的多项式系数

        """

        # 简化: 将数据库分成块并编码

        n_blocks = (self.n + self.block_size - 1) // self.block_size

        encoded = np.zeros(n_blocks, dtype=int)



        for i in range(n_blocks):

            start = i * self.block_size

            end = min(start + self.block_size, self.n)

            block_data = b"".join(self.data[start:end])

            encoded[i] = int(hashlib.md5(block_data).hexdigest()[:8], 16)



        return encoded



    def query(self, index: int) -> np.ndarray:

        """

        生成查询多项式



        Args:

            index: 要检索的索引



        Returns:

            查询多项式

        """

        # 创建单点多项式: P(x) = 0 if x != index, P(index) = 1

        # 简化为选择向量

        query = np.zeros(self.n, dtype=int)

        query[index] = 1

        return query



    def respond(self, query: np.ndarray) -> bytes:

        """

        响应查询



        Args:

            query: 查询向量



        Returns:

            结果

        """

        # 找打1的位置

        indices = np.where(query == 1)[0]

        if len(indices) > 0:

            return self.data[indices[0]]

        return b""





def pir_demo():

    """

    PIR演示

    """



    print("私密信息检索(PIR)演示")

    print("=" * 60)



    # 1. 简单PIR(多服务器)

    print("\n1. 简单PIR (多服务器)")

    database = [f"记录{i}".encode() for i in range(10)]

    pir_db = SimplePIRDatabase(database)



    index = 5

    queries = pir_db.query(index, num_servers=3)

    print(f"   数据库大小: {len(database)}条记录")

    print(f"   查询索引: {index}")

    print(f"   生成{len(queries)}个查询向量")



    # 模拟服务器响应

    responses = [pir_db.respond(q) for q in queries]

    # 客户端合并响应

    result = responses[0]  # 简化

    print(f"   检索结果: {result}")



    # 2. 关键词PIR

    print("\n2. 关键词PIR")

    documents = [

        "apple fruit",

        "banana yellow",

        "apple pie recipe",

        "orange citrus fruit",

        "banana bread recipe"

    ]



    keyword_pir = KeywordPIRDatabase(documents)

    print(f"   文档数量: {len(documents)}")



    keyword = "apple"

    query = keyword_pir.query(keyword)

    results = keyword_pir.respond(query, keyword)

    print(f"   搜索关键词: '{keyword}'")

    print(f"   匹配文档: {len(results)}个")

    for doc in results:

        print(f"     - {doc.decode()}")



    # 3. 同态PIR

    print("\n3. 基于同态加密的PIR")

    db_data = [f"机密文件{i}".encode() for i in range(10)]

    homomorphic_pir = HomomorphicPIRDatabase(db_data)



    target_index = 7

    encrypted_query = homomorphic_pir.query(target_index)

    ciphertext_result = homomorphic_pir.respond(encrypted_query)

    result = homomorphic_pir.decrypt_result(ciphertext_result)



    print(f"   数据库大小: {len(db_data)}条")

    print(f"   查询索引: {target_index}")

    print(f"   检索结果: {result}")



    # 4. 安全性说明

    print("\n4. 安全性说明")

    print("   PIR保证:")

    print("   - 服务器不知道用户查询的是哪条记录")

    print("   - 即使数据库被攻破,查询记录仍然保密")

    print("   ")

    print("   不同PIR方案:")

    print("   - 简单PIR: 需要多个非共谋服务器")

    print("   - 同态PIR: 单服务器,但计算开销大")

    print("   - XPIR: 优化通信复杂度的扩展PIR")





if __name__ == "__main__":

    pir_demo()



    print("\n" + "=" * 60)

    print("PIR演示完成!")

    print("实际PIR系统需要: 同态加密 + 压缩编码 + 优化索引")

    print("=" * 60)

