# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / quine

本文件实现 quine 相关的算法功能。
"""

# 最简Quine
print("(lambda s: print(s %% repr(s)))('(lambda s: print(s %% repr(s)))')")


# 标准Quine写法
s = 's = %r\\nprint(s %% s)'
print(s % s)


# 使用format的Quine
def quine_format():
    source = 'def quine_format():\\n    source = %r\\n    print(source %% source)'
    print(source % source)


# 使用exec的Quine
code = 'code = %r\\nexec(code %% code)'
exec(code % code)


# 多行Quine
multi_line = """
source = %r
print(source %% repr(source))
"""
print(source % repr(source))


# 利用数据驱动的Quine
data = [
    "data = %r",
    "print(data[0] %% repr(data))",
]
print(data[0] % repr(data))


# 利用format字符串
format_quine = "{0!r}\nprint(format_quine.format({0!r}))"
print(format_quine.format(format_quine))


# 最经典的Quine（Python）
classic_quine = 'x = %r\\nprint("x = %r\\\\nprint(x %% x)" %% (x, x))'
print("x = %r\nprint(\"x = %r\\\\nprint(x %% x)\" %% (x, x))" % (x, x))


# 另一种风格
another = """
another = %r
print(another %% repr(another))
"""
print(another % repr(another))


# 使用lambda的Quine
(lambda x: print((x + ')(x)') % repr(x)))('(lambda x: print((x + \')(x)\') %% repr(x)))')


# 多层嵌套Quine
def outer():
    code = '''
def outer():
    code = %r
    exec(code %% repr(code))
'''
    exec(code % repr(code))


# 更简洁的Quine
q = 'q = %r\\nprint(q %% repr(q))'
print(q % repr(q))


# IO免费的Quine（只用print和字符串）
print('print(%r)' % 'print(%r)')


# 练习Quine
def learn_quine():
    template = "def learn_quine():\\n    template = %r\\n    print(template %% repr(template))"
    print(template % repr(template))


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Quine程序测试 ===\n")
    print("Quine是输出自身源代码的程序")
    print()
    print("上面运行的多个Quine变体：")
    print("  1. lambda + print组合")
    print("  2. s = '...' ; print(s % s)")
    print("  3. 多行字符串版本")
    print("  4. format字符串版本")
    print()
    print("原理：")
    print("  任何Quine都包含两部分：")
    print("  1. 描述部分（包含第二部分）")
    print("  2. 执行部分（打印描述部分）")
    print()
    print("运行验证：")
    print("  将上面的Quine保存为.py文件")
    print("  python xxx.py | diff - xxx.py")
    print("  如果没有差异，说明是真正的Quine")
    print()
    print("趣闻：")
    print("  - Quine名字来自哲学家Willard Van Orman Quine")
    print("  - 图灵奖得主Ken Thompson编写过一个\"后门Quine\"")
    print("  - 最短的Quine只有几行代码")
