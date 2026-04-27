# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / nas_darts



本文件实现 nas_darts 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F

from typing import List, Tuple, Dict





class Operation:

    """

    可搜索的操作定义



    包括：卷积、池化、跳连、零操作等

    """



    def __init__(self, C_in, C_out, stride=1, affine=True):

        self.C_in = C_in

        self.C_out = C_out

        self.stride = stride

        self.affine = affine



    def __call__(self, x, op_index):

        """执行操作"""

        return x





class SearchSpace:

    """

    DARTS搜索空间

    """



    # 可选操作

    OPS = {

        'none': lambda C, stride, affine: Zero(stride),

        'skip_connect': lambda C, stride, affine: Identity() if stride == 1 else FactorizedReduce(C, affine),

        'sep_conv_3x3': lambda C, stride, affine: SepConv(C, C, 3, stride, 1, affine=affine),

        'sep_conv_5x5': lambda C, stride, affine: SepConv(C, C, 5, stride, 2, affine=affine),

        'dil_conv_3x3': lambda C, stride, affine: DilConv(C, C, 3, stride, 2, 2, affine=affine),

        'dil_conv_5x5': lambda C, stride, affine: DilConv(C, C, 5, stride, 4, 2, affine=affine),

        'avg_pool_3x3': lambda C, stride, affine: nn.AvgPool2d(3, stride=stride, padding=1, count_include_pad=False),

        'max_pool_3x3': lambda C, stride, affine: nn.MaxPool2d(3, stride=stride, padding=1),

    }



    @staticmethod

    def get_op(name, C, stride, affine):

        """获取操作"""

        if name in SearchSpace.OPS:

            return SearchSpace.OPS[name](C, stride, affine)

        return nn.Identity()





class Zero(nn.Module):

    """零操作"""



    def __init__(self, stride):

        super().__init__()

        self.stride = stride



    def forward(self, x):

        return x * 0





class Identity(nn.Module):

    """恒等映射"""



    def forward(self, x):

        return x





