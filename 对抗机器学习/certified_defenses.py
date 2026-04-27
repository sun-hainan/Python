# -*- coding: utf-8 -*-

"""

算法实现：对抗机器学习 / certified_defenses



本文件实现 certified_defenses 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class ParsevalRegularizer:

    """

    Parseval正则化器



    通过在训练损失中加入正交性惩罚项，使权重矩阵接近正交

    """



    def __init__(self, model, beta=1.0):

        """

        参数:

            model: 待正则化的模型

            beta: 正则化系数

        """

        self.model = model

        self.beta = beta



    def compute_orthogonality_penalty(self):

        """

        计算正交性惩罚项



        对于权重矩阵W，惩罚项为 ||W^T W - I||_F^2

        这鼓励W的列向量互相正交

        """

        penalty = 0.0



        for name, param in self.model.named_parameters():

            if 'weight' in name and param.dim() == 2:

                # 只处理二维权重矩阵（全连接层）

                W = param

                d_out, d_in = W.shape



                # 计算 W^T @ W

                WtW = torch.mm(W.t(), W)



                # 单位矩阵

                if d_out <= d_in:

                    I = torch.eye(d_out, device=W.device)

                    size = d_out

                else:

                    I = torch.eye(d_in, device=W.device)

                    size = d_in



                # 补零到相同维度

                I_padded = torch.zeros_like(WtW)

                I_padded[:size, :size] = I



                # Frobenius范数平方

                penalty += torch.sum((WtW - I_padded) ** 2)



        return penalty



    def compute_orthogonality_penalty_conv(self):

        """

        计算卷积层权重的正交性惩罚



        将卷积核 reshape 为矩阵后应用 Parseval 正则化

        """

        penalty = 0.0



        for name, param in self.model.named_parameters():

            if 'weight' in name and param.dim() == 4:

                # 卷积层权重 [out_channels, in_channels, kH, kW]

                W = param

                out_c, in_c, kH, kW = W.shape



                # reshape 为 [out_channels * kH * kW, in_channels]

                W_matrix = W.reshape(out_c * kH * kW, in_c)



                # 计算正交性

                WtW = torch.mm(W_matrix.t(), W_matrix)

                I = torch.eye(in_c, device=W.device)



                penalty += torch.sum((WtW - I) ** 2)



        return penalty



    def total_penalty(self):

        """计算总正则化惩罚"""

        return self.compute_orthogonality_penalty() + 0.5 * self.compute_orthogonality_penalty_conv()





def train_with_parseval(model, dataloader, optimizer, device, epochs=10, beta=1.0):

    """

    使用Parseval正则化训练模型



    参数:

        model: 待训练模型

        dataloader: 数据加载器

        optimizer: 优化器

        device: 计算设备

        epochs: 训练轮数

        beta: 正则化系数



    返回:

        training_history: 训练历史记录

    """

    parseval = ParsevalRegularizer(model, beta=beta)

    history = {'loss': [], 'penalty': [], 'acc': []}



    for epoch in range(epochs):

        model.train()

        epoch_loss = 0.0

        epoch_penalty = 0.0

        correct = 0

        total = 0



        for images, labels in dataloader:

            images = images.to(device)

            labels = labels.to(device)



            # 前向传播

            outputs = model(images)

            ce_loss = F.cross_entropy(outputs, labels)



            # Parseval惩罚

            penalty = parseval.total_penalty()



            # 总损失

            loss = ce_loss + beta * penalty



            # 反向传播

            optimizer.zero_grad()

            loss.backward()

            optimizer.step()



            # 统计

            epoch_loss += ce_loss.item() * len(labels)

            epoch_penalty += penalty.item() * len(labels)

            correct += (torch.argmax(outputs, dim=1) == labels).sum().item()

            total += len(labels)



        history['loss'].append(epoch_loss / total)

        history['penalty'].append(epoch_penalty / total)

        history['acc'].append(correct / total)



        print(f"Epoch {epoch + 1}: Loss={epoch_loss / total:.4f}, "

              f"Penalty={epoch_penalty / total:.4f}, Acc={correct / total:.2%}")



    return history





class CurvatureDefense:

    """

    曲率（Curvature）防御方法



    通过分析损失函数的局部曲率（Hessian矩阵）来评估和提升鲁棒性。

    核心思想：平坦的局部极小值点比尖锐的更鲁棒。

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def compute_hessian_trace(self, images, labels, num_samples=10):

        """

        近似计算Hessian矩阵的迹（用于测量锐度）



        参数:

            images: 输入图像

            labels: 标签

            num_samples: 采样次数（ Hutchinson 近似）



        返回:

            avg_trace: 平均Hessian迹

        """

        self.model.eval()

        total_trace = 0.0



        for _ in range(num_samples):

            # 生成随机向量

            v = torch.randn_like(images).view(len(images), -1)

            v = v / torch.norm(v, dim=1, keepdim=True)

            v.requires_grad = True



            # 计算 v^T @ H @ v

            outputs = self.model(images)

            loss = F.cross_entropy(outputs, labels)



            grad_v = torch.autograd.grad(loss, images, create_graph=True)[0]

            grad_v_flat = grad_v.view(len(images), -1)



            # Hessian-vector product

            hvp = torch.autograd.grad(

                (grad_v_flat * v).sum(), images, retain_graph=True

            )[0]



            hvp_flat = hvp.view(len(images), -1)

            trace_estimate = (grad_v_flat * hvp_flat).sum(dim=1)

            total_trace += trace_estimate.mean().item()



        return total_trace / num_samples



    def compute_sharpness(self, images, labels, epsilon=0.01):

        """

        计算损失面的锐度



        参数:

            epsilon: 扰动半径

            返回: 锐度度量（扰动后损失 - 原始损失 的上界）

        """

        self.model.eval()



        # 原始损失

        with torch.no_grad():

            outputs = self.model(images)

            original_loss = F.cross_entropy(outputs, labels).item()



        # 找最大损失扰动方向（简化版）

        perturbed_images = images + torch.randn_like(images) * epsilon

        perturbed_images = torch.clamp(perturbed_images, 0, 1)



        with torch.no_grad():

            perturbed_outputs = self.model(perturbed_images)

            perturbed_loss = F.cross_entropy(perturbed_outputs, labels).item()



        sharpness = perturbed_loss - original_loss



        return sharpness, perturbed_loss



    def curvature_regularized_loss(self, images, labels, lambda_curv=0.1):

        """

        曲率正则化损失



        加入曲率惩罚，鼓励更平坦的局部极小值



        参数:

            lambda_curv: 曲率正则化系数

        """

        outputs = self.model(images)

        ce_loss = F.cross_entropy(outputs, labels)



        # 简化版：使用梯度范数作为曲率的代理

        images_flat = images.view(len(images), -1)

        grad = torch.autograd.grad(

            ce_loss, images, retain_graph=True, create_graph=True

        )[0]

        grad_flat = grad.view(len(grad), -1)



        # 曲率惩罚 = 梯度范数

        curvature_penalty = torch.norm(grad_flat, dim=1).mean()



        return ce_loss + lambda_curv * curvature_penalty





