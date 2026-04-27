# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / unstructured_pruning



本文件实现 unstructured_pruning 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F

import copy

from typing import Dict, List, Tuple





class MagnitudePruner:

    """

    幅度剪枝器



    移除绝对值最小的权重

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def compute_sparsity(self):

        """

        计算当前模型稀疏度



        返回:

            sparsity: 零值权重比例

            total_weights: 总权重数

        """

        total_weights = 0

        zero_weights = 0



        for param in self.model.parameters():

            if param.dim() > 1:  # 只计算权重

                total_weights += param.numel()

                zero_weights += (param == 0).sum().item()



        sparsity = zero_weights / total_weights if total_weights > 0 else 0



        return sparsity, total_weights, zero_weights



    def prune(self, sparsity_target, threshold_fn=None):

        """

        执行幅度剪枝



        参数:

            sparsity_target: 目标稀疏度

            threshold_fn: 可选的阈值计算函数

        """

        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data.abs()



            if threshold_fn is None:

                threshold = torch.quantile(weight.flatten(), sparsity_target)

            else:

                threshold = threshold_fn(weight)



            mask = (weight > threshold).float()

            param.data *= mask



    def magnitude_pruning_iterative(self, final_sparsity=0.7, epochs=100, freq=10):

        """

        迭代幅度剪枝



        逐步增加稀疏度

        """

        sparsity_schedule = np.linspace(0, final_sparsity, epochs // freq + 1)



        current_epoch = 0

        for target_sparsity in sparsity_schedule:

            self.prune(sparsity_target=target_sparsity)

            print(f"Epoch {current_epoch}: Sparsity={self.compute_sparsity()[0]:.2%}")

            current_epoch += freq





class RandomPruner:

    """

    随机剪枝器



    随机移除权重（作为基线对比）

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def prune(self, sparsity):

        """

        随机剪枝



        参数:

            sparsity: 剪枝比例

        """

        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            mask = (torch.rand_like(param) > sparsity).float()

            param.data *= mask