class FactorizedReduce(nn.Module):

    """因子化降维"""



    def __init__(self, C_out, affine=True):

        super().__init__()

        self.conv1 = nn.Conv2d(C_out, C_out // 2, 1, stride=2, padding=0, bias=not affine)

        self.conv2 = nn.Conv2d(C_out, C_out // 2, 1, stride=2, padding=0, bias=not affine)

        self.bn = nn.BatchNorm2d(C_out, affine=affine)



    def forward(self, x):

        x = torch.cat([self.conv1(x), self.conv2(x[:, :, 1:, 1:])], dim=1)

        return self.bn(x)





class SepConv(nn.Module):

    """深度可分离卷积"""



    def __init__(self, C_in, C_out, kernel_size, stride, padding, affine=True):

        super().__init__()

        self.net = nn.Sequential(

            nn.ReLU(inplace=False),

            nn.Conv2d(C_in, C_in, kernel_size, stride, padding, groups=C_in, bias=not affine),

            nn.Conv2d(C_in, C_in, 1, stride=1, padding=0, bias=not affine),

            nn.BatchNorm2d(C_in, affine=affine),

            nn.ReLU(inplace=False),

            nn.Conv2d(C_in, C_in, kernel_size, 1, padding, groups=C_in, bias=not affine),

            nn.Conv2d(C_in, C_out, 1, stride=1, padding=0, bias=not affine),

            nn.BatchNorm2d(C_out, affine=affine),

        )



    def forward(self, x):

        return self.net(x)





class DilConv(nn.Module):

    """空洞卷积"""



    def __init__(self, C_in, C_out, kernel_size, stride, padding, dilation, affine=True):

        super().__init__()

        self.net = nn.Sequential(

            nn.ReLU(inplace=False),

            nn.Conv2d(C_in, C_in, kernel_size, stride, padding, dilation=dilation, groups=C_in, bias=not affine),

            nn.Conv2d(C_in, C_out, 1, stride=1, padding=0, bias=not affine),

            nn.BatchNorm2d(C_out, affine=affine),

        )



    def forward(self, x):

        return self.net(x)





class MixedOp(nn.Module):

    """

    混合操作



    使用softmax加权组合多个操作

    """



    def __init__(self, C, stride, affine=True):

        super().__init__()

        self._ops = nn.ModuleDict()

        self._candidate_names = []



        for name, op in SearchSpace.OPS.items():

            if name == 'none':

                continue

            self._ops[name] = op(C, stride, affine)

            self._candidate_names.append(name)



        # 初始化参数

        num_ops = len(self._candidate_names)

        self._params = nn.Parameter(torch.zeros(num_ops))



    def forward(self, x):

        """

        可微分前向传播



        使用softmax权重组合所有操作

        """

        weights = F.softmax(self._params, dim=0)



        return sum(weights[i] * self._ops[name](x)

                   for i, name in enumerate(self._candidate_names))



    def get_weights(self):

        """获取当前权重"""

        return F.softmax(self._params, dim=0)



    def get_architecture(self):

        """获取当前选择的架构"""

        weights = self.get_weights()

        best_idx = weights.argmax().item()

        return self._candidate_names[best_idx]





class Cell(nn.Module):

    """

    DARTS的Cell结构



    包含N个节点的有向无环图

    """



    def __init__(self, num_nodes, C_in, C_out, stride=1, affine=True):

        super().__init__()

        self.num_nodes = num_nodes

        self.C_in = C_in

        self.C_out = C_out



        # 预处理（如果输入维度不匹配）

        if C_in != C_out or stride != 1:

            self.preprocess = nn.Sequential(

                nn.Conv2d(C_in, C_out, 1, stride=stride, padding=0, bias=not affine),

                nn.BatchNorm2d(C_out, affine=affine)

            )

        else:

            self.preprocess = Identity()



        # 节点间的混合操作

        self._ops = nn.ModuleDict()

        self._edges = []



        for i in range(num_nodes):

            for j in range(i + 1, num_nodes):

                edge_key = f"{i}_{j}"

                self._ops[edge_key] = MixedOp(C_out, stride=1, affine=affine)

                self._edges.append(edge_key)



    def forward(self, s0, s1):

        """s0, s1是输入节点"""

        states = [self.preprocess(s0), self.preprocess(s1)]



        for i in range(2, self.num_nodes):

            # 聚合所有前驱节点的输出

            node_input = torch.zeros_like(states[0])



            for j in range(i):

                edge_key = f"{j}_{i}"

                if edge_key in self._ops:

                    node_input += self._ops[edge_key](states[j])



            states.append(node_input)



        return torch.cat(states[-2:], dim=1)  # 返回最后两个节点的输出





class DARTSNetwork(nn.Module):

    """

    DARTS搜索网络

    """



    def __init__(self, num_classes=10, num_cells=14, num_nodes=4, C=16):

        super().__init__()

        self.num_cells = num_cells

        self.num_nodes = num_nodes

        self.C = C



        # 初始层

        self.stem = nn.Sequential(

            nn.Conv2d(1, C, 3, padding=1, bias=False),

            nn.BatchNorm2d(C)

        )



        # 单元格

        self.cells = nn.ModuleList()

        C_out = C



        for i in range(num_cells):

            if i in [num_cells // 3, 2 * num_cells // 3]:

                # 下采样

                C_out *= 2

                stride = 2

            else:

                stride = 1



            cell = Cell(num_nodes, C, C_out, stride)

            self.cells.append(cell)

            C = C_out



        # 分类头

        self.classifier = nn.Sequential(

            nn.AdaptiveAvgPool2d(1),

            nn.Flatten(),

            nn.Linear(C, num_classes)

        )



        self._initialize_weights()



    def forward(self, x):

        s0 = s1 = self.stem(x)



        for cell in self.cells:

            s0, s1 = s1, cell(s0, s1)



        return self.classifier(s1)



    def _initialize_weights(self):

        for m in self.modules():

            if isinstance(m, nn.Conv2d):

                nn.init.kaiming_normal_(m.weight, mode='fan_out')

                if m.bias is not None:

                    nn.init.zeros_(m.bias)

            elif isinstance(m, nn.BatchNorm2d):

                if m.weight is not None:

                    nn.init.ones_(m.weight)

                if m.bias is not None:

                    nn.init.zeros_(m.bias)



    def get_architecture_weights(self):

        """获取架构权重"""

        arch_weights = {}



        for cell_idx, cell in enumerate(self.cells):

            cell_weights = {}

            for edge_key, op in cell._ops.items():

                weights = op.get_weights().detach().cpu().numpy()

                arch_weights[f"cell_{cell_idx}_{edge_key}"] = {

                    op_name: w for op_name, w in zip(op._candidate_names, weights)

                }



        return arch_weights



    def get_final_architecture(self):

        """获取最终选择的架构"""

        arch = []



        for cell_idx, cell in enumerate(self.cells):

            cell_arch = {}

            for edge_key, op in cell._ops.items():

                cell_arch[edge_key] = op.get_architecture()

            arch.append(cell_arch)



        return arch





class DARTSOptimizer:

    """

    DARTS优化器



    交替优化网络权重和架构参数

    """



    def __init__(self, model, device='cpu', lr=0.025, arch_lr=0.001):

        self.model = model

        self.device = device

        self.lr = lr

        self.arch_lr = arch_lr



    def step(self, images, labels, unrolled=False):

        """

        一步优化



        参数:

            images: 输入

            labels: 标签

            unrolled: 是否使用unrolled优化

        """

        if unrolled:

            self._unrolled_step(images, labels)

        else:

            self._bilevel_step(images, labels)



    def _bilevel_step(self, images, labels):

        """

        双层优化



        1. 更新架构参数（固定权重）

        2. 更新网络权重

        """

        # Step 1: 更新架构参数

        arch_optimizer = torch.optim.Adam(

            self._get_arch_params(),

            lr=self.arch_lr

        )



        for edge_key, op in self._get_arch_ops():

            arch_optimizer.zero_grad()



            # 近似：只计算一次前向

            outputs = self.model(images)

            loss = F.cross_entropy(outputs, labels)



            # 梯度反向到架构参数

            loss.backward()

            arch_optimizer.step()



        # Step 2: 更新网络权重

        weight_optimizer = torch.optim.SGD(

            self._get_weight_params(),

            lr=self.lr,

            momentum=0.9,

            weight_decay=3e-4

        )



        for edge_key, op in self._get_arch_ops():

            # 临时移除架构参数的梯度

            for p in op.parameters():

                p.requires_grad = False



        weight_optimizer.zero_grad()

        outputs = self.model(images)

        loss = F.cross_entropy(outputs, labels)

        loss.backward()

        weight_optimizer.step()



        for edge_key, op in self._get_arch_ops():

            for p in op.parameters():

                p.requires_grad = True



    def _unrolled_step(self, images, labels):

        """Unrolled优化（计算量更大但更精确）"""

        # 简化的unrolled步骤

        self._bilevel_step(images, labels)



    def _get_arch_params(self):

        """获取架构参数"""

        arch_params = []

        for cell in self.model.cells:

            for op in cell._ops.values():

                arch_params.extend(op._params)

        return arch_params



    def _get_arch_ops(self):

        """获取所有架构操作"""

        ops = []

        for cell in self.model.cells:

            for edge_key, op in cell._ops.items():

                ops.append((edge_key, op))

        return ops



    def _get_weight_params(self):

        """获取网络权重参数"""

        weight_params = []

        for name, param in self.model.named_parameters():

            if 'cells' not in name and 'classifier' not in name:

                weight_params.append(param)

            elif 'classifier' in name:

                weight_params.append(param)

        return weight_params





def darts_search(num_epochs=50):

    """

    运行DARTS搜索

    """

    device = torch.device("cpu")



    # 创建搜索网络

    model = DARTSNetwork(num_classes=10, num_cells=8, num_nodes=4, C=16).to(device)

    optimizer = DARTSOptimizer(model, device)



    # 虚拟数据

    class DummyDataset:

        def __init__(self, size=100):

            self.size = size



        def __iter__(self):

            for _ in range(self.size):

                images = torch.rand(32, 1, 32, 32)

                labels = torch.randint(0, 10, (32,))

                yield images, labels



    print("=" * 50)

    print("DARTS架构搜索")

    print("=" * 50)



    for epoch in range(num_epochs):

        for images, labels in DummyDataset(20):

            images = images.to(device)

            labels = labels.to(device)



            optimizer.step(images, labels, unrolled=False)



        if (epoch + 1) % 10 == 0:

            arch = model.get_final_architecture()

            print(f"\nEpoch {epoch + 1} 架构选择:")

            for i, cell_arch in enumerate(arch[:2]):

                print(f"  Cell {i}: {cell_arch}")



    return model





if __name__ == "__main__":

    darts_search(num_epochs=20)



    print("\n测试完成！")

