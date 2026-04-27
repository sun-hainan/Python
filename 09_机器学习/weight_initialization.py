# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / weight_initialization



本文件实现 weight_initialization 相关的算法功能。

"""



import numpy as np





def xavier_uniform(fan_in, fan_out):

    """

    Xavier均匀初始化



    公式: W ~ Uniform(-bound, bound)

    其中 bound = sqrt(6 / (fan_in + fan_out))



    适用于: Sigmoid, Tanh



    参数:

        fan_in: 输入维度

        fan_out: 输出维度



    返回:

        W: 初始化权重

    """

    bound = np.sqrt(6.0 / (fan_in + fan_out))

    W = np.random.uniform(-bound, bound, (fan_in, fan_out))

    return W





def xavier_normal(fan_in, fan_out):

    """

    Xavier正态初始化



    公式: W ~ N(0, 2/(fan_in + fan_out))



    适用于: Sigmoid, Tanh



    参数:

        fan_in: 输入维度

        fan_out: 输出维度



    返回:

        W: 初始化权重

    """

    std = np.sqrt(2.0 / (fan_in + fan_out))

    W = np.random.randn(fan_in, fan_out) * std

    return W





def kaiming_uniform(fan_in, fan_out, nonlinearity='relu'):

    """

    Kaiming/He均匀初始化



    公式: W ~ Uniform(-bound, bound)

    其中 bound = sqrt(6 / fan_in) * gain



    适用于: ReLU, Leaky ReLU, PReLU



    参数:

        fan_in: 输入维度

        fan_out: 输出维度

        nonlinearity: 激活函数类型

    """

    gain = {'relu': np.sqrt(2), 'leaky_relu': np.sqrt(2 / 1.01), 'linear': 1}.get(

        nonlinearity, np.sqrt(2)

    )

    bound = gain * np.sqrt(6.0 / fan_in)

    W = np.random.uniform(-bound, bound, (fan_in, fan_out))

    return W





def kaiming_normal(fan_in, fan_out, nonlinearity='relu'):

    """

    Kaiming/He正态初始化



    公式: W ~ N(0, 2/fan_in)



    适用于: ReLU, Leaky ReLU, PReLU



    参数:

        fan_in: 输入维度

        fan_out: 输出维度

        nonlinearity: 激活函数类型

    """

    gain = {'relu': np.sqrt(2), 'leaky_relu': np.sqrt(2 / 1.01), 'linear': 1}.get(

        nonlinearity, np.sqrt(2)

    )

    std = gain * np.sqrt(2.0 / fan_in)

    W = np.random.randn(fan_in, fan_out) * std

    return W





def lecun_normal(fan_in, fan_out):

    """

    LeCun正态初始化



    公式: W ~ N(0, 1/fan_in)



    适用于: SELU, Identity mappings



    参数:

        fan_in: 输入维度

        fan_out: 输出维度

    """

    std = np.sqrt(1.0 / fan_in)

    W = np.random.randn(fan_in, fan_out) * std

    return W





def orthogonal_init(fan_in, fan_out, gain=1.0):

    """

    正交初始化



    权重以正交矩阵形式初始化，

    有助于保持前向传播时各层方差一致



    参数:

        fan_in: 输入维度

        fan_out: 输出维度

        gain: 缩放因子



    返回:

        W: 正交初始化权重

    """

    if fan_in < fan_out:

        # 使用QR分解生成正交基

        flat_W = np.random.randn(fan_in, fan_out)

    else:

        flat_W = np.random.randn(fan_out, fan_in).T



    # QR分解

    Q, R = np.linalg.qr(flat_W)



    # 调整符号确保列范数一致

    diag = np.diag(R)

    sign = np.where(diag > 0, 1, -1)

    Q = Q * sign



    # 缩放

    if fan_in < fan_out:

        W = Q * gain

    else:

        W = Q[:fan_out, :] * gain



    return W





class WeightInitializer:

    """

    权重初始化工具类



    支持多种初始化方法和激活函数适配

    """



    # 初始化方法映射

    METHODS = {

        'xavier_uniform': lambda fan_in, fan_out, **kwargs: xavier_uniform(fan_in, fan_out),

        'xavier_normal': lambda fan_in, fan_out, **kwargs: xavier_normal(fan_in, fan_out),

        'kaiming_uniform': lambda fan_in, fan_out, **kwargs: kaiming_uniform(fan_in, fan_out, **kwargs),

        'kaiming_normal': lambda fan_in, fan_out, **kwargs: kaiming_normal(fan_in, fan_out, **kwargs),

        'lecun_normal': lambda fan_in, fan_out, **kwargs: lecun_normal(fan_in, fan_out),

        'orthogonal': lambda fan_in, fan_out, **kwargs: orthogonal_init(fan_in, fan_out, **kwargs),

    }



    # 激活函数推荐初始化方法

    ACTIVATION_RECOMMENDATIONS = {

        'sigmoid': 'xavier_uniform',

        'tanh': 'xavier_uniform',

        'relu': 'kaiming_normal',

        'leaky_relu': 'kaiming_normal',

        'prelu': 'kaiming_normal',

        'selu': 'lecun_normal',

        'linear': 'xavier_uniform',

    }



    @classmethod

    def initialize(cls, shape, method='xavier_normal', activation='relu', **kwargs):

        """

        初始化权重



        参数:

            shape: 权重形状 (fan_in, fan_out)

            method: 初始化方法

            activation: 激活函数类型

            **kwargs: 其他参数



        返回:

            W: 初始化权重

        """

        fan_in, fan_out = shape[0], shape[1]



        # 自动选择方法

        if method == 'auto':

            method = cls.ACTIVATION_RECOMMENDATIONS.get(activation, 'xavier_normal')



        init_func = cls.METHODS.get(method)

        if init_func is None:

            raise ValueError(f"未知的初始化方法: {method}")



        return init_func(fan_in, fan_out, **kwargs)



    @classmethod

    def test_initialization(cls, init_method, n_samples=10000):

        """

        测试初始化方法的统计特性



        参数:

            init_method: 初始化方法函数

            n_samples: 采样次数

        """

        # 测试不同形状

        shapes = [(512, 256), (256, 512), (1000, 1000)]



        print(f"\n测试 {init_method.__name__}:")

        print("-" * 50)



        for shape in shapes:

            W = init_method(shape[0], shape[1])

            mean = np.mean(W)

            std = np.std(W)

            var = np.var(W)



            print(f"  形状 {shape}:")

            print(f"    均值: {mean:.6f} (期望≈0)")

            print(f"    方差: {var:.6f}")

            print(f"    标准差: {std:.6f}")





if __name__ == "__main__":

    np.random.seed(42)



    print("=" * 60)

    print("神经网络权重初始化方法测试")

    print("=" * 60)



    # 测试各种初始化方法

    test_methods = [

        ('Xavier均匀', xavier_uniform),

        ('Xavier正态', xavier_normal),

        ('Kaiming均匀', kaiming_uniform),

        ('Kaiming正态', kaiming_normal),

        ('LeCun正态', lecun_normal),

    ]



    for name, method in test_methods:

        WeightInitializer.test_initialization(method)



    # 演示实际使用

    print("\n" + "=" * 60)

    print("实际使用示例")

    print("=" * 60)



    # 模拟一个简单网络

    layer_dims = [784, 512, 256, 10]

    weights = []

    biases = []



    print("\n使用推荐的初始化方法构建网络:")

    for i in range(len(layer_dims) - 1):

        fan_in = layer_dims[i]

        fan_out = layer_dims[i + 1]



        # 根据层位置选择激活函数（简化）

        if i < len(layer_dims) - 2:

            activation = 'relu'

        else:

            activation = 'linear'



        # 自动选择初始化方法

        W = WeightInitializer.initialize(

            (fan_in, fan_out),

            method='auto',

            activation=activation

        )

        b = np.zeros(fan_out)



        weights.append(W)

        biases.append(b)



        print(f"  层 {i+1}: {fan_in} -> {fan_out}, 激活={activation}")

        print(f"    W形状: {W.shape}, 均值={np.mean(W):.4f}, 标准差={np.std(W):.4f}")



    # 对比不同初始化的效果

    print("\n" + "=" * 60)

    print("梯度传播对比（简化模拟）")

    print("=" * 60)



    x = np.random.randn(32, layer_dims[0])

    print(f"输入方差: {np.var(x):.4f}")



    for i, W in enumerate(weights):

        x = x @ W

        variance_after = np.var(x)

        print(f"层 {i+1} 后方差: {variance_after:.4f}, "

              f"缩放比: {variance_after / np.var(x) if np.var(x) > 0 else 0:.4f}")

        x = np.maximum(0, x)  # ReLU

