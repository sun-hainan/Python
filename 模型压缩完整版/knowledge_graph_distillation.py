# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / knowledge_graph_distillation



本文件实现 knowledge_graph_distillation 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





class KnowledgeGraphDistiller:

    """

    知识图谱蒸馏器



    使用类别关系图结构辅助蒸馏

    """



    def __init__(self, teacher_model, student_model, num_classes=10, device='cpu', temperature=4.0):

        """

        参数:

            teacher_model: 教师模型

            student_model: 学生模型

            num_classes: 类别数

            device: 计算设备

            temperature: 温度参数

        """

        self.teacher_model = teacher_model

        self.student_model = student_model

        self.num_classes = num_classes

        self.device = device

        self.temperature = temperature



        # 构建类别关系图（可以是预定义的或从数据学习的）

        self.relation_graph = self._build_default_graph()



    def _build_default_graph(self):

        """

        构建默认的类别关系图



        使用相似度矩阵表示类别间的关系

        """

        # 简化：使用随机初始化的关系矩阵

        # 实际应从数据或预训练模型学习

        graph = torch.eye(self.num_classes)

        return graph.to(self.device)



    def compute_graph_knowledge_distillation_loss(self, student_logits, teacher_logits):

        """

        计算图知识蒸馏损失



        不仅传递单个类别的知识，还传递类别间关系的知识



        参数:

            student_logits: 学生模型输出

            teacher_logits: 教师模型输出

        """

        # 软标签损失

        student_soft = F.log_softmax(student_logits / self.temperature, dim=1)

        teacher_soft = F.softmax(teacher_logits / self.temperature, dim=1)

        soft_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean') * (self.temperature ** 2)



        # 图结构损失：学生和教师的类别关系应该一致

        # 计算类别相似度矩阵

        teacher_sim = F.cosine_similarity(teacher_logits.unsqueeze(1), teacher_logits.unsqueeze(0), dim=2)

        student_sim = F.cosine_similarity(student_logits.unsqueeze(1), student_logits.unsqueeze(0), dim=2)



        # 图结构损失

        graph_loss = F.mse_loss(student_sim, teacher_sim)



        return soft_loss, graph_loss



    def distill(self, images, labels, alpha=0.5):

        """

        执行知识图谱蒸馏



        参数:

            images: 输入图像

            labels: 真实标签

            alpha: 软损失权重



        返回:

            total_loss: 总损失

            soft_loss: 软标签损失

            graph_loss: 图结构损失

        """

        images = images.to(self.device)

        labels = labels.to(self.device)



        with torch.no_grad():

            teacher_logits = self.teacher_model(images)



        student_logits = self.student_model(images)



        # 计算损失

        soft_loss, graph_loss = self.compute_graph_knowledge_distillation_loss(student_logits, teacher_logits)

        hard_loss = F.cross_entropy(student_logits, labels)



        total_loss = alpha * soft_loss + (1 - alpha) * graph_loss + hard_loss



        return total_loss, soft_loss.item(), graph_loss.item(), hard_loss.item()





class GraphBasedKnowledgeTransfer:

    """

    基于图的知识迁移



    使用图卷积网络来传递结构化知识

    """



    def __init__(self, num_classes, embedding_dim=128, device='cpu'):

        self.num_classes = num_classes

        self.embedding_dim = embedding_dim

        self.device = device



        # 类别嵌入

        self.class_embeddings = nn.Parameter(torch.randn(num_classes, embedding_dim))

        self.adjacency_matrix = self._build_adjacency()



    def _build_adjacency(self):

        """构建类别邻接矩阵"""

        # 简化：全连接

        adj = torch.ones(self.num_classes, self.num_classes)

        return adj.to(self.device)



    def graph_convolution(self, features, adj):

        """

        简化的图卷积



        参数:

            features: 节点特征

            adj: 邻接矩阵

        """

        # 归一化邻接矩阵

        degree = adj.sum(dim=1, keepdim=True)

        adj_norm = adj / (degree + 1e-8)



        # 消息传递

        return torch.matmul(adj_norm, features)



    def propagate_knowledge(self, logits):

        """

        传播知识到邻居节点

        """

        embeddings = F.linear(logits, self.class_embeddings)



        # 图卷积

        propagated = self.graph_convolution(embeddings, self.adjacency_matrix)



        return propagated



    def compute_distillation_loss(self, student_logits, teacher_logits):

        """计算蒸馏损失"""

        # 原始logits损失

        teacher_soft = F.softmax(teacher_logits / 4.0, dim=1)

        student_soft = F.log_softmax(student_logits / 4.0, dim=1)

        soft_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean') * 16



        # 传播后的知识损失

        teacher_propagated = self.propagate_knowledge(teacher_logits)

        student_propagated = self.propagate_knowledge(student_logits)



        prop_loss = F.mse_loss(student_propagated, teacher_propagated)



        return soft_loss + prop_loss





