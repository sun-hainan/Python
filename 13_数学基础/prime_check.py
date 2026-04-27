# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / prime_check



本文件实现 prime_check 相关的算法功能。

"""



class Test(unittest.TestCase):

    def test_primes(self):

        assert is_prime(2)

        assert is_prime(3)

        assert is_prime(5)

        assert is_prime(7)

        assert is_prime(11)

        assert is_prime(13)

        assert is_prime(17)

        assert is_prime(19)

        assert is_prime(23)

        assert is_prime(29)



    def test_not_primes(self):

        with pytest.raises(ValueError):

            is_prime(-19)

        assert not is_prime(0), (

            "Zero doesn't have any positive factors, primes must have exactly two."

        )

        assert not is_prime(1), (

            "One only has 1 positive factor, primes must have exactly two."

        )

        assert not is_prime(2 * 2)

        assert not is_prime(2 * 3)

        assert not is_prime(3 * 3)

        assert not is_prime(3 * 5)

        assert not is_prime(3 * 5 * 7)





if __name__ == "__main__":

    unittest.main()