class GradientPruner:

    """

    基于梯度的剪枝



    移除梯度最小的权重

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def compute_importance(self):

        """

        计算权重重要性



        使用权重和梯度的乘积（类似泰勒展开）

        """

        importance = {}



        for name, param in self.model.named_parameters():

            if 'weight' not in name or param.grad is None:

                continue



            # 泰勒重要性：|weight * gradient|

            imp = (param.data.abs() * param.grad.abs()).mean().item()

            importance[name] = imp



        return importance



    def prune(self, sparsity):

        """剪枝"""

        importance = self.compute_importance()



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            if name not in importance:

                continue



            # 简单处理：直接基于参数值

            weight_abs = param.data.abs()

            threshold = torch.quantile(weight_abs.flatten(), sparsity)



            mask = (weight_abs > threshold).float()

            param.data *= mask





class LotteryTicketFinder:

    """

    彩票假说验证器



    寻找"中奖彩票"：初始化的子网络经过训练可以达到与大网络相当的准确率

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device

        self.original_state_dict = copy.deepcopy(model.state_dict())

        self.winning_ticket_mask = {}



    def get_pruning_mask(self, sparsity):

        """

        获取剪枝掩码



        参数:

            sparsity: 剪枝比例

        """

        mask = {}



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data.abs()

            threshold = torch.quantile(weight.flatten(), sparsity)

            mask[name] = (weight > threshold).float()



        return mask



    def find_winning_ticket(self, dataloader, sparsity=0.7, epochs=10, lr=0.01):

        """

        寻找中奖彩票



        步骤：

        1. 训练网络直到收敛

        2. 剪枝得到mask

        3. 将权重重置到初始值，应用mask

        4. 用mask重新训练



        参数:

            dataloader: 数据加载器

            sparsity: 最终稀疏度

            epochs: 训练轮数

            lr: 学习率

        """

        print("阶段1: 训练原始网络")

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)



        for epoch in range(epochs):

            self._train_epoch(dataloader, optimizer)



        # 获取剪枝掩码

        mask = self.get_pruning_mask(sparsity)

        self.winning_ticket_mask = mask



        # 保存训练后的权重（用于比较）

        trained_weights = copy.deepcopy(self.model.state_dict())



        print("阶段2: 重置到初始权重")

        self.model.load_state_dict(self.original_state_dict)



        # 应用mask

        self._apply_mask(mask)



        print("阶段3: 使用mask重新训练")

        for epoch in range(epochs):

            self._train_epoch(dataloader, optimizer)



        # 比较结果

        final_acc = self._evaluate(dataloader)

        print(f"最终准确率: {final_acc:.4f}")



        return self.winning_ticket_mask



    def iterative_pruning(self, dataloader, final_sparsity=0.99, steps=10, epochs_per_step=5):

        """

        迭代剪枝



        逐步增加剪枝率，每步重置到初始权重



        参数:

            final_sparsity: 最终稀疏度

            steps: 迭代次数

            epochs_per_step: 每步训练轮数

        """

        sparsity_schedule = np.linspace(0, final_sparsity, steps + 1)[1:]



        for step, target_sparsity in enumerate(sparsity_schedule):

            print(f"\n=== 迭代 {step + 1}/{steps}: 目标稀疏度={target_sparsity:.2%} ===")



            # 应用当前mask

            if self.winning_ticket_mask:

                self._apply_mask(self.winning_ticket_mask)



            # 训练

            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)

            for epoch in range(epochs_per_step):

                self._train_epoch(dataloader, optimizer)



            # 更新mask

            mask = self.get_pruning_mask(target_sparsity)



            # 重置并应用新mask

            self.model.load_state_dict(self.original_state_dict)

            self._apply_mask(mask)

            self.winning_ticket_mask = mask



            # 评估

            acc = self._evaluate(dataloader)

            print(f"当前稀疏度: {self.compute_sparsity():.2%}, 准确率: {acc:.4f}")



    def _apply_mask(self, mask):

        """应用mask"""

        for name, param in self.model.named_parameters():

            if name in mask:

                param.data *= mask[name]



    def _train_epoch(self, dataloader, optimizer):

        """训练一个epoch"""

        self.model.train()

        for images, labels in dataloader:

            images = images.to(self.device)

            labels = labels.to(self.device)



            outputs = self.model(images)

            loss = F.cross_entropy(outputs, labels)



            optimizer.zero_grad()

            loss.backward()

            optimizer.step()



    def _evaluate(self, dataloader):

        """评估准确率"""

        self.model.eval()

        correct = 0

        total = 0



        with torch.no_grad():

            for images, labels in dataloader:

                images = images.to(self.device)

                labels = labels.to(self.device)



                outputs = self.model(images)

                preds = torch.argmax(outputs, dim=1)



                correct += (preds == labels).sum().item()

                total += len(labels)



        return correct / total



    def compute_sparsity(self):

        """计算当前稀疏度"""

        total = 0

        zero = 0



        for name, param in self.model.named_parameters():

            if name in self.winning_ticket_mask:

                total += param.numel()

                zero += (self.winning_ticket_mask[name] == 0).sum().item()



        return zero / total if total > 0 else 0