class SemanticRelationDistillation:

    """

    语义关系蒸馏



    关注类别之间的语义关系

    """



    def __init__(self, teacher_model, student_model, num_classes=10, device='cpu'):

        self.teacher_model = teacher_model

        self.student_model = student_model

        self.num_classes = num_classes

        self.device = device



    def compute_semantic_relation(self, logits):

        """

        计算语义关系矩阵



        使用余弦相似度

        """

        # 归一化

        normed = F.normalize(logits, dim=1)

        # 相似度矩阵

        sim = torch.mm(normed, normed.t())

        return sim



    def compute_relation_distillation_loss(self, images, labels, margin=1.0):

        """

        关系蒸馏损失



        参数:

            margin: 边界参数

        """

        with torch.no_grad():

            teacher_logits = self.teacher_model(images)



        student_logits = self.student_model(images)



        # 计算关系矩阵

        teacher_rel = self.compute_semantic_relation(teacher_logits)

        student_rel = self.compute_semantic_relation(student_logits)



        # 关系蒸馏损失

        relation_loss = F.mse_loss(student_rel, teacher_rel)



        # 硬标签损失

        hard_loss = F.cross_entropy(student_logits, labels)



        return relation_loss + hard_loss





class IntermediateFeatureDistillation:

    """

    中间特征蒸馏



    结合中间层表示和输出层logits

    """



    def __init__(self, teacher_model, student_model, device='cpu'):

        self.teacher_model = teacher_model

        self.student_model = student_model

        self.device = device

        self.teacher_features = []

        self.student_features = []



        self._register_hooks()



    def _register_hooks(self):

        """注册hook获取中间特征"""

        def teacher_hook(module, input, output):

            self.teacher_features.append(output.detach())



        def student_hook(module, input, output):

            self.student_features.append(output.detach())



        # 假设两个模型有相似的结构

        for t_name, t_module in self.teacher_model.named_modules():

            if 'fc' in t_name or 'conv' in t_name:

                t_module.register_forward_hook(teacher_hook)



        for s_name, s_module in self.student_model.named_modules():

            if 'fc' in s_name or 'conv' in s_name:

                s_module.register_forward_hook(student_hook)



    def compute_feature_distillation_loss(self, alpha=0.5):

        """

        计算特征蒸馏损失



        参数:

            alpha: 加权因子

        """

        loss = 0.0



        for t_feat, s_feat in zip(self.teacher_features, self.student_features):

            # 匹配维度

            if t_feat.shape != s_feat.shape:

                # 使用自适应池化

                t_feat = F.adaptive_avg_pool2d(t_feat, s_feat.shape[2:]) if t_feat.dim() == 4 else t_feat

                if t_feat.shape != s_feat.shape:

                    t_feat = t_feat.reshape(s_feat.shape[0], -1)



            # MSE损失

            loss += F.mse_loss(s_feat, t_feat)



        self.teacher_features = []

        self.student_features = []



        return loss / len(self.teacher_features) if self.teacher_features else torch.tensor(0.0)





