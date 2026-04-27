# -*- coding: utf-8 -*-

"""

算法实现：对抗机器学习 / detection



本文件实现 detection 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F

from scipy import stats





class StatisticalDetector:

    """

    基于统计特征的对抗样本检测器



    对抗样本在统计上往往与正常样本有差异

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device

        self.model.eval()



    def compute_statistical_features(self, images):

        """

        计算统计特征



        参数:

            images: 输入图像 [B, C, H, W]



        返回:

            features: 统计特征向量

        """

        features = []



        # 基本统计量

        features.append(images.mean(dim=(1, 2, 3)))  # 均值

        features.append(images.std(dim=(1, 2, 3)))   # 标准差

        features.append(images.min(dim=2)[0].min(dim=2)[0])  # 最小值

        features.append(images.max(dim=2)[0].max(dim=2)[0])  # 最大值



        # 分位数

        flat_images = images.reshape(len(images), -1)

        features.append(torch.quantile(flat_images, 0.25, dim=1))

        features.append(torch.quantile(flat_images, 0.75, dim=1))



        # 偏度和峰度（简化版）

        mean = flat_images.mean(dim=1)

        std = flat_images.std(dim=1)

        z = (flat_images - mean.view(-1, 1)) / (std.view(-1, 1) + 1e-8)

        skewness = (z ** 3).mean(dim=1)

        kurtosis = (z ** 4).mean(dim=1) - 3

        features.append(skewness)

        features.append(kurtosis)



        # 梯度统计

        grad_mean = []

        for img in images:

            img_grad = torch.abs(img[:, 1:] - img[:, :-1]).mean() + \

                      torch.abs(img[1:, :] - img[:-1, :]).mean()

            grad_mean.append(img_grad)



        features.append(torch.tensor(grad_mean, device=self.device))



        return torch.stack(features, dim=1)



    def fit_threshold(self, clean_images, percentile=95):

        """

        从干净样本学习检测阈值



        参数:

            clean_images: 干净图像集合

            percentile: 阈值百分位

        """

        with torch.no_grad():

            features = self.compute_statistical_features(clean_images)

            # 使用马氏距离作为异常度量

            mean = features.mean(dim=0)

            cov = torch.cov(features.T)

            cov_inv = torch.linalg.pinv(cov)



            self.threshold = 0.0

            for i in range(len(features)):

                diff = features[i] - mean

                maha_dist = torch.sqrt(diff @ cov_inv @ diff)

                self.threshold += maha_dist.item()



            self.threshold = self.threshold / len(features) * percentile / 100



    def detect(self, images):

        """

        检测对抗样本



        返回:

            is_adversarial: 布尔张量

            scores: 异常分数

        """

        with torch.no_grad():

            features = self.compute_statistical_features(images)



            # 计算马氏距离

            mean = features.mean(dim=0)

            cov = torch.cov(features.T)

            cov_inv = torch.linalg.pinv(cov)



            scores = []

            for i in range(len(features)):

                diff = features[i] - mean

                maha_dist = torch.sqrt(diff @ cov_inv @ diff + 1e-8)

                scores.append(maha_dist.item())



            scores = torch.tensor(scores)

            is_adversarial = scores > self.threshold



        return is_adversarial, scores





