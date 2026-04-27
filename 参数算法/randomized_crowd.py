# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / randomized_crowd

本文件实现 randomized_crowd 相关的算法功能。
"""

import random
from typing import List, Dict, Tuple


class Worker:
    """标注者模型"""

    def __init__(self, worker_id: int, reliability: float):
        """
        参数：
            worker_id: 标注者ID
            reliability: 可靠性（1=完全可靠，0=完全随机）
        """
        self.worker_id = worker_id
        self.reliability = reliability
        self.answers = {}

    def answer(self, question: str, true_answer: str = None) -> str:
        """
        回答问题

        如果有真实答案，按可靠性返回
        否则返回随机答案
        """
        if true_answer is None or self.reliability == 0.5:
            return random.choice(['yes', 'no'])

        if random.random() < self.reliability:
            return true_answer
        else:
            return 'no' if true_answer == 'yes' else 'yes'


class CrowdsourcingModel:
    """众包模型"""

    def __init__(self):
        self.workers = {}
        self.questions = {}
        self.answers = {}  # (worker_id, question) -> answer

    def add_worker(self, worker_id: int, reliability: float):
        """添加标注者"""
        self.workers[worker_id] = Worker(worker_id, reliability)

    def add_question(self, question_id: str):
        """添加问题"""
        self.questions[question_id] = {
            'answers': {},
            'true_label': None
        }

    def collect_answers(self, question_id: str, worker_ids: List[int]):
        """
        收集标注

        参数：
            question_id: 问题ID
            worker_ids: 回答该问题的标注者列表
        """
        true_label = self.questions[question_id]['true_label']

        for worker_id in worker_ids:
            worker = self.workers[worker_id]
            answer = worker.answer(question_id, true_label)
            self.answers[(worker_id, question_id)] = answer
            self.questions[question_id]['answers'][worker_id] = answer

    def majority_voting(self, question_id: str) -> str:
        """
        多数投票

        最简单的聚合方法
        """
        answers = self.questions[question_id]['answers']
        yes_count = sum(1 for a in answers.values() if a == 'yes')
        no_count = len(answers) - yes_count

        return 'yes' if yes_count > no_count else 'no'

    def expectation_maximization(self, question_id: str, max_iter: int = 10) -> Tuple[str, Dict]:
        """
        EM算法估计真实标签和标注者可靠性

        参数：
            question_id: 问题ID

        返回：(估计的真实标签, 各标注者的估计可靠性)
        """
        answers = self.questions[question_id]['answers']
        n_workers = len(answers)

        # 初始化
        worker_reliability = {wid: 0.7 for wid in answers.keys()}

        for iteration in range(max_iter):
            # E步：估计真实标签
            prob_yes = []
            for wid, ans in answers.items():
                r = worker_reliability[wid]
                if ans == 'yes':
                    prob_yes.append(r / (r + (1-r)))
                else:
                    prob_yes.append((1-r) / (2-r))

            # M步：更新可靠性
            new_reliability = {}
            for wid, ans in answers.items():
                if ans == 'yes':
                    new_reliability[wid] = prob_yes[wid] / len(answers)
                else:
                    new_reliability[wid] = 1 - prob_yes[wid]

            worker_reliability = new_reliability

        # 最终标签估计
        label = 'yes' if sum(prob_yes) / n_workers > 0.5 else 'no'

        return label, worker_reliability


def simulate_crowdsourcing(n_workers: int, n_questions: int, n_answers_per_question: int = 5):
    """
    众包模拟

    比较多数投票和EM算法的效果
    """
    print("=== 众包模拟 ===\n")

    model = CrowdsourcingModel()

    # 添加标注者（可靠性从0.6到0.95）
    for i in range(n_workers):
        reliability = random.uniform(0.6, 0.95)
        model.add_worker(i, reliability)

    # 添加问题
    for i in range(n_questions):
        model.add_question(f'q_{i}')
        model.questions[f'q_{i}']['true_label'] = random.choice(['yes', 'no'])

        # 随机选择标注者回答
        worker_ids = random.sample(range(n_workers), n_answers_per_question)
        model.collect_answers(f'q_{i}', worker_ids)

    # 比较方法
    mv_correct = 0
    em_correct = 0

    for qid in model.questions:
        true_label = model.questions[qid]['true_label']

        mv_label = model.majority_voting(qid)
        em_label, _ = model.expectation_maximization(qid)

        if mv_label == true_label:
            mv_correct += 1
        if em_label == true_label:
            em_correct += 1

    print(f"问题数: {n_questions}")
    print(f"标注者数: {n_workers}")
    print(f"每问题回答数: {n_answers_per_question}")
    print()
    print(f"多数投票准确率: {mv_correct/n_questions*100:.1f}%")
    print(f"EM算法准确率: {em_correct/n_questions*100:.1f}%")

    return mv_correct / n_questions, em_correct / n_questions


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    random.seed(42)

    simulate_crowdsourcing(n_workers=20, n_questions=100, n_answers_per_question=5)

    print("\n说明：")
    print("  - 多数投票：简单但易受不可靠标注者影响")
    print("  - EM算法：同时估计真实标签和标注者可靠性")
    print("  - 实际应用中还需要考虑成本和标注者多样性")