class MultiScaleDistillation:

    """

    多尺度蒸馏



    在不同粒度上进行蒸馏

    """



    def __init__(self, teacher_model, student_model, device='cpu'):

        self.teacher_model = teacher_model

        self.student_model = student_model

        self.device = device



    def distill_multiscale(self, images, labels):

        """

        多尺度蒸馏

        """

        with torch.no_grad():

            teacher_outputs = self.teacher_model(images)



        student_outputs = self.student_model(images)



        # 1. Logits蒸馏

        soft_loss = F.cross_entropy(student_outputs, labels)



        # 2. 关系蒸馏

        teacher_soft = F.softmax(teacher_outputs / 4.0, dim=1)

        student_soft = F.log_softmax(student_outputs / 4.0, dim=1)

        kl_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean') * 16



        # 3. 边界蒸馏（关注预测边界）

        teacher_conf, teacher_pred = torch.max(F.softmax(teacher_outputs, dim=1), dim=1)

        student_conf, student_pred = torch.max(F.softmax(student_outputs, dim=1), dim=1)



        # 关注边界样本

        boundary_mask = (teacher_conf < 0.9) | (student_pred != teacher_pred)

        if boundary_mask.any():

            boundary_loss = F.cross_entropy(student_outputs[boundary_mask], labels[boundary_mask])

        else:

            boundary_loss = torch.tensor(0.0)



        return soft_loss + kl_loss + 0.1 * boundary_loss





if __name__ == "__main__":

    import torch.nn as nn



    # 定义教师和学生模型

    class TeacherCNN(nn.Module):

        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 64, 3, padding=1)

            self.conv2 = nn.Conv2d(64, 128, 3, padding=1)

            self.fc1 = nn.Linear(128 * 7 * 7, 256)

            self.fc2 = nn.Linear(256, num_classes)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    class StudentCNN(nn.Module):

        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 16, 3, padding=1)

            self.conv2 = nn.Conv2d(16, 32, 3, padding=1)

            self.fc1 = nn.Linear(32 * 7 * 7, 64)

            self.fc2 = nn.Linear(64, num_classes)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    device = torch.device("cpu")



    teacher = TeacherCNN(num_classes=10).to(device)

    student = StudentCNN(num_classes=10).to(device)



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

    print("知识图谱蒸馏测试")

    print("=" * 50)



    optimizer = torch.optim.Adam(student.parameters(), lr=0.001)



    # 知识图谱蒸馏

    print("\n--- 知识图谱蒸馏 ---")

    distiller = KnowledgeGraphDistiller(teacher, student, num_classes=10, device=device)



    for epoch in range(3):

        total_loss = 0

        for images, labels in DummyDataset(5):

            loss, soft, graph, hard = distiller.distill(images, labels, alpha=0.5)

            optimizer.zero_grad()

            loss.backward()

            optimizer.step()

            total_loss += loss.item()



        print(f"Epoch {epoch + 1}: Loss={total_loss / 80:.4f}")



    # 语义关系蒸馏

    print("\n--- 语义关系蒸馏 ---")

    student2 = StudentCNN(num_classes=10).to(device)

    optimizer2 = torch.optim.Adam(student2.parameters(), lr=0.001)

    rel_distiller = SemanticRelationDistillation(teacher, student2, num_classes=10, device=device)



    for epoch in range(3):

        for images, labels in DummyDataset(5):

            images, labels = images.to(device), labels.to(device)

            loss = rel_distiller.compute_relation_distillation_loss(images, labels)



            optimizer2.zero_grad()

            loss.backward()

            optimizer2.step()



        print(f"Epoch {epoch + 1}: Loss={loss.item():.4f}")



    # 多尺度蒸馏

    print("\n--- 多尺度蒸馏 ---")

    student3 = StudentCNN(num_classes=10).to(device)

    optimizer3 = torch.optim.Adam(student3.parameters(), lr=0.001)

    ms_distiller = MultiScaleDistillation(teacher, student3, device=device)



    for epoch in range(3):

        for images, labels in DummyDataset(5):

            images, labels = images.to(device), labels.to(device)

            loss = ms_distiller.distill_multiscale(images, labels)



            optimizer3.zero_grad()

            loss.backward()

            optimizer3.step()



        print(f"Epoch {epoch + 1}: Loss={loss.item():.4f}")



    print("\n测试完成！")

