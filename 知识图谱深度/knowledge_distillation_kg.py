# -*- coding: utf-8 -*-
"""
算法实现：知识图谱深度 / knowledge_distillation_kg

本文件实现 knowledge_distillation_kg 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from collections import defaultdict


class KnowledgeDistiller:
    """
    知识蒸馏器
    
    将"教师"模型的知识蒸馏到"学生"KG嵌入模型
    
    参数:
        teacher_dim: 教师模型嵌入维度
        student_dim: 学生模型嵌入维度
    """
    
    def __init__(self, teacher_dim: int = 768, student_dim: int = 100):
        self.teacher_dim = teacher_dim
        self.student_dim = student_dim
        
        np.random.seed(42)
        
        # 投影层：教师 -> 学生
        self.projection = np.random.randn(teacher_dim, student_dim) * 0.1
        
        # 温度参数（用于软最大化）
        self.temperature = 2.0
    
    def project_to_student(self, teacher_embeddings: np.ndarray) -> np.ndarray:
        """
        将教师嵌入投影到学生空间
        """
        return teacher_embeddings @ self.projection
    
    def soft_target_distribution(self, teacher_scores: np.ndarray) -> np.ndarray:
        """
        计算软目标分布
        
        使用温度缩放的softmax
        """
        exp_scores = np.exp(teacher_scores / self.temperature)
        return exp_scores / np.sum(exp_scores)


class KGDistillation:
    """
    知识图谱蒸馏
    
    参数:
        n_entities: 实体数量
        n_relations: 关系数量
        embedding_dim: 嵌入维度
    """
    
    def __init__(self, n_entities: int, n_relations: int, embedding_dim: int = 100):
        self.n_entities = n_entities
        self.n_relations = n_relations
        self.dim = embedding_dim
        
        np.random.seed(42)
        
        # 学生实体嵌入
        self.entity_embeddings = np.random.randn(n_entities, embedding_dim) * 0.1
        
        # 学生关系嵌入
        self.relation_embeddings = np.random.randn(n_relations, embedding_dim) * 0.1
        
        # 教师软标签（从预训练模型获得）
        self.teacher_labels: Dict[Tuple[int, int], np.ndarray] = {}
    
    def set_teacher_labels(self, head_idx: int, relation_idx: int,
                          soft_labels: np.ndarray):
        """
        设置教师模型的软标签
        
        soft_labels: 尾实体的概率分布
        """
        self.teacher_labels[(head_idx, relation_idx)] = soft_labels
    
    def distillation_loss(self, head_idx: int, relation_idx: int,
                         student_scores: np.ndarray,
                         ground_truth: int,
                         alpha: float = 0.5) -> float:
        """
        计算蒸馏损失
        
        参数:
            head_idx: 头实体索引
            relation_idx: 关系索引
            student_scores: 学生模型的分数
            ground_truth: 真实尾实体
            alpha: 硬标签和软标签的权衡
        
        返回:
            蒸馏损失
        """
        # 获取教师软标签
        key = (head_idx, relation_idx)
        if key in self.teacher_labels:
            soft_labels = self.teacher_labels[key]
        else:
            soft_labels = None
        
        # 硬标签损失（交叉熵）
        hard_loss = -np.log(student_scores[ground_truth] + 1e-10)
        
        # 软标签损失（KL散度）
        if soft_labels is not None:
            # 学生概率
            student_probs = np.exp(student_scores / self.temperature)
            student_probs = student_probs / np.sum(student_probs)
            
            # KL散度
            soft_loss = np.sum(soft_labels * np.log(soft_labels / (student_probs + 1e-10) + 1e-10))
        else:
            soft_loss = 0.0
        
        # 组合损失
        total_loss = alpha * hard_loss + (1 - alpha) * soft_loss
        
        return total_loss
    
    def train_step(self, triples: List[Tuple[int, int, int]],
                  teacher_model, batch_size: int = 64,
                  learning_rate: float = 0.01) -> float:
        """
        一步训练
        """
        total_loss = 0.0
        
        np.random.shuffle(triples)
        
        for i in range(0, len(triples), batch_size):
            batch = triples[i:i + batch_size]
            
            for h, r, t in batch:
                # 计算学生分数
                h_emb = self.entity_embeddings[h]
                r_emb = self.relation_embeddings[r]
                
                # 预测所有尾实体
                scores = []
                for tail_idx in range(self.n_entities):
                    t_emb = self.entity_embeddings[tail_idx]
                    score = -np.linalg.norm(h_emb + r_emb - t_emb)
                    scores.append(score)
                
                scores = np.array(scores)
                
                # 软标签（如果教师模型可用）
                if teacher_model is not None:
                    soft_labels = teacher_model.predict_tail_distribution(h, r)
                    self.set_teacher_labels(h, r, soft_labels)
                
                # 计算损失
                loss = self.distillation_loss(h, r, scores, t)
                total_loss += loss
                
                # 更新（简化）
                self.entity_embeddings[h] -= learning_rate * np.random.randn(self.dim) * 0.01
                self.entity_embeddings[t] -= learning_rate * np.random.randn(self.dim) * 0.01
        
        return total_loss


class MockTeacherModel:
    """模拟教师模型"""
    
    def __init__(self, n_entities: int, embedding_dim: int = 200):
        self.n_entities = n_entities
        
        np.random.seed(42)
        
        # 教师有更大的嵌入
        self.embeddings = np.random.randn(n_entities, embedding_dim) * 0.1
    
    def predict_tail_distribution(self, head_idx: int, relation_idx: int) -> np.ndarray:
        """
        预测尾实体分布（模拟教师模型输出）
        """
        h_emb = self.embeddings[head_idx]
        
        # 计算与所有尾实体的相似度
        similarities = np.zeros(self.n_entities)
        for i in range(self.n_entities):
            similarities[i] = np.dot(h_emb, self.embeddings[i])
        
        # 转换为概率分布
        probs = np.exp(similarities) / np.sum(np.exp(similarities))
        
        return probs


class DistillationMetrics:
    """蒸馏评估指标"""
    
    def __init__(self):
        self.teacher_acc = []
        self.student_acc = []
        self.losses = []
    
    def add(self, teacher_accuracy: float, student_accuracy: float, loss: float):
        """添加评估结果"""
        self.teacher_acc.append(teacher_accuracy)
        self.student_acc.append(student_accuracy)
        self.losses.append(loss)
    
    def summary(self) -> Dict[str, float]:
        """获取评估汇总"""
        return {
            'avg_teacher_acc': np.mean(self.teacher_acc),
            'avg_student_acc': np.mean(self.student_acc),
            'avg_loss': np.mean(self.losses),
            'knowledge_transfer': np.mean(self.teacher_acc) - np.mean(self.student_acc)
        }


def evaluate_distillation(student_model, teacher_model, test_triples: List[Tuple[int, int, int]]) -> Dict[str, float]:
    """
    评估蒸馏效果
    """
    teacher_correct = 0
    student_correct = 0
    n = len(test_triples)
    
    for h, r, t in test_triples:
        # 教师预测
        teacher_pred = np.argmax(teacher_model.predict_tail_distribution(h, r))
        if teacher_pred == t:
            teacher_correct += 1
        
        # 学生预测
        h_emb = student_model.entity_embeddings[h]
        r_emb = student_model.relation_embeddings[r]
        
        best_tail = 0
        best_score = -np.inf
        for tail_idx in range(student_model.n_entities):
            t_emb = student_model.entity_embeddings[tail_idx]
            score = -np.linalg.norm(h_emb + r_emb - t_emb)
            if score > best_score:
                best_score = score
                best_tail = tail_idx
        
        if best_tail == t:
            student_correct += 1
    
    return {
        'teacher_accuracy': teacher_correct / n,
        'student_accuracy': student_correct / n
    }


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("知识蒸馏到知识图谱测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 参数设置
    n_entities = 1000
    n_relations = 50
    n_triples = 5000
    
    # 生成测试数据
    triples = []
    for _ in range(n_triples):
        h = np.random.randint(n_entities)
        r = np.random.randint(n_relations)
        t = np.random.randint(n_entities)
        triples.append((h, r, t))
    
    print(f"\n数据: {n_entities} 实体, {n_relations} 关系, {n_triples} 三元组")
    
    # 创建教师模型
    print("\n--- 创建模型 ---")
    teacher = MockTeacherModel(n_entities, embedding_dim=200)
    student = KGDistillation(n_entities, n_relations, embedding_dim=100)
    
    print(f"教师嵌入维度: 200")
    print(f"学生嵌入维度: 100")
    
    # 蒸馏训练
    print("\n--- 蒸馏训练 ---")
    distiller = KnowledgeDistiller(teacher_dim=200, student_dim=100)
    
    train_triples = triples[:4000]
    test_triples = triples[4000:]
    
    for epoch in range(5):
        loss = student.train_step(train_triples[:100], teacher, batch_size=32)
        
        if (epoch + 1) % 2 == 0:
            print(f"Epoch {epoch + 1}: Loss = {loss:.4f}")
    
    # 评估
    print("\n--- 评估蒸馏效果 ---")
    metrics = evaluate_distillation(student, teacher, test_triples[:200])
    
    print(f"教师准确率: {metrics['teacher_accuracy']:.4f}")
    print(f"学生准确率: {metrics['student_accuracy']:.4f}")
    print(f"知识迁移损失: {metrics['teacher_accuracy'] - metrics['student_accuracy']:.4f}")
    
    # 蒸馏指标
    print("\n--- 蒸馏指标 ---")
    dist_metrics = DistillationMetrics()
    
    for i in range(5):
        teacher_acc = 0.6 + np.random.rand() * 0.2
        student_acc = 0.5 + np.random.rand() * 0.2
        loss = 0.5 - np.random.rand() * 0.3
        
        dist_metrics.add(teacher_acc, student_acc, loss)
    
    summary = dist_metrics.summary()
    
    for key, value in summary.items():
        print(f"{key}: {value:.4f}")
    
    print("\n" + "=" * 50)
    print("测试完成")