class LIDDetector:

    """

    基于局部内在维度（Local Intrinsic Dimensionality）的检测器



    LID测量样本周围邻域的扩张速度，对抗样本通常有异常的低维结构

    """



    def __init__(self, model, device='cpu', k=20):

        """

        参数:

            k: 近邻数

        """

        self.model = model

        self.device = device

        self.k = k



    def compute_lid(self, images, layer_name='fc1'):

        """

        计算图像的LID值



        参数:

            images: 输入图像

            layer_name: 用于提取特征的层名

        """

        self.model.eval()



        # 提取特征

        features = []

        handle = None



        def hook_fn(module, input, output):

            features.append(output.detach())



        for name, module in self.model.named_modules():

            if layer_name in name and 'fc' in name:

                handle = module.register_forward_hook(hook_fn)

                break



        with torch.no_grad():

            _ = self.model(images)



        if handle:

            handle.remove()



        if len(features) == 0:

            # 使用logits作为特征

            with torch.no_grad():

                features.append(self.model(images))



        feat = features[0].view(len(images), -1)



        # 计算k近邻距离

        dists = []

        for i in range(len(feat)):

            diff = feat - feat[i]

            distances = torch.norm(diff, dim=1, p=2)

            distances[i] = float('inf')  # 排除自身



            # k个最近邻的距离

            k_dist = torch.topk(distances, self.k, largest=False)[0]

            dists.append(k_dist)



        k_dists = torch.stack(dists)



        # LID估计：-k / sum(log(r_k / r_k-1))

        lids = []

        for i in range(len(k_dists)):

            kd = k_dists[i]

            # 避免log(0)

            kd = kd[kd > 1e-8]

            if len(kd) > 1:

                ratios = kd[1:] / (kd[:-1] + 1e-8)

                ratios = ratios[ratios > 0]

                if len(ratios) > 0:

                    lid = -self.k / (torch.log(ratios).sum() + 1e-8)

                    lids.append(lid.item())

                else:

                    lids.append(0.0)

            else:

                lids.append(0.0)



        return torch.tensor(lids, device=self.device)



    def fit(self, clean_images, adversarial_images=None):

        """

        训练检测器



        参数:

            clean_images: 干净样本

            adversarial_images: 对抗样本（用于校准）

        """

        clean_lids = self.compute_lid(clean_images)

        self.clean_mean = clean_lids.mean().item()

        self.clean_std = clean_lids.std().item()



        if adversarial_images is not None:

            adv_lids = self.compute_lid(adversarial_images)

            self.adv_mean = adv_lids.mean().item()

            self.adv_std = adv_lids.std().item()



    def detect(self, images, threshold=None):

        """

        检测对抗样本

        """

        lids = self.compute_lid(images)



        if threshold is None:

            # 使用clean样本的标准差作为阈值

            threshold = self.clean_mean + 3 * self.clean_std



        is_adv = lids > threshold



        return is_adv, lids