class LipschitzRegularizer:

    """

    Lipschitz正则化器



    约束神经网络的全局Lipschitz常数来保证鲁棒性

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def compute_lipschitz_bound(self):

        """

        计算网络 Lipschitz 常数的上界



        对于 ReLU 网络：L <= prod(layer_norms)

        其中 layer_norm 是权重矩阵的谱范数

        """

        lipschitz_bound = 1.0



        for name, param in self.model.named_parameters():

            if 'weight' in name:

                if param.dim() == 2:

                    # 谱范数（最大奇异值）

                    sigma = torch.svd(param).S[0]

                    lipschitz_bound *= sigma.item()

                elif param.dim() == 4:

                    # 卷积层：用 reshape 后的谱范数

                    W = param.reshape(param.size(0), -1)

                    sigma = torch.svd(W).S[0]

                    lipschitz_bound *= sigma.item()



        return lipschitz_bound



    def spectral_normalization(self, name, n_power_iter=1):

        """

        对权重矩阵进行谱归一化，使谱范数 <= 1



        参数:

            name: 参数名

            n_power_iter: 幂迭代次数

        """

        # 在实际实现中需要追踪原始权重

        pass





if __name__ == "__main__":

    # 定义简单模型

    class SimpleCNN(nn.Module):

        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)

            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)

            self.fc1 = nn.Linear(64 * 7 * 7, 128)

            self.fc2 = nn.Linear(128, num_classes)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    device = torch.device("cpu")

    model = SimpleCNN(num_classes=10).to(device)



    # 虚拟数据

    class DummyDataset:

        def __init__(self, size=10):

            self.size = size



        def __iter__(self):

            for _ in range(self.size):

                images = torch.rand(16, 1, 28, 28)

                labels = torch.randint(0, 10, (16,))

                yield images, labels



    print("=" * 50)

    print("认证防御测试（Parseval + Curvature）")

    print("=" * 50)



    # Parseval正则化测试

    print("\n--- Parseval 正则化 ---")

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)



    parseval = ParsevalRegularizer(model, beta=1.0)

    initial_penalty = parseval.total_penalty().item()

    print(f"初始正交性惩罚: {initial_penalty:.4f}")



    # 训练几步

    model.train()

    for epoch in range(3):

        for images, labels in DummyDataset(5):

            images, labels = images.to(device), labels.to(device)



            outputs = model(images)

            ce_loss = F.cross_entropy(outputs, labels)

            penalty = parseval.total_penalty()

            loss = ce_loss + penalty



            optimizer.zero_grad()

            loss.backward()

            optimizer.step()



    final_penalty = parseval.total_penalty().item()

    print(f"训练后正交性惩罚: {final_penalty:.4f}")



    # Curvature测试

    print("\n--- Curvature 防御 ---")

    curvature = CurvatureDefense(model, device)



    test_images = torch.rand(4, 1, 28, 28).to(device)

    test_labels = torch.tensor([0, 1, 2, 3]).to(device)



    sharpness, pert_loss = curvature.compute_sharpness(test_images, test_labels)

    print(f"损失锐度: {sharpness:.4f}, 扰动后损失: {pert_loss:.4f}")



    # Lipschitz边界

    print("\n--- Lipschitz 常数 ---")

    lipschitz = LipschitzRegularizer(model, device)

    lip_bound = lipschitz.compute_lipschitz_bound()

    print(f"网络 Lipschitz 上界: {lip_bound:.4f}")



    print("\n测试完成！")

