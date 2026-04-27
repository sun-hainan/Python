# -*- coding: utf-8 -*-

"""

算法实现：对抗机器学习 / adversarial_generation



本文件实现 adversarial_generation 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class WhiteBoxAttacker:

    """

    白盒攻击器：拥有模型完整信息的攻击者



    使用PGD和FGSM作为主要攻击方法

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device

        self.model.to(device)

        self.model.eval()



    def fgsm_attack(self, images, labels, epsilon=0.03):

        """快速梯度符号法攻击"""

        images.requires_grad = True

        outputs = self.model(images)

        loss = F.cross_entropy(outputs, labels)

        self.model.zero_grad()

        loss.backward()



        grad = images.grad.data

        perturbation = epsilon * torch.sign(grad)

        adversarial = torch.clamp(images + perturbation, 0, 1).detach()



        return adversarial



    def pgd_attack(self, images, labels, epsilon=0.03, alpha=0.001, num_iter=40):

        """投影梯度下降攻击"""

        lower_bound = torch.clamp(images - epsilon, 0, 1)

        upper_bound = torch.clamp(images + epsilon, 0, 1)



        # 随机初始化

        adversarial = images.clone().uniform_(-epsilon, epsilon)

        adversarial = torch.clamp(adversarial, lower_bound, upper_bound).detach()



        for _ in range(num_iter):

            adversarial.requires_grad = True

            outputs = self.model(adversarial)

            loss = F.cross_entropy(outputs, labels)



            self.model.zero_grad()

            loss.backward()



            grad = adversarial.grad.data

            adversarial = torch.clamp(adversarial + alpha * torch.sign(grad), lower_bound, upper_bound).detach()



        return adversarial





class BlackBoxAttacker:

    """

    黑盒攻击器：只能查询模型输入输出，不知道内部结构



    使用替代模型（surrogate model）生成对抗样本

    攻击者通过观察模型对不同输入的预测来构建替代模型

    """



    def __init__(self, substitute_model, target_model, device='cpu'):

        """

        参数:

            substitute_model: 替代模型（攻击者训练的白盒模型）

            target_model: 目标模型（实际攻击目标）

            device: 计算设备

        """

        self.substitute_model = substitute_model

        self.target_model = target_model

        self.device = device

        self.substitute_model.to(device)

        self.target_model.to(device)



    def generate_adversarial(self, images, labels, epsilon=0.03, alpha=0.001, num_iter=40):

        """

        使用替代模型生成对抗样本，然后攻击目标模型



        参数:

            images: 原始图像

            labels: 真实标签

            epsilon: 扰动上界

            alpha: 步长

            num_iter: 迭代次数



        返回:

            adversarial_images: 对抗样本

        """

        # 使用替代模型生成对抗样本（白盒攻击）

        self.substitute_model.eval()

        lower_bound = torch.clamp(images - epsilon, 0, 1)

        upper_bound = torch.clamp(images + epsilon, 0, 1)



        adversarial = images.clone().uniform_(-epsilon, epsilon)

        adversarial = torch.clamp(adversarial, lower_bound, upper_bound).detach()



        for _ in range(num_iter):

            adversarial.requires_grad = True



            # 使用替代模型计算损失

            outputs = self.substitute_model(adversarial)

            loss = F.cross_entropy(outputs, labels)



            self.substitute_model.zero_grad()

            loss.backward()



            grad = adversarial.grad.data

            adversarial = torch.clamp(adversarial + alpha * torch.sign(grad), lower_bound, upper_bound).detach()



        return adversarial



    def query_based_attack(self, images, labels, num_queries=100, epsilon=0.03):

        """

        基于查询的攻击：通过多次查询估计梯度方向



        参数:

            num_queries: 查询次数

            epsilon: 扰动上界



        返回:

            adversarial_images: 对抗样本

        """

        batch_size = images.size(0)

        adversarial = images.clone()



        for i in range(num_queries):

            # 随机扰动

            perturbation = torch.randn_like(images) * epsilon * 0.1

            perturbed = torch.clamp(adversarial + perturbation, 0, 1)



            # 查询目标模型

            with torch.no_grad():

                outputs = self.target_model(perturbed)

                predictions = torch.argmax(outputs, dim=1)



            # 如果成功攻击，记录

            if (predictions != labels).any():

                adversarial = perturbed

                break



        # 使用估计的梯度进行攻击

        adversarial.requires_grad = True

        outputs = self.substitute_model(adversarial)

        loss = F.cross_entropy(outputs, labels)

        self.substitute_model.zero_grad()

        loss.backward()



        grad = adversarial.grad.data

        adversarial = torch.clamp(adversarial + epsilon * torch.sign(grad), 0, 1).detach()



        return adversarial





