# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / explainability



本文件实现 explainability 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class ActivationVisualizer:

    """

    激活值可视化器

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device

        self.activations = {}

        self.hooks = []



    def register_hooks(self, layer_names=None):

        """注册hook获取激活值"""

        def hook_fn(name):

            def hook(module, input, output):

                self.activations[name] = output.detach()

            return hook



        for name, module in self.model.named_modules():

            if layer_names is None or name in layer_names:

                handle = module.register_forward_hook(hook_fn(name))

                self.hooks.append(handle)



    def remove_hooks(self):

        """移除hooks"""

        for handle in self.hooks:

            handle.remove()

        self.hooks = []



    def get_activations(self, images, layer_name):

        """获取特定层的激活"""

        self.activations = {}

        with torch.no_grad():

            _ = self.model(images)



        return self.activations.get(layer_name)



    def compute_saliency(self, images, labels):

        """

        计算显著图（Saliency Map）



        使用梯度方法

        """

        images.requires_grad = True

        outputs = self.model(images)



        self.model.zero_grad()

        loss = F.cross_entropy(outputs, labels)

        loss.backward()



        # 梯度绝对值作为显著度

        saliency = images.grad.data.abs()



        return saliency





class LayerImportanceAnalyzer:

    """

    层重要性分析

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def compute_gradient_based_importance(self, dataloader):

        """基于梯度的重要性"""

        importance = {}



        for name, param in self.model.named_parameters():

            if 'weight' in name:

                param.requires_grad = True



        total_grad = {name: 0 for name, _ in self.model.named_parameters() if 'weight' in name[0]}



        for images, labels in dataloader:

            images = images.to(self.device)

            labels = labels.to(self.device)



            outputs = self.model(images)

            loss = F.cross_entropy(outputs, labels)



            self.model.zero_grad()

            loss.backward()



            for name, param in self.model.named_parameters():

                if param.grad is not None:

                    total_grad[name] += param.grad.abs().mean().item()



        return total_grad



    def compute_activation_based_importance(self, images):

        """基于激活的重要性"""

        activations = {}

        hooks = []



        def hook_fn(name):

            def hook(module, input, output):

                activations[name] = output.detach().mean().item()

            return hook



        for name, module in self.model.named_modules():

            handle = module.register_forward_hook(hook_fn(name))

            hooks.append(handle)



        with torch.no_grad():

            _ = self.model(images)



        for handle in hooks:

            handle.remove()



        return activations





class NeuralDebugger:

    """

    神经网络调试器

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def check_nan_gradients(self):

        """检查NaN梯度"""

        nan_params = []



        for name, param in self.model.named_parameters():

            if param.grad is not None:

                if torch.isnan(param.grad).any():

                    nan_params.append(name)



        return nan_params



    def check_dead_neurons(self, dataloader):

        """检查死亡神经元"""

        activation_sums = {}



        hooks = []

        handles = []



        def hook_fn(name):

            def hook(module, input, output):

                if isinstance(output, torch.Tensor):

                    # 计算平均激活

                    mean_act = output.mean().item()

                    if name not in activation_sums:

                        activation_sums[name] = []

                    activation_sums[name].append(mean_act)

            return hook



        for name, module in self.model.named_modules():

            handle = module.register_forward_hook(hook_fn(name))

            handles.append(handle)



        # 运行数据

        for images, _ in dataloader:

            images = images.to(self.device)

            with torch.no_grad():

                _ = self.model(images)



        for handle in handles:

            handle.remove()



        # 找出死亡神经元

        dead_neurons = {}

        for name, acts in activation_sums.items():

            if sum(acts) < 1e-6:

                dead_neurons[name] = len(acts)



        return dead_neurons



    def check_gradient_explosion(self):

        """检查梯度爆炸"""

        max_grad = 0.0

        max_param = None



        for name, param in self.model.named_parameters():

            if param.grad is not None:

                grad_norm = param.grad.norm().item()

                if grad_norm > max_grad:

                    max_grad = grad_norm

                    max_param = name



        return max_grad, max_param





class FeatureExtractor:

    """

    特征提取器

    """



    def __init__(self, model, layer_name, device='cpu'):

        self.model = model

        self.layer_name = layer_name

        self.device = device

        self.features = None



        self._register_hook()



    def _register_hook(self):

        """注册hook"""

        def hook_fn(module, input, output):

            self.features = output.detach()



        for name, module in self.model.named_modules():

            if self.layer_name in name:

                module.register_forward_hook(hook_fn)

                break



    def extract(self, images):

        """提取特征"""

        with torch.no_grad():

            _ = self.model(images)

            return self.features





if __name__ == "__main__":

    class SimpleCNN(nn.Module):

        def __init__(self):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)

            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)

            self.fc1 = nn.Linear(64 * 7 * 7, 128)

            self.fc2 = nn.Linear(128, 10)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    device = torch.device("cpu")

    model = SimpleCNN().to(device)



    class DummyDataset:

        def __init__(self, size=5):

            self.size = size



        def __iter__(self):

            for _ in range(self.size):

                yield torch.rand(8, 1, 28, 28), torch.randint(0, 10, (8,))



    print("=" * 50)

    print("可解释性工具测试")

    print("=" * 50)



    # 激活可视化

    print("\n--- 激活可视化 ---")

    visualizer = ActivationVisualizer(model, device)

    visualizer.register_hooks(['conv1', 'conv2'])



    test_images = torch.rand(4, 1, 28, 28)

    acts = visualizer.get_activations(test_images, 'conv1')

    print(f"conv1激活形状: {acts.shape if acts is not None else 'None'}")



    # 显著图

    print("\n--- 显著图 ---")

    saliency = visualizer.compute_saliency(test_images, torch.tensor([0, 1, 2, 3]))

    print(f"显著图形状: {saliency.shape}")



    # 调试器

    print("\n--- 神经网络调试器 ---")

    debugger = NeuralDebugger(model, device)



    nan_params = debugger.check_nan_gradients()

    print(f"NaN梯度参数: {nan_params if nan_params else 'None'}")



    dead = debugger.check_dead_neurons(DummyDataset(3))

    print(f"死亡神经元: {len(dead)} 层")



    print("\n测试完成！")

