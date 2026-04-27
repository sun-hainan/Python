# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / bloom_filter



本文件实现 bloom_filter 相关的算法功能。

"""



from hashlib import md5, sha256



HASH_FUNCTIONS = (sha256, md5)





class Bloom:

    def __init__(self, size: int = 8) -> None:

        self.bitarray = 0b0

        self.size = size



    def add(self, value: str) -> None:

        h = self.hash_(value)

        self.bitarray |= h



    def exists(self, value: str) -> bool:

        h = self.hash_(value)

        return (h & self.bitarray) == h



    def __contains__(self, other: str) -> bool:

        return self.exists(other)



    def format_bin(self, bitarray: int) -> str:

        res = bin(bitarray)[2:]

        return res.zfill(self.size)



    @property

    def bitstring(self) -> str:

        return self.format_bin(self.bitarray)



    def hash_(self, value: str) -> int:

        res = 0b0

        for func in HASH_FUNCTIONS:

            position = (

                int.from_bytes(func(value.encode()).digest(), "little") % self.size

            )

            res |= 2**position

        return res



    def format_hash(self, value: str) -> str:

        return self.format_bin(self.hash_(value))



    @property

    def estimated_error_rate(self) -> float:

        n_ones = bin(self.bitarray).count("1")

        return (n_ones / self.size) ** len(HASH_FUNCTIONS)

if __name__ == "__main__":

    import doctest

    doctest.testmod()

