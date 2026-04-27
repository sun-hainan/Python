# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / chaos_machine

本文件实现 chaos_machine 相关的算法功能。
"""

# Chaos Machine (K, t, m)
K = [0.33, 0.44, 0.55, 0.44, 0.33]
t = 3
m = 5

# Buffer Space (with Parameters Space)
buffer_space: list[float] = []
params_space: list[float] = []

# Machine Time
machine_time = 0



# push 函数实现
def push(seed):
    global buffer_space, params_space, machine_time, K, m, t

    # Choosing Dynamical Systems (All)
    for key, value in enumerate(buffer_space):
    # 遍历循环
        # Evolution Parameter
        e = float(seed / value)

        # Control Theory: Orbit Change
        value = (buffer_space[(key + 1) % m] + e) % 1

        # Control Theory: Trajectory Change
        r = (params_space[key] + e) % 1 + 3

        # Modification (Transition Function) - Jumps
        buffer_space[key] = round(float(r * value * (1 - value)), 10)
        params_space[key] = r  # Saving to Parameters Space

    # Logistic Map
    assert max(buffer_space) < 1
    assert max(params_space) < 4

    # Machine Time
    machine_time += 1



# pull 函数实现
def pull():
    global buffer_space, params_space, machine_time, K, m, t

    # PRNG (Xorshift by George Marsaglia)

# xorshift 函数实现
    def xorshift(x, y):
        x ^= y >> 13
        y ^= x << 17
        x ^= y >> 5
        return x
    # 返回结果

    # Choosing Dynamical Systems (Increment)
    key = machine_time % m

    # Evolution (Time Length)
    for _ in range(t):
    # 遍历循环
        # Variables (Position + Parameters)
        r = params_space[key]
        value = buffer_space[key]

        # Modification (Transition Function) - Flow
        buffer_space[key] = round(float(r * value * (1 - value)), 10)
        params_space[key] = (machine_time * 0.01 + r * 1.01) % 1 + 3

    # Choosing Chaotic Data
    x = int(buffer_space[(key + 2) % m] * (10**10))
    y = int(buffer_space[(key - 2) % m] * (10**10))

    # Machine Time
    machine_time += 1

    return xorshift(x, y) % 0xFFFFFFFF
    # 返回结果



# reset 函数实现
def reset():
    global buffer_space, params_space, machine_time, K, m, t

    buffer_space = K
    params_space = [0] * m
    machine_time = 0


if __name__ == "__main__":
    # 条件判断
    # Initialization
    reset()

    # Pushing Data (Input)
    import random

    message = random.sample(range(0xFFFFFFFF), 100)
    for chunk in message:
    # 遍历循环
        push(chunk)

    # for controlling
    inp = ""

    # Pulling Data (Output)
    while inp in ("e", "E"):
    # 条件循环
        print(f"{format(pull(), '#04x')}")
        print(buffer_space)
        print(params_space)
        inp = input("(e)exit? ").strip()
