# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / sha1



本文件实现 sha1 相关的算法功能。

"""



import argparse

import hashlib  # hashlib is only used inside the Test class

import struct





class SHA1Hash:

    """

    Class to contain the entire pipeline for SHA1 hashing algorithm

    >>> SHA1Hash(bytes('Allan', 'utf-8')).final_hash()

    '872af2d8ac3d8695387e7c804bf0e02c18df9e6e'

    """



    def __init__(self, data):

        """

        Initiates the variables data and h. h is a list of 5 8-digit hexadecimal

        numbers corresponding to

        (1732584193, 4023233417, 2562383102, 271733878, 3285377520)

        respectively. We will start with this as a message digest. 0x is how you write

        hexadecimal numbers in Python

        """

        self.data = data

        self.h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]



    @staticmethod



# rotate 函数实现

    def rotate(n, b):

        """

        Static method to be used inside other methods. Left rotates n by b.

        >>> SHA1Hash('').rotate(12,2)

        48

        """

        return ((n << b) | (n >> (32 - b))) & 0xFFFFFFFF

    # 返回结果





# padding 函数实现

    def padding(self):

        """

        Pads the input message with zeros so that padded_data has 64 bytes or 512 bits

        """

        padding = b"\x80" + b"\x00" * (63 - (len(self.data) + 8) % 64)

        padded_data = self.data + padding + struct.pack(">Q", 8 * len(self.data))

        return padded_data

    # 返回结果





# split_blocks 函数实现

    def split_blocks(self):

        """

        Returns a list of bytestrings each of length 64

        """

        return [

    # 返回结果

            self.padded_data[i : i + 64] for i in range(0, len(self.padded_data), 64)

        ]



    # @staticmethod



# expand_block 函数实现

    def expand_block(self, block):

        """

        Takes a bytestring-block of length 64, unpacks it to a list of integers and

        returns a list of 80 integers after some bit operations

        """

        w = list(struct.unpack(">16L", block)) + [0] * 64

        for i in range(16, 80):

    # 遍历循环

            w[i] = self.rotate((w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16]), 1)

        return w

    # 返回结果





# final_hash 函数实现

    def final_hash(self):

        """

        Calls all the other methods to process the input. Pads the data, then splits

        into blocks and then does a series of operations for each block (including

        expansion).

        For each block, the variable h that was initialized is copied to a,b,c,d,e

        and these 5 variables a,b,c,d,e undergo several changes. After all the blocks

        are processed, these 5 variables are pairwise added to h ie a to h[0], b to h[1]

        and so on. This h becomes our final hash which is returned.

        """

        self.padded_data = self.padding()

        self.blocks = self.split_blocks()

        for block in self.blocks:

    # 遍历循环

            expanded_block = self.expand_block(block)

            a, b, c, d, e = self.h

            for i in range(80):

    # 遍历循环

                if 0 <= i < 20:

    # 条件判断

                    f = (b & c) | ((~b) & d)

                    k = 0x5A827999

                elif 20 <= i < 40:

                    f = b ^ c ^ d

                    k = 0x6ED9EBA1

                elif 40 <= i < 60:

                    f = (b & c) | (b & d) | (c & d)

                    k = 0x8F1BBCDC

                elif 60 <= i < 80:

                    f = b ^ c ^ d

                    k = 0xCA62C1D6

                a, b, c, d, e = (

                    self.rotate(a, 5) + f + e + k + expanded_block[i] & 0xFFFFFFFF,

                    a,

                    self.rotate(b, 30),

                    c,

                    d,

                )

            self.h = (

                self.h[0] + a & 0xFFFFFFFF,

                self.h[1] + b & 0xFFFFFFFF,

                self.h[2] + c & 0xFFFFFFFF,

                self.h[3] + d & 0xFFFFFFFF,

                self.h[4] + e & 0xFFFFFFFF,

            )

        return ("{:08x}" * 5).format(*self.h)

    # 返回结果







# test_sha1_hash 函数实现

def test_sha1_hash():

    msg = b"Test String"

    assert SHA1Hash(msg).final_hash() == hashlib.sha1(msg).hexdigest()  # noqa: S324







# main 函数实现

def main():

    """

    Provides option 'string' or 'file' to take input and prints the calculated SHA1

    hash. unittest.main() has been commented out because we probably don't want to run

    the test each time.

    """

    # unittest.main()

    parser = argparse.ArgumentParser(description="Process some strings or files")

    parser.add_argument(

        "--string",

        dest="input_string",

        default="Hello World!! Welcome to Cryptography",

        help="Hash the string",

    )

    parser.add_argument("--file", dest="input_file", help="Hash contents of a file")

    args = parser.parse_args()

    input_string = args.input_string

    # In any case hash input should be a bytestring

    if args.input_file:

    # 条件判断

        with open(args.input_file, "rb") as f:

            hash_input = f.read()

    else:

        hash_input = bytes(input_string, "utf-8")

    print(SHA1Hash(hash_input).final_hash())





if __name__ == "__main__":

    # 条件判断

    main()

    import doctest



    doctest.testmod()

