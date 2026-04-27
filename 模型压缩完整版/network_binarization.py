# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / network_binarization



本文件实现 network_binarization 相关的算法功能。

"""



import numpy as np





def sign_function(x):

    """

    符号函数: 将实数值映射到二值 {+1, -1}

    

    Parameters

    ----------

    x : float or np.ndarray

        输入的实数值

    

    Returns

    -------

    np.ndarray

        二值化后的结果, +1 表示正, -1 表示非正

    """

    # 使用 np.where 实现符号函数,兼容向量输入

    return np.where(x >= 0, 1.0, -1.0)





def clip_gradient(x, lower=-1.0, upper=1.0):

    """

    裁剪梯度: 将梯度限制在 [lower, upper] 范围内

    用于防止梯度爆炸,稳定训练过程

    

    Parameters

    ----------

    x : np.ndarray

        输入梯度

    lower : float

        梯度下界,默认 -1.0

    upper : float

        梯度上界,默认 1.0

    

    Returns

    -------

    np.ndarray

        裁剪后的梯度

    """

    return np.clip(x, lower, upper)





def binarize_weights(weights, method="deterministic"):

    """

    二值化权重矩阵

    

    BNN 中权重二值化方法:

    - deterministic: 直接使用符号函数, w_b = sign(w)

    - stochastic: 基于概率的随机二值化,更利于梯度传递

    

    Parameters

    ----------

    weights : np.ndarray

        原始浮点权重,形状为 (out_features, in_features)

    method : str

        二值化方法,可选 "deterministic" 或 "stochastic"

    

    Returns

    -------

    np.ndarray

        二值化后的权重,形状与输入相同

    """

    if method == "deterministic":

        # 确定性方法: 直接取符号

        binary_weights = sign_function(weights)

    elif method == "stochastic":

        # 随机方法: 以概率 p = (w+1)/2 输出 +1

        prob_plus_one = (weights + 1.0) / 2.0

        prob_plus_one = np.clip(prob_plus_one, 0.0, 1.0)

        random_vals = np.random.uniform(0, 1, size=weights.shape)

        binary_weights = np.where(random_vals <= prob_plus_one, 1.0, -1.0)

    else:

        raise ValueError(f"未知的二值化方法: {method}")

    

    return binary_weights





def xnor_binarize(x, return_scale=True):

    """

    XNOR-Net 二值化: 权重/激活值的缩放二值化

    

    XNOR-Net 核心公式: x ≈ α ⊙ sign(x)

    其中 α = ||x||_L1 / n 是缩放因子,n为元素个数

    

    优势: 

    1. 缩放因子部分恢复量化损失的精度

    2. 二值操作可用 XNOR+BitCount 极致加速

    

    Parameters

    ----------

    x : np.ndarray

        输入张量,任意形状

    return_scale : bool

        若为 True,返回 (二值张量, 缩放因子); 否则只返回二值张量

    

    Returns

    -------

    tuple or np.ndarray

        (二值张量, 缩放因子) 或 仅二值张量

    """

    # 计算 L1 范数的缩放因子: α = mean(|x|)

    # keepdims=True 保持广播兼容性

    scale_factor = np.mean(np.abs(x), keepdims=True)

    

    # 二值化: 使用符号函数

    binary_x = sign_function(x)

    

    if return_scale:

        return binary_x, scale_factor

    else:

        return binary_x





def xnor_conv2d(input_activations, kernel_weights, stride=1, padding=0):

    """

    XNOR-Net 风格的二值卷积 (伪实现,展示计算流程)

    

    标准卷积: y = W * x

    二值卷积: y = α_W ⊙ sign(W) * (α_X ⊙ sign(X))

            = (α_W * α_X) ⊙ (sign(W) ⊙ sign(X))

    

    其中 ⊙ 为 element-wise 乘法, * 为卷积操作

    

    Parameters

    ----------

    activations : np.ndarray

        输入激活值,形状 (batch, channels, height, width)

    weights : np.ndarray

        卷积核权重,形状 (out_channels, in_channels, kH, kW)

    stride : int

        卷积步长,默认 1

    padding : int

        填充大小,默认 0

    

    Returns

    -------

    np.ndarray

        卷积输出,形状 (batch, out_channels, out_h, out_w)

    """

    # 获取输入形状

    batch, in_c, in_h, in_w = activations.shape

    out_c, _, kH, kW = weights.shape

    

    # 计算输出尺寸

    out_h = (in_h + 2 * padding - kH) // stride + 1

    out_w = (in_w + 2 * padding - kW) // stride + 1

    

    # 对输入和权重分别进行 XNOR 二值化

    binary_act, scale_act = xnor_binarize(activations, return_scale=True)

    binary_wgt, scale_wgt = xnor_binarize(weights, return_scale=True)

    

    # 组合缩放因子: α = α_W * α_X

    combined_scale = scale_wgt * scale_act

    

    # 由于 numpy 没有高效的二值卷积实现,这里用 im2col 模拟

    # 实际硬件实现中,sign(W) ⊙ sign(X) 可用 XNOR 门完成

    output = np.zeros((batch, out_c, out_h, out_w))

    

    for b in range(batch):

        for oc in range(out_c):

            for oh in range(out_h):

                for ow in range(out_w):

                    # 提取局部区域

                    h_start = oh * stride

                    w_start = ow * stride

                    patch = binary_act[b, :, h_start:h_start+kH, w_start:w_start+kW]

                    # 二值向量内积: sum(sign(a)*sign(w)) = count(1) - count(0)

                    # 硬件上用 XNOR + popcount 实现

                    binary_conv_sum = np.sum(patch * binary_wgt[oc])

                    # 应用缩放因子

                    output[b, oc, oh, ow] = combined_scale[0, 0] * binary_conv_sum

    

    return output





def straight_through_estimator(grad_output):

    """

    Straight-Through Estimator (STE) 近似梯度

    

    问题: sign() 函数的梯度在除零点外均为 0,无法用于反向传播

    解决: STE 假设 sign() 的梯度为 1 (或裁剪后的值)

    

    公式: dL/dx = dL/d(sign(x)), 当 |x| ≤ 1 时梯度为 dL/dy,否则为 0

    

    Parameters

    ----------

    grad_output : np.ndarray

        上游传来的梯度 ∂L/∂y

    

    Returns

    -------

    np.ndarray

        近似的梯度 ∂L/∂x

    """

    # STE: 当 |x| ≤ 1 时,梯度直通;否则梯度为 0

    return clip_gradient(grad_output, -1.0, 1.0)





def binarized_network_layer(input_x, weights, method="xnor"):

    """

    单层二值化网络的前向传播

    

    完整流程:

    1. 输入二值化: X_b = sign(X)

    2. 权重二值化: W_b = sign(W)

    3. 计算缩放因子: α_X, α_W

    4. 输出: Y = (α_X * α_W) ⊙ (X_b ⊙ W_b)

    

    Parameters

    ----------

    input_x : np.ndarray

        输入激活值,形状 (batch, in_features)

    weights : np.ndarray

        权重矩阵,形状 (out_features, in_features)

    method : str

        二值化方法, "bnn" 或 "xnor"

    

    Returns

    -------

    np.ndarray

        层输出,形状 (batch, out_features)

    """

    if method == "bnn":

        # BNN: 简单二值化,无缩放因子

        binary_x = sign_function(input_x)

        binary_w = binarize_weights(weights)

        output = binary_x @ binary_w.T

    elif method == "xnor":

        # XNOR-Net: 带缩放因子

        binary_x, scale_x = xnor_binarize(input_x, return_scale=True)

        binary_w, scale_w = xnor_binarize(weights, return_scale=True)

        # XNOR 操作: 异号为 -1,同号为 +1

        xnor_result = binary_x * binary_w

        # 应用缩放因子

        output = (scale_x * scale_w) * xnor_result @ np.ones_like(binary_w)

    else:

        raise ValueError(f"未知的二值化方法: {method}")

    

    return output





def compute_binarization_error(original, reconstructed):

    """

    计算量化误差: MSE(original, reconstructed)

    

    用于评估二值化方案的信息损失程度

    

    Parameters

    ----------

    original : np.ndarray

        原始浮点张量

    reconstructed : np.ndarray

        二值化重建的张量

    

    Returns

    -------

    float

        均方误差 (MSE)

    """

    return np.mean((original - reconstructed) ** 2)





if __name__ == "__main__":

    # 测试: BNN 和 XNOR-Net 二值化

    

    print("=" * 60)

    print("神经网络二值化测试")

    print("=" * 60)

    

    # 设置随机种子,确保结果可复现

    np.random.seed(42)

    

    # 创建模拟的权重和激活值

    batch_size = 4

    in_features = 8

    out_features = 16

    

    weights = np.random.randn(out_features, in_features)

    activations = np.random.randn(batch_size, in_features)

    

    print(f"\n原始权重形状: {weights.shape}")

    print(f"原始激活值形状: {activations.shape}")

    

    # 测试 BNN 二值化

    binary_weights_bnn = binarize_weights(weights, method="deterministic")

    print(f"\nBNN 二值化权重 (前3行):\n{binary_weights_bnn[:3]}")

    

    # 测试 XNOR 二值化

    binary_act, scale_act = xnor_binarize(activations, return_scale=True)

    binary_wgt, scale_wgt = xnor_binarize(weights, return_scale=True)

    print(f"\nXNOR 激活值缩放因子: {scale_act}")

    print(f"XNOR 权重缩放因子形状: {scale_wgt.shape}")

    

    # 测试完整层传播

    output_bnn = binarized_network_layer(activations, weights, method="bnn")

    output_xnor = binarized_network_layer(activations, weights, method="xnor")

    

    print(f"\nBNN 层输出形状: {output_bnn.shape}")

    print(f"XNOR 层输出形状: {output_xnor.shape}")

    

    # 计算量化误差

    # 重建 XNOR 输出: reconstructed ≈ α ⊙ sign(x)

    reconstructed = scale_act * binary_act

    error_xnor = compute_binarization_error(activations, reconstructed)

    

    print(f"\nXNOR 激活值量化误差 (MSE): {error_xnor:.6f}")

    

    # 测试 STE

    grad_output = np.random.randn(batch_size, out_features)

    grad_approx = straight_through_estimator(grad_output)

    print(f"\nSTE 梯度近似 (前5个元素): {grad_approx[0, :5]}")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)

