# -*- coding: utf-8 -*-

"""

算法实现：27_整数与FFT / big_integer_ops



本文件实现 big_integer_ops 相关的算法功能。

"""



# =============================================================================

# 数据结构定义 - Data Structure

# =============================================================================



class BigInt:

    """

    高精度大整数类。



    属性：

        digits: list[int]，十进制位列表，最低位在前（[0,1,2] = 210）

        sign: bool，符号（True=正，False=负，零为正）

    """



    def __init__(self, value=0):

        """

        初始化BigInt。



        参数：

            value: int/str/float，用于初始化

        """

        if isinstance(value, BigInt):

            # 拷贝构造

            self.digits = value.digits[:]

            self.sign = value.sign

        elif isinstance(value, str):

            self._parse_string(value)

        elif isinstance(value, int):

            self._parse_int(value)

        elif isinstance(value, float):

            self._parse_int(int(value))

        else:

            raise TypeError(f"不支持的类型: {type(value)}")



        self._normalize()



    def _parse_int(self, value):

        """将Python整数解析为BigInt内部表示。"""

        self.sign = value >= 0

        value = abs(value)

        self.digits = []

        if value == 0:

            self.digits = [0]

        else:

            while value > 0:

                self.digits.append(value % 10)

                value //= 10



    def _parse_string(self, s):

        """将字符串解析为BigInt。"""

        s = s.strip()

        if s.startswith('-'):

            self.sign = False

            s = s[1:]

        else:

            self.sign = True



        if not s:

            raise ValueError("空字符串")



        self.digits = []

        for ch in reversed(s):

            if ch.isdigit():

                self.digits.append(int(ch))

            elif ch == '_' or ch == ',':

                continue  # 忽略分隔符

            else:

                raise ValueError(f"非法字符: {ch}")



    def _normalize(self):

        """去除前导零，规范化表示。"""

        # 去除高位零

        while len(self.digits) > 1 and self.digits[-1] == 0:

            self.digits.pop()

        # 零永远是正的

        if self.digits == [0]:

            self.sign = True



    # -------------------------------------------------------------------------

    # 辅助方法 - Helpers

    # -------------------------------------------------------------------------



    def __repr__(self):

        """调试用字符串表示。"""

        sign_str = "-" if not self.sign and self.digits != [0] else ""

        digits_str = "".join(str(d) for d in reversed(self.digits))

        return f"BigInt('{sign_str}{digits_str}')"



    def __str__(self):

        """人类可读的十进制字符串。"""

        sign_str = "-" if not self.sign else ""

        return sign_str + "".join(str(d) for d in reversed(self.digits))



    def to_int(self):

        """转换回Python内置int（可能溢出）。"""

        result = 0

        for i, d in enumerate(self.digits):

            result += d * (10 ** i)

        return -result if not self.sign else result



    def __len__(self):

        """返回十进制位数。"""

        return len(self.digits)



    def __eq__(self, other):

        """相等比较。"""

        if not isinstance(other, BigInt):

            other = BigInt(other)

        return self.sign == other.sign and self.digits == other.digits



    def __lt__(self, other):

        """小于比较。"""

        if not isinstance(other, BigInt):

            other = BigInt(other)

        if self.sign != other.sign:

            return not self.sign  # 负数永远小于正数

        # 同号比较绝对值

        cmp = self._compare_abs(other)

        return cmp < 0 if self.sign else cmp > 0



    def __le__(self, other):

        return self == other or self < other



    def __gt__(self, other):

        return not self <= other



    def __ge__(self, other):

        return not self < other



    def _compare_abs(self, other):

        """比较绝对值大小。返回 -1/0/1。"""

        if len(self.digits) != len(other.digits):

            return -1 if len(self.digits) < len(other.digits) else 1

        for i in range(len(self.digits) - 1, -1, -1):

            if self.digits[i] < other.digits[i]:

                return -1

            elif self.digits[i] > other.digits[i]:

                return 1

        return 0



    def copy(self):

        """返回BigInt的深拷贝。"""

        return BigInt(self)



    # -------------------------------------------------------------------------

    # 加法 - Addition

    # -------------------------------------------------------------------------



    def __add__(self, other):

        """加法：self + other"""

        if not isinstance(other, BigInt):

            other = BigInt(other)



        # 异号：转化为减法

        if self.sign != other.sign:

            # a + (-b) = a - b

            # (-a) + b = b - a

            if self.sign:

                # self为正，other为负 → self - |other|

                neg_other = other.copy()

                neg_other.sign = True

                return self._sub(neg_other)

            else:

                # self为负，other为正 → other - |self|

                neg_self = self.copy()

                neg_self.sign = True

                return other._sub(neg_self)



        # 同号：直接加

        result = self._add_abs(other)

        result.sign = self.sign

        return result



    def __radd__(self, other):

        """右加：other + self"""

        return self.__add__(other)



    def _add_abs(self, other):

        """绝对值加法：|self| + |other|"""

        max_len = max(len(self.digits), len(other.digits))

        result = BigInt(0)

        result.digits = [0] * max_len

        carry = 0



        for i in range(max_len):

            a = self.digits[i] if i < len(self.digits) else 0

            b = other.digits[i] if i < len(other.digits) else 0

            s = a + b + carry

            result.digits[i] = s % 10

            carry = s // 10



        if carry > 0:

            result.digits.append(carry)



        result._normalize()

        return result



    # -------------------------------------------------------------------------

    # 减法 - Subtraction

    # -------------------------------------------------------------------------



    def __sub__(self, other):

        """减法：self - other"""

        if not isinstance(other, BigInt):

            other = BigInt(other)



        # 异号：转化为加法

        if self.sign != other.sign:

            # a - (-b) = a + b

            # (-a) - b = -(a + b)

            result = self._add_abs(other)

            result.sign = self.sign

            return result



        # 同号：比较绝对值确定符号

        cmp_result = self._compare_abs(other)



        if cmp_result == 0:

            return BigInt(0)  # 相等



        if cmp_result > 0:

            # |self| > |other|，结果为正

            result = self._sub_abs(other)

            result.sign = True

        else:

            # |self| < |other|，结果为负

            result = other._sub_abs(self)

            result.sign = False



        return result



    def __rsub__(self, other):

        """右减：other - self"""

        result = self.__sub__(other)

        result.sign = not result.sign

        return result



    def _sub_abs(self, other):

        """绝对值减法：|self| - |other|，要求|self| >= |other|"""

        max_len = len(self.digits)

        result = BigInt(0)

        result.digits = [0] * max_len

        borrow = 0



        for i in range(max_len):

            a = self.digits[i] if i < len(self.digits) else 0

            b = other.digits[i] if i < len(other.digits) else 0

            diff = a - b - borrow



            if diff < 0:

                diff += 10

                borrow = 1

            else:

                borrow = 0



            result.digits[i] = diff



        result._normalize()

        return result



    # -------------------------------------------------------------------------

    # 乘法 - Multiplication

    # -------------------------------------------------------------------------



    def __mul__(self, other):

        """乘法：self * other"""

        if not isinstance(other, BigInt):

            other = BigInt(other)



        # 零检测

        if self.digits == [0] or other.digits == [0]:

            return BigInt(0)



        # 符号

        result_sign = self.sign == other.sign



        # 竖式乘法 O(n²)

        result = BigInt(0)

        result.digits = [0] * (len(self.digits) + len(other.digits))



        for i, a in enumerate(self.digits):

            for j, b in enumerate(other.digits):

                result.digits[i + j] += a * b



        # 处理进位

        carry = 0

        for i in range(len(result.digits)):

            s = result.digits[i] + carry

            result.digits[i] = s % 10

            carry = s // 10



        while carry > 0:

            result.digits.append(carry % 10)

            carry //= 10



        result.sign = result_sign

        result._normalize()

        return result



    def __rmul__(self, other):

        """右乘：other * self"""

        return self.__mul__(other)



    # -------------------------------------------------------------------------

    # 除法 - Division

    # -------------------------------------------------------------------------



    def __floordiv__(self, other):

        """整数除法（向下取整）：self // other"""

        if not isinstance(other, BigInt):

            other = BigInt(other)



        if other.digits == [0]:

            raise ZeroDivisionError("division by zero")



        # 符号

        result_sign = self.sign == other.sign



        # 绝对值除法

        abs_quotient, _ = self._divmod_abs(other)



        abs_quotient.sign = result_sign

        return abs_quotient



    def __rfloordiv__(self, other):

        """右整数除：other // self"""

        result = BigInt(other).__floordiv__(self)

        return result



    def __mod__(self, other):

        """取模：self % other"""

        if not isinstance(other, BigInt):

            other = BigInt(other)



        if other.digits == [0]:

            raise ZeroDivisionError("modulo by zero")



        # 绝对值除法获取余数

        _, abs_remainder = self._divmod_abs(other)



        # Python风格的取模：结果与被除数同号

        # 但BigInt的sign只影响显示，不影响运算

        return abs_remainder



    def __rmod__(self, other):

        """右取模：other % self"""

        return BigInt(other).__mod__(self)



    def _divmod_abs(self, other):

        """

        绝对值除法：|self| ÷ |other|

        返回 (商, 余数)，均为BigInt



        算法：试商法（Trial Division）

        对于当前最高位，逐步估计商的一位

        """

        # 比较被除数与除数大小

        cmp_result = self._compare_abs(other)



        if cmp_result < 0:

            # |self| < |other|，商为0，余数为|self|

            return BigInt(0), self.copy()



        if cmp_result == 0:

            # |self| == |other|，商为1，余数为0

            return BigInt(1), BigInt(0)



        # 长除法

        n = len(other.digits)  # 除数长度

        m = len(self.digits)  # 被除数长度



        # 将被除数复制到工作区

        remainder_digits = self.digits[:]



        quotient_digits = [0] * (m - n + 1)

        quotient_idx = len(quotient_digits) - 1



        # 从最高位开始，逐步构建商

        for pos in range(m - 1, n - 1, -1):

            # 当前余数对应的数值（从pos到n-1的子串）

            current_len = pos - n + 1 + 1  # 长度

            if current_len < 0:

                break



            # 估算当前位的商

            # 找到当前余数部分对应的最高位

            # 从pos位置向前看n位

            if len(remainder_digits) <= pos:

                quotient_idx -= 1

                continue



            # 构建当前被除子串的值

            # 逐步扩展余数

            # 简化的试商：估算

            est = 0

            for i in range(pos, max(pos - n, -1) - 1, -1):

                if i >= len(remainder_digits):

                    continue

                est = est * 10 + remainder_digits[i]



            # 估算除数

            divisor_val = 0

            for i in range(n - 1, -1, -1):

                if i >= len(other.digits):

                    continue

                divisor_val = divisor_val * 10 + other.digits[i]



            # 试商

            q_digit = est // divisor_val

            if q_digit > 9:

                q_digit = 9

            if q_digit < 0:

                q_digit = 0



            quotient_digits[quotient_idx] = q_digit



            # 从余数中减去 q_digit * other * 10^{pos-n+1}

            power = pos - n + 1

            for i, d in enumerate(other.digits):

                for j in range(n - 1, -1, -1):

                    idx = i + power

                    if idx < len(remainder_digits):

                        remainder_digits[idx] -= d * other.digits[j]

                    if idx + 1 < len(remainder_digits):

                        remainder_digits[idx + 1] -= d * other.digits[j] // 10



            # 处理借位和归一化

            for i in range(len(remainder_digits)):

                while remainder_digits[i] < 0:

                    remainder_digits[i] += 10

                    if i + 1 < len(remainder_digits):

                        remainder_digits[i + 1] -= 1



            quotient_idx -= 1



        # 去除商的前导零

        while len(quotient_digits) > 1 and quotient_digits[-1] == 0:

            quotient_digits.pop()



        quotient = BigInt(0)

        quotient.digits = quotient_digits

        quotient.sign = True

        quotient._normalize()



        remainder = BigInt(0)

        remainder.digits = remainder_digits

        remainder.sign = True

        remainder._normalize()



        return quotient, remainder



    # -------------------------------------------------------------------------

    # 负号与绝对值 - Negation and Absolute Value

    # -------------------------------------------------------------------------



    def __neg__(self):

        """取负：-self"""

        result = self.copy()

        if result.digits != [0]:

            result.sign = not result.sign

        return result



    def __abs__(self):

        """绝对值：abs(self)"""

        result = self.copy()

        result.sign = True

        return result



    # -------------------------------------------------------------------------

    # 类型转换 - Type Conversions

    # -------------------------------------------------------------------------



    def __int__(self):

        """转换为Python int。"""

        return self.to_int()



    def __index__(self):

        """支持切片等int上下文中使用。"""

        return self.to_int()