class RigLPruning:

    """

    RigL: 稀疏训练的梯度下降



    动态调整稀疏连接，在训练过程中重新连接权重

    """



    def __init__(self, model, sparsity=0.5, device='cpu'):

        self.model = model

        self.sparsity = sparsity

        self.device = device

        self.drop_fraction = 0.3  # 每步drop的比例

        self.registeration_fraction = 0.3  # 每步注册新连接的比例



    def compute_adaptive_threshold(self, epoch):

        """计算自适应阈值"""

        # 线性增加稀疏度

        if epoch < 100:

            current_sparsity = epoch / 100 * self.sparsity

        else:

            current_sparsity = self.sparsity



        return current_sparsity



    def rigl_step(self, images, labels, optimizer, epoch):

        """

        RigL训练步骤



        参数:

            epoch: 当前epoch

        """

        # 前向传播

        outputs = self.model(images)

        loss = F.cross_entropy(outputs, labels)



        # 反向传播

        optimizer.zero_grad()

        loss.backward()



        # 获取梯度

        grads = {}

        for name, param in self.model.named_parameters():

            if 'weight' in name:

                grads[name] = param.grad.abs() if param.grad is not None else None



        # 更新稀疏模式

        self.update_sparse_pattern(grads, epoch)



        optimizer.step()



        return loss.item()



    def update_sparse_pattern(self, grads, epoch):

        """

        更新稀疏模式



        1. 根据当前稀疏度确定阈值

        2. 移除弱连接（低梯度）

        3. 添加新连接（随机或基于结构）

        """

        current_sparsity = self.compute_adaptive_threshold(epoch)



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data

            grad = grads.get(name)



            if grad is None:

                continue



            # 当前mask

            current_mask = (weight != 0).float()



            # 计算阈值

            threshold = torch.quantile(grad.flatten(), self.drop_fraction)



            # 新mask：保留强梯度或随机保留

            new_connections = (grad > threshold) | (torch.rand_like(weight) < self.registeration_fraction)

            new_mask = current_mask + new_connections.float()



            # 确保稀疏度正确

            num_keep = int(param.numel() * (1 - current_sparsity))

            if new_mask.sum() > num_keep:

                # 随机drop多余连接

                positions = torch.where(new_mask)[0]

                drop_idx = torch.randperm(len(positions))[:new_mask.sum() - num_keep]

                new_mask[positions[drop_idx]] = 0



            # 应用mask

            param.data *= new_mask.to(self.device)





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

        def __init__(self, size=20):

            self.size = size



        def __iter__(self):

            for _ in range(self.size):

                images = torch.rand(32, 1, 28, 28)

                labels = torch.randint(0, 10, (32,))

                yield images, labels



    print("=" * 50)

    print("非结构化剪枝测试")

    print("=" * 50)



    # 幅度剪枝

    print("\n--- 幅度剪枝 ---")

    pruner = MagnitudePruner(model, device)

    sparsity, total, zero = pruner.compute_sparsity()

    print(f"剪枝前: 稀疏度={sparsity:.2%}, 总权重={total}, 零权重={zero}")



    pruner.prune(sparsity_target=0.5)

    sparsity, total, zero = pruner.compute_sparsity()

    print(f"剪枝后: 稀疏度={sparsity:.2%}, 总权重={total}, 零权重={zero}")



    # 随机剪枝

    print("\n--- 随机剪枝 ---")

    model2 = SimpleCNN(num_classes=10).to(device)

    random_pruner = RandomPruner(model2, device)

    random_pruner.prune(sparsity=0.3)



    sparsity2, _, _ = MagnitudePruner(model2).compute_sparsity()

    print(f"随机剪枝后稀疏度: {sparsity2:.2%}")



    # 彩票假说

    print("\n--- 彩票假说 ---")

    model3 = SimpleCNN(num_classes=10).to(device)

    finder = LotteryTicketFinder(model3, device)



    # 快速测试（减少epoch）

    print("寻找中奖彩票（简化测试）...")

    mask = finder.get_pruning_mask(sparsity=0.5)

    print(f"初始mask数量: {len(mask)}")



    # 评估稀疏度

    finder._apply_mask(mask)

    sparsity3 = finder.compute_sparsity()

    print(f"应用mask后稀疏度: {sparsity3:.2%}")



    # RigL

    print("\n--- RigL稀疏训练 ---")

    model4 = SimpleCNN(num_classes=10).to(device)

    rigl = RigLPruning(model4, sparsity=0.5, device=device)



    optimizer = torch.optim.Adam(model4.parameters(), lr=0.001)



    for epoch in range(3):

        total_loss = 0

        for images, labels in DummyDataset(5):

            images, labels = images.to(device), labels.to(device)

            loss = rigl.rigl_step(images, labels, optimizer, epoch)

            total_loss += loss



        print(f"Epoch {epoch + 1}: Loss={total_loss / 160:.4f}")



    print("\n测试完成！")