class TransferAttacker:

    """

    迁移攻击：利用一个模型生成的对抗样本攻击另一个模型



    对抗样本在不同模型之间具有一定迁移性，

    即在一个模型上生成的对抗样本往往也能欺骗其他模型

    """



    def __init__(self, source_model, device='cpu'):

        self.source_model = source_model

        self.device = device

        self.source_model.to(device)



    def generate_transferable_adversarial(self, images, labels, epsilon=0.03, alpha=0.001, num_iter=40):

        """

        生成具有高迁移性的对抗样本



        策略：

        1. 使用动量累积梯度（类似I-FGSM）

        2. 在多个模型上验证迁移性



        参数:

            images: 原始图像

            labels: 真实标签

            epsilon: 扰动上界

            alpha: 步长

            num_iter: 迭代次数



        返回:

            adversarial_images: 对抗样本

        """

        self.source_model.eval()

        adversarial = images.clone().detach()

        momentum = torch.zeros_like(images)



        lower_bound = torch.clamp(images - epsilon, 0, 1)

        upper_bound = torch.clamp(images + epsilon, 0, 1)



        for i in range(num_iter):

            adversarial.requires_grad = True



            outputs = self.source_model(adversarial)

            loss = F.cross_entropy(outputs, labels)



            self.source_model.zero_grad()

            loss.backward()



            # 计算梯度

            grad = adversarial.grad.data



            # 累积动量

            momentum = momentum * 0.9 + grad / torch.norm(grad.view(len(grad), -1), dim=1, p=1).view(len(grad), 1, 1, 1)



            # 使用动量更新

            adversarial = torch.clamp(adversarial + alpha * torch.sign(momentum), lower_bound, upper_bound).detach()



        return adversarial



    def multi_model_transfer(self, images, labels, model_ensemble, epsilon=0.03, alpha=0.001, num_iter=40):

        """

        多模型集成迁移攻击：同时考虑多个模型的梯度



        参数:

            model_ensemble: 模型列表

            epsilon: 扰动上界

            alpha: 步长

            num_iter: 迭代次数



        返回:

            adversarial_images: 对抗样本

        """

        adversarial = images.clone().detach()

        lower_bound = torch.clamp(images - epsilon, 0, 1)

        upper_bound = torch.clamp(images + epsilon, 0, 1)



        for _ in range(num_iter):

            adversarial.requires_grad = True



            # 聚合多个模型的梯度

            total_loss = 0

            for model in model_ensemble:

                model.eval()

                outputs = model(adversarial)

                loss = F.cross_entropy(outputs, labels)

                loss.backward()

                total_loss += loss.item()



            # 平均梯度

            grad = adversarial.grad.data / len(model_ensemble)



            adversarial = torch.clamp(adversarial + alpha * torch.sign(grad), lower_bound, upper_bound).detach()



        return adversarial





if __name__ == "__main__":

    # 定义两个不同的模型架构

    class ModelA(nn.Module):

        def __init__(self):

            super().__init__()

            self.conv = nn.Sequential(

                nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(),

                nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),

                nn.AdaptiveAvgPool2d(1)

            )

            self.fc = nn.Linear(64, 10)



        def forward(self, x):

            x = self.conv(x)

            x = x.view(x.size(0), -1)

            return self.fc(x)



    class ModelB(nn.Module):

        def __init__(self):

            super().__init__()

            self.conv = nn.Sequential(

                nn.Conv2d(1, 64, 5, padding=2), nn.ReLU(),

                nn.MaxPool2d(2),

                nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),

                nn.AdaptiveAvgPool2d(1)

            )

            self.fc = nn.Linear(128, 10)



        def forward(self, x):

            x = self.conv(x)

            x = x.view(x.size(0), -1)

            return self.fc(x)



    device = torch.device("cpu")

    model_a = ModelA().to(device)

    model_b = ModelB().to(device)

    model_a.eval()

    model_b.eval()



    torch.manual_seed(42)

    test_images = torch.rand(8, 1, 28, 28).to(device)

    test_labels = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7]).to(device)



    print("=" * 50)

    print("对抗样本生成测试（白盒/黑盒/迁移）")

    print("=" * 50)



    # 白盒攻击

    white_box = WhiteBoxAttacker(model_a, device)

    adv_white = white_box.pgd_attack(test_images, test_labels, epsilon=0.1, num_iter=20)



    with torch.no_grad():

        preds_white = torch.argmax(model_a(adv_white), dim=1)

        print(f"白盒攻击（模型A）: {preds_white.cpu().numpy()}")



    # 黑盒攻击

    black_box = BlackBoxAttacker(model_a, model_b, device)

    adv_black = black_box.generate_adversarial(test_images, test_labels, epsilon=0.1, num_iter=20)



    with torch.no_grad():

        preds_black_a = torch.argmax(model_a(adv_black), dim=1)

        preds_black_b = torch.argmax(model_b(adv_black), dim=1)

        print(f"黑盒攻击-源模型A: {preds_black_a.cpu().numpy()}")

        print(f"黑盒攻击-目标模型B: {preds_black_b.cpu().numpy()}")



    # 迁移攻击

    transfer = TransferAttacker(model_a, device)

    adv_transfer = transfer.generate_transferable_adversarial(test_images, test_labels, epsilon=0.1, num_iter=20)



    with torch.no_grad():

        preds_transfer_a = torch.argmax(model_a(adv_transfer), dim=1)

        preds_transfer_b = torch.argmax(model_b(adv_transfer), dim=1)

        print(f"迁移攻击-源模型A: {preds_transfer_a.cpu().numpy()}")

        print(f"迁移攻击-目标模型B: {preds_transfer_b.cpu().numpy()}")



    # 多模型集成迁移

    ensemble = [model_a, model_b]

    adv_ensemble = transfer.multi_model_transfer(test_images, test_labels, ensemble, epsilon=0.1, num_iter=20)



    with torch.no_grad():

        preds_ensemble_a = torch.argmax(model_a(adv_ensemble), dim=1)

        preds_ensemble_b = torch.argmax(model_b(adv_ensemble), dim=1)

        print(f"集成迁移-模型A: {preds_ensemble_a.cpu().numpy()}")

        print(f"集成迁移-模型B: {preds_ensemble_b.cpu().numpy()}")



    print("\n测试完成！")