# =============================================================================

# 辅助函数 - Utility Functions

# =============================================================================



def factorial_big(n):

    """

    计算n!，使用BigInt大整数。



    参数：

        n: 非负整数



    返回：

        BigInt: n!的值

    """

    if n < 0:

        raise ValueError("n必须为非负整数")

    if n <= 1:

        return BigInt(1)



    result = BigInt(1)

    for i in range(2, n + 1):

        result = result * BigInt(i)

    return result





def fibonacci_big(n):

    """

    计算第n个斐波那契数，使用BigInt大整数。



    参数：

        n: 非负整数（第0项为0，第1项为1）



    返回：

        BigInt: 斐波那契数

    """

    if n < 0:

        raise ValueError("n必须为非负整数")

    if n <= 1:

        return BigInt(n)



    a = BigInt(0)

    b = BigInt(1)



    for _ in range(2, n + 1):

        a, b = b, a + b



    return b





# =============================================================================

# 测试 - Tests

# =============================================================================



if __name__ == '__main__':

    print("=" * 60)

    print("BigInt大整数运算测试")

    print("=" * 60)



    # 基本运算测试

    test_cases = [

        ("12345 + 6789", BigInt(12345) + BigInt(6789), 19134),

        ("999999 + 1", BigInt(999999) + BigInt(1), 1000000),

        ("12345 - 6789", BigInt(12345) - BigInt(6789), 5556),

        ("1000 - 1", BigInt(1000) - BigInt(1), 999),

        ("123 * 456", BigInt(123) * BigInt(456), 56088),

        ("12345 * 6789", BigInt(12345) * BigInt(6789), 83810205),

        ("1000 // 7", int(BigInt(1000) // BigInt(7)), 142),

        ("1000 % 7", int(BigInt(1000) % BigInt(7)), 6),

    ]



    print("\n四则运算测试：")

    for expr, result, expected in test_cases:

        actual = int(result) if hasattr(result, 'to_int') else result

        status = "✓" if actual == expected else "✗"

        print(f"  {status} {expr} = {actual} (期望: {expected})")



    # 大数阶乘测试

    print("\n大数阶乘测试：")

    fact_100 = factorial_big(100)

    print(f"  100! = {fact_100}")

    print(f"  位数: {len(fact_100)} 位")



    # 斐波那契测试

    print("\n大数斐波那契测试：")

    fib_500 = fibonacci_big(500)

    fib_str = str(fib_500)

    print(f"  F(500) = {fib_str[:20]}...{fib_str[-20:]} (共{len(fib_str)}位)")



    # 负数运算测试

    print("\n负数运算测试：")

    a = BigInt(-12345)

    b = BigInt(678)

    print(f"  (-12345) + 678 = {a + b}")

    print(f"  (-12345) - 678 = {a - b}")

    print(f"  (-12345) * 67 = {a * BigInt(67)}")



    # 比较运算测试

    print("\n比较运算测试：")

    print(f"  BigInt(123) < BigInt(456) = {BigInt(123) < BigInt(456)}")

    print(f"  BigInt(999) > BigInt(1000) = {BigInt(999) > BigInt(1000)}")

    print(f"  BigInt(42) == BigInt(42) = {BigInt(42) == BigInt(42)}")



    # 与Python内置int对比

    print("\n与Python内置int对比（大数乘法）：")

    a_bi = BigInt("123456789012345678901234567890")

    b_bi = BigInt("987654321098765432109876543210")

    a_py = 123456789012345678901234567890

    b_py = 987654321098765432109876543210

    result_bi = a_bi * b_bi

    result_py = a_py * b_py

    print(f"  BigInt结果: {str(result_bi)[:30]}...")

    print(f"  Python int: {result_py}")

    print(f"  一致性: {'✓' if str(result_bi) == str(result_py) else '✗'}")