class LSBSteganalysisDetector:

    """

    基于LSB（最低有效位）特征的检测器



    对抗扰动往往修改了LSB位，与自然图像的LSB分布不同

    """



    def __init__(self, device='cpu'):

        self.device = device



    def extract_lsb_features(self, images):

        """

        提取LSB特征



        参数:

            images: [B, C, H, W] 归一化到[0,1]的图像



        返回:

            features: LSB特征

        """

        # 将图像转换到0-255范围

        pixel_vals = (images * 255).round().long()



        # 提取LSB

        lsb = (pixel_vals % 2).float()



        features = []



        # LSB统计

        features.append(lsb.mean(dim=(1, 2, 3)))  # LSB均值

        features.append(lsb.std(dim=(1, 2, 3)))   # LSB标准差



        # LSB配对相关性（相邻像素的LSB相关性）

        lsb_h = lsb[:, :, :, 1:] * lsb[:, :, :, :-1]  # 水平

        lsb_v = lsb[:, :, 1:, :] * lsb[:, :, :-1, :]  # 垂直

        features.append(lsb_h.mean(dim=(1, 2, 3)))

        features.append(lsb_v.mean(dim=(1, 2, 3)))



        # LSB过渡概率

        diff_h = torch.abs(lsb[:, :, :, 1:] - lsb[:, :, :, :-1])

        diff_v = torch.abs(lsb[:, :, 1:, :] - lsb[:, :, :-1, :])

        features.append(diff_h.mean(dim=(1, 2, 3)))

        features.append(diff_v.mean(dim=(1, 2, 3)))



        # 高位与LSB的相关性

        msb = (pixel_vals // 128).float()

        corr_h = (msb[:, :, :, 1:] * lsb[:, :, :, :-1]).mean(dim=(1, 2, 3))

        corr_v = (msb[:, :, 1:, :] * lsb[:, :, :-1, :]).mean(dim=(1, 2, 3))

        features.append(corr_h)

        features.append(corr_v)



        return torch.stack(features, dim=1)



    def fit(self, clean_images):

        """从干净样本学习"""

        self.clean_features = self.extract_lsb_features(clean_images)

        self.clean_mean = self.clean_features.mean(dim=0)

        self.clean_cov = torch.cov(self.clean_features.T)



    def detect(self, images, threshold_multiplier=3):

        """

        检测对抗样本

        """

        features = self.extract_lsb_features(images)



        # 计算与干净样本特征的差异

        diff = features - self.clean_mean



        # 使用马氏距离

        cov_inv = torch.linalg.pinv(self.clean_cov)

        scores = []

        for i in range(len(diff)):

            d = diff[i]

            maha = torch.sqrt(d @ cov_inv @ d)

            scores.append(maha.item())



        scores = torch.tensor(scores)

        threshold = threshold_multiplier * scores.mean()



        is_adv = scores > threshold



        return is_adv, scores





class ClassifierDetector(nn.Module):

    """

    基于二分类器的对抗样本检测器



    训练一个单独的分类器来判断输入是否为对抗样本

    """



    def __init__(self, input_dim=10, hidden_dim=128):

        super().__init__()

        self.detector = nn.Sequential(

            nn.Linear(input_dim, hidden_dim),

            nn.ReLU(),

            nn.Dropout(0.3),

            nn.Linear(hidden_dim, hidden_dim),

            nn.ReLU(),

            nn.Dropout(0.3),

            nn.Linear(hidden_dim, 2)  # 二分类：干净或对抗

        )



    def forward(self, features):

        return self.detector(features)



    def extract_features(self, model, images, device='cpu'):

        """

        从主模型提取用于检测的特征



        参数:

            model: 主分类模型

            images: 输入图像

        """

        model.eval()

        features_list = []



        # Hook获取中间层

        def hook_fn(module, input, output):

            features_list.append(output.detach())



        handles = []

        for name, module in model.named_modules():

            if 'fc' in name and 'output' not in name:

                handles.append(module.register_forward_hook(hook_fn))



        with torch.no_grad():

            _ = model(images)



        for h in handles:

            h.remove()



        # 组合特征

        if len(features_list) > 0:

            combined = torch.cat(features_list, dim=1)

        else:

            combined = model(images)



        return combined



    def train_detector(self, clean_features, adv_features, epochs=10, lr=0.001):

        """

        训练检测器



        参数:

            clean_features: 干净样本特征

            adv_features: 对抗样本特征

        """

        # 准备标签

        clean_labels = torch.zeros(len(clean_features))

        adv_labels = torch.ones(len(adv_features))



        X = torch.cat([clean_features, adv_features])

        y = torch.cat([clean_labels, adv_labels]).long()



        # 随机打乱

        perm = torch.randperm(len(X))

        X = X[perm]

        y = y[perm]



        optimizer = torch.optim.Adam(self.parameters(), lr=lr)

        criterion = nn.CrossEntropyLoss()



        self.train()

        for epoch in range(epochs):

            optimizer.zero_grad()

            outputs = self(X)

            loss = criterion(outputs, y)

            loss.backward()

            optimizer.step()



            if (epoch + 1) % 5 == 0:

                acc = (outputs.argmax(dim=1) == y).float().mean()

                print(f"Detector Epoch {epoch + 1}: Loss={loss.item():.4f}, Acc={acc:.2%}")



    def predict(self, features):

        """预测是否为对抗样本"""

        self.eval()

        with torch.no_grad():

            logits = self(features)

            probs = F.softmax(logits, dim=1)

            is_adv = probs[:, 1] > 0.5



        return is_adv, probs[:, 1]





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

    model.eval()



    # 生成测试数据

    torch.manual_seed(42)

    clean_images = torch.rand(50, 1, 28, 28).to(device)

    adv_images = clean_images + torch.randn_like(clean_images) * 0.05

    adv_images = torch.clamp(adv_images, 0, 1)



    test_labels = torch.randint(0, 10, (50,)).to(device)



    print("=" * 50)

    print("对抗样本检测测试")

    print("=" * 50)



    # 统计检测器

    print("\n--- 统计特征检测器 ---")

    stat_detector = StatisticalDetector(model, device)

    stat_detector.fit_threshold(clean_images[:30])



    is_adv_stat, scores_stat = stat_detector.detect(clean_images[30:])

    is_adv_stat_adv, scores_stat_adv = stat_detector.detect(adv_images[30:])



    print(f"干净样本异常分数: {scores_stat.mean():.4f}")

    print(f"对抗样本异常分数: {scores_stat_adv.mean():.4f}")



    # LID检测器

    print("\n--- LID检测器 ---")

    lid_detector = LIDDetector(model, device, k=10)

    lid_detector.fit(clean_images[:30], adv_images[:30])



    is_adv_lid, lids = lid_detector.detect(adv_images[30:])

    print(f"对抗样本LID均值: {lids.mean():.4f}")



    # LSB检测器

    print("\n--- LSB检测器 ---")

    lsb_detector = LSBSteganalysisDetector(device)

    lsb_detector.fit(clean_images[:30])



    is_adv_lsb, lsb_scores = lsb_detector.detect(adv_images[30:])

    print(f"LSB检测异常分数: {lsb_scores.mean():.4f}")



    # 分类器检测器

    print("\n--- 分类器检测器 ---")

    detector = ClassifierDetector(input_dim=10)



    # 简单特征模拟

    clean_feat = torch.rand(30, 10)

    adv_feat = torch.rand(30, 10) + 0.5



    detector.train_detector(clean_feat, adv_feat, epochs=20)



    test_feat = torch.rand(10, 10) + 0.3

    is_adv_cls, probs = detector.predict(test_feat)

    print(f"分类器检测: {is_adv_cls.sum()}/{len(is_adv_cls)} 被判定为对抗")



    print("\n测试完成！")

