# -*- coding: utf-8 -*-

"""

算法实现：对抗机器学习 / adversarial_training



本文件实现 adversarial_training 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class StandardAdversarialTraining:

    """

    标准对抗训练（Standard AT）



    在每个训练步骤中同时使用干净样本和PGD对抗样本

    """



    def __init__(self, model, optimizer, device='cpu', epsilon=0.03, alpha=0.001, num_iter=7):

        self.model = model

        self.optimizer = optimizer

        self.device = device

        self.epsilon = epsilon

        self.alpha = alpha

        self.num_iter = num_iter



    def pgd_attack(self, images, labels):

        """生成PGD对抗样本"""

        lower_bound = torch.clamp(images - self.epsilon, 0, 1)

        upper_bound = torch.clamp(images + self.epsilon, 0, 1)



        adversarial = images.clone().uniform_(-self.epsilon, self.epsilon)

        adversarial = torch.clamp(adversarial, lower_bound, upper_bound).detach()



        for _ in range(self.num_iter):

            adversarial.requires_grad = True

            outputs = self.model(adversarial)

            loss = F.cross_entropy(outputs, labels)



            self.model.zero_grad()

            loss.backward()



            grad = adversarial.grad.data

            adversarial = torch.clamp(adversarial + self.alpha * torch.sign(grad), lower_bound, upper_bound).detach()



        return adversarial



    def train_step(self, images, labels):

        """一步训练"""

        self.model.train()



        # 干净样本损失

        clean_outputs = self.model(images)

        clean_loss = F.cross_entropy(clean_outputs, labels)



        # 生成对抗样本

        adversarial = self.pgd_attack(images, labels)



        # 对抗样本损失

        adv_outputs = self.model(adversarial)

        adv_loss = F.cross_entropy(adv_outputs, labels)



        # 总损失

        loss = clean_loss + adv_loss



        self.optimizer.zero_grad()

        loss.backward()

        self.optimizer.step()



        # 计算准确率

        clean_acc = (torch.argmax(clean_outputs, dim=1) == labels).float().mean().item()

        adv_acc = (torch.argmax(adv_outputs, dim=1) == labels).float().mean().item()



        return loss.item(), clean_acc, adv_acc





class FreeAdversarialTraining:

    """

    Free Adversarial Training



    通过累积梯度来加速对抗训练

    """



    def __init__(self, model, optimizer, device='cpu', epsilon=0.03, num_replays=4):

        self.model = model

        self.optimizer = optimizer

        self.device = device

        self.epsilon = epsilon

        self.num_replays = num_replays



    def train_step(self, images, labels):

        """Free训练步骤"""

        self.model.train()



        batch_size = len(labels)

        images = images.to(self.device)

        labels = labels.to(self.device)



        # 累积梯度

        cumulative_grads = None



        for replay in range(self.num_replays):

            images = images.detach().requires_grad_(True)



            outputs = self.model(images)

            loss = F.cross_entropy(outputs, labels)



            self.optimizer.zero_grad()

            loss.backward()



            if cumulative_grads is None:

                cumulative_grads = [p.grad.clone() for p in self.model.parameters() if p.grad is not None]

            else:

                for i, p in enumerate([p for p in self.model.parameters() if p.grad is not None]):

                    cumulative_grads[i] += p.grad



            # 更新图像（生成新的对抗样本）

            if replay < self.num_replays - 1:

                grad = images.grad.data

                images = images.detach() + self.epsilon * torch.sign(grad)

                images = torch.clamp(images, 0, 1).detach()



        # 应用累积梯度

        self.optimizer.zero_grad()

        for p, g in zip([p for p in self.model.parameters() if p.grad is not None], cumulative_grads):

            p.grad = g

        self.optimizer.step()



        return loss.item()





class TRADESAdversarialTraining:

    """

    TRADES (TRAditional vs. Distillation) 对抗训练



    通过KL散度使干净样本和对抗样本的输出分布一致

    """



    def __init__(self, model, optimizer, device='cpu', epsilon=0.03, alpha=1.0, num_iter=7, beta=1.0):

        self.model = model

        self.optimizer = optimizer

        self.device = device

        self.epsilon = epsilon

        self.alpha = alpha  # TRADES损失权重

        self.beta = beta    # KL散度权重

        self.num_iter = num_iter



    def pgd_attack(self, images, labels):

        """PGD攻击"""

        lower_bound = torch.clamp(images - self.epsilon, 0, 1)

        upper_bound = torch.clamp(images + self.epsilon, 0, 1)



        adversarial = images.clone().uniform_(-self.epsilon, self.epsilon)

        adversarial = torch.clamp(adversarial, lower_bound, upper_bound).detach()



        for _ in range(self.num_iter):

            adversarial.requires_grad = True

            outputs = self.model(adversarial)

            self.model.zero_grad()



            # 使用logits而不是one-hot

            loss = -F.cross_entropy(outputs, labels)

            loss.backward()



            grad = adversarial.grad.data

            adversarial = torch.clamp(adversarial + 0.007 * torch.sign(grad), lower_bound, upper_bound).detach()



        return adversarial



    def train_step(self, images, labels):

        """TRADES训练步骤"""

        self.model.train()

        images = images.to(self.device)

        labels = labels.to(self.device)



        # 干净样本的logits

        clean_outputs = self.model(images)



        # 生成对抗样本

        adversarial = self.pgd_attack(images, labels)

        adv_outputs = self.model(adversarial)



        # 分类损失

        ce_loss = F.cross_entropy(clean_outputs, labels)



        # KL散度损失：使对抗样本的输出分布接近干净样本

        kl_loss = F.kl_div(

            F.log_softmax(adv_outputs, dim=1),

            F.softmax(clean_outputs, dim=1),

            reduction='batchmean'

        )



        # 总损失

        loss = ce_loss + self.beta * kl_loss



        self.optimizer.zero_grad()

        loss.backward()

        self.optimizer.step()



        return loss.item(), ce_loss.item(), kl_loss.item()





class MARTAdversarialTraining:

    """

    MART (Misclassification Aware Adversarial Training) 对抗训练



    区别对待分类正确和分类错误的对抗样本

    """



    def __init__(self, model, optimizer, device='cpu', epsilon=0.03, alpha=1.0, num_iter=7, beta=6.0):

        self.model = model

        self.optimizer = optimizer

        self.device = device

        self.epsilon = epsilon

        self.alpha = alpha

        self.beta = beta

        self.num_iter = num_iter



    def pgd_attack(self, images, labels):

        """生成PGD对抗样本"""

        lower = torch.clamp(images - self.epsilon, 0, 1)

        upper = torch.clamp(images + self.epsilon, 0, 1)



        adversarial = images.clone().uniform_(-self.epsilon, self.epsilon)

        adversarial = torch.clamp(adversarial, lower, upper).detach()



        for _ in range(self.num_iter):

            adversarial.requires_grad = True

            outputs = self.model(adversarial)

            loss = F.cross_entropy(outputs, labels)



            self.model.zero_grad()

            loss.backward()



            grad = adversarial.grad.data

            adversarial = torch.clamp(adversarial + 0.01 * torch.sign(grad), lower, upper).detach()



        return adversarial



    def train_step(self, images, labels):

        """MART训练步骤"""

        self.model.train()

        images = images.to(self.device)

        labels = labels.to(self.device)



        # 干净样本预测

        clean_outputs = self.model(images)

        clean_preds = torch.argmax(clean_outputs, dim=1)

        clean_correct = (clean_preds == labels)



        # 生成对抗样本

        adversarial = self.pgd_attack(images, labels)

        adv_outputs = self.model(adversarial)

        adv_preds = torch.argmax(adv_outputs, dim=1)



        # 分类损失（只对干净样本）

        if clean_correct.any():

            ce_loss = F.cross_entropy(clean_outputs[clean_correct], labels[clean_correct])

        else:

            ce_loss = torch.tensor(0.0, device=self.device)



        # MART损失：关注被错误分类的对抗样本

        # 使用BCE作为置信度损失

        probs = F.softmax(adv_outputs, dim=1)

        one_hot = F.one_hot(labels, num_classes=probs.size(1)).float()



        # 对抗边界损失

        conf_margin = 0.5

        confidence = (probs * one_hot).sum(dim=1)

        mart_loss = (1 - confidence).clamp(min=0).mean()



        # 总损失

        loss = ce_loss + self.beta * mart_loss



        self.optimizer.zero_grad()

        loss.backward()

        self.optimizer.step()



        return loss.item(), ce_loss.item(), mart_loss.item()





class AdversarialTrainingSuite:

    """

    对抗训练套件：统一接口



    支持多种对抗训练方法的切换

    """



    def __init__(self, model, optimizer, device='cpu', method='standard', **kwargs):

        self.model = model

        self.optimizer = optimizer

        self.device = device

        self.method = method



        # 通用参数

        self.epsilon = kwargs.get('epsilon', 0.03)

        self.alpha = kwargs.get('alpha', 0.001)

        self.num_iter = kwargs.get('num_iter', 7)



        # 创建对应的训练器

        if method == 'standard':

            self.trainer = StandardAdversarialTraining(

                model, optimizer, device, self.epsilon, self.alpha, self.num_iter

            )

        elif method == 'free':

            self.trainer = FreeAdversarialTraining(

                model, optimizer, device, self.epsilon, kwargs.get('num_replays', 4)

            )

        elif method == 'trades':

            self.trainer = TRADESAdversarialTraining(

                model, optimizer, device, self.epsilon, self.alpha, self.num_iter,

                kwargs.get('beta', 1.0)

            )

        elif method == 'mart':

            self.trainer = MARTAdversarialTraining(

                model, optimizer, device, self.epsilon, self.alpha, self.num_iter,

                kwargs.get('beta', 6.0)

            )

        else:

            raise ValueError(f"Unknown method: {method}")



    def train_step(self, images, labels):

        """执行训练步骤"""

        if self.method in ['standard', 'trades', 'mart']:

            return self.trainer.train_step(images, labels)

        else:

            loss = self.trainer.train_step(images, labels)

            return loss, 0.0, 0.0



    def train_epoch(self, dataloader):

        """训练一个epoch"""

        total_loss = 0.0

        total_clean_acc = 0.0

        total_adv_acc = 0.0

        num_batches = 0



        for images, labels in dataloader:

            result = self.train_step(images, labels)

            if len(result) == 3:

                loss, clean_acc, adv_acc = result

                total_clean_acc += clean_acc

                total_adv_acc += adv_acc

            else:

                loss = result



            total_loss += loss

            num_batches += 1



        return {

            'loss': total_loss / num_batches,

            'clean_acc': total_clean_acc / num_batches if num_batches > 0 else 0,

            'adv_acc': total_adv_acc / num_batches if num_batches > 0 else 0

        }





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



    # 虚拟数据

    class DummyDataset:

        def __init__(self, size=10):

            self.size = size



        def __iter__(self):

            for _ in range(self.size):

                images = torch.rand(32, 1, 28, 28)

                labels = torch.randint(0, 10, (32,))

                yield images, labels



    device = torch.device("cpu")

    print("=" * 50)

    print("对抗训练完整套件测试")

    print("=" * 50)



    # 测试各种训练方法

    for method in ['standard', 'free', 'trades', 'mart']:

        print(f"\n--- {method.upper()} ---")



        model = SimpleCNN(num_classes=10).to(device)

        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)



        trainer = AdversarialTrainingSuite(

            model, optimizer, device,

            method=method,

            epsilon=0.1,

            num_iter=5

        )



        for epoch in range(3):

            result = trainer.train_epoch(DummyDataset(5))

            print(f"Epoch {epoch + 1}: Loss={result['loss']:.4f}, "

                  f"Clean={result['clean_acc']:.2%}, Adv={result['adv_acc']:.2%}")



    print("\n测试完成！")

