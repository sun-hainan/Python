"""
时序知识图谱基准数据集评估 (Temporal KG Benchmark Evaluation)
==========================================================
实现时序知识图谱基准数据集的评估框架。

常用基准：
- ICEWS (Integrated Crisis Early Warning System)
- GDELT (Global Database of Events, Language, and Tone)
- Wikidata-History

评估指标：
- MRR (Mean Reciprocal Rank)
- Hits@K
- 时间预测准确率
- 因果关系准确率

参考：
    - WDC Wikidata-History Dataset.
    - ICEWS Event Data.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
import random


class TemporalKGDataset:
    """时序知识图谱数据集"""
    
    def __init__(self, name: str):
        self.name = name
        self.train = []
        self.valid = []
        self.test = []
        self.entities = set()
        self.predicates = set()
        self.time_range = (None, None)
        self.metadata = {}
    
    def load_from_dict(self, data: Dict[str, List[Tuple]]):
        """
        从字典加载数据
        
        参数:
            data: {"train": [...], "valid": [...], "test": [...]}
        """
        if "train" in data:
            self.train = data["train"]
        if "valid" in data:
            self.valid = data["valid"]
        if "test" in data:
            self.test = data["test"]
        
        # 统计
        for split in [self.train, self.valid, self.test]:
            for triple in split:
                if len(triple) >= 4:
                    s, p, o, t = triple[:4]
                    self.entities.add(s)
                    self.entities.add(o)
                    self.predicates.add(p)
                    
                    if self.time_range[0] is None or t < self.time_range[0]:
                        self.time_range = (t, self.time_range[1])
                    if self.time_range[1] is None or t > self.time_range[1]:
                        self.time_range = (self.time_range[0], t)
    
    def statistics(self) -> Dict[str, Any]:
        """返回数据集统计"""
        return {
            "name": self.name,
            "num_train": len(self.train),
            "num_valid": len(self.valid),
            "num_test": len(self.test),
            "num_entities": len(self.entities),
            "num_predicates": len(self.predicates),
            "time_range": self.time_range,
        }


class TemporalKGEvaluator:
    """
    时序知识图谱评估器
    
    参数:
        dataset: 数据集
    """
    
    def __init__(self, dataset: TemporalKGDataset):
        self.dataset = dataset
        self.results = {}
    
    def evaluate_tail_prediction(self, predict_func, split: str = "test") -> Dict[str, float]:
        """
        评估尾实体预测
        
        参数:
            predict_func: 预测函数 (s, p, t) -> [(o, score), ...]
            split: 评估的数据集划分
        
        返回:
            评估指标
        """
        if split == "test":
            data = self.dataset.test
        elif split == "valid":
            data = self.dataset.valid
        else:
            data = self.dataset.train
        
        ranks = []
        hits_at_k = {"1": 0, "3": 0, "10": 0, "50": 0}
        
        for triple in data:
            if len(triple) < 4:
                continue
            
            s, p, o, t = triple[:4]
            
            # 预测
            predictions = predict_func(s, p, t)
            
            # 找真实实体的排名
            rank = None
            for i, (pred_o, _) in enumerate(predictions):
                if pred_o == o:
                    rank = i + 1
                    break
            
            if rank is not None:
                ranks.append(rank)
                for k in hits_at_k.keys():
                    if rank <= int(k):
                        hits_at_k[k] += 1
            else:
                ranks.append(len(predictions) + 1)
        
        n = len(ranks)
        if n == 0:
            return {}
        
        # 计算指标
        mrr = sum(1.0 / r for r in ranks) / n
        mr = sum(ranks) / n
        
        for k in hits_at_k:
            hits_at_k[k] /= n
        
        self.results["tail_prediction"] = {
            "MRR": mrr,
            "MR": mr,
            "Hits@1": hits_at_k["1"],
            "Hits@3": hits_at_k["3"],
            "Hits@10": hits_at_k["10"],
            "Hits@50": hits_at_k["50"],
        }
        
        return self.results["tail_prediction"]
    
    def evaluate_time_prediction(self, predict_func, split: str = "test") -> Dict[str, float]:
        """
        评估时间预测
        
        参数:
            predict_func: 预测函数 (s, p, o) -> [t1, t2, ...] 或 {(t, score), ...}
            split: 数据集划分
        
        返回:
            评估指标
        """
        if split == "test":
            data = self.dataset.test
        else:
            data = self.dataset.valid if split == "valid" else self.dataset.train
        
        exact_matches = 0
        time_diffs = []
        
        for triple in data:
            if len(triple) < 4:
                continue
            
            s, p, o, t = triple[:4]
            
            # 预测时间
            predictions = predict_func(s, p, o)
            
            if isinstance(predictions, list):
                # 直接是时间列表
                if t in predictions:
                    exact_matches += 1
            else:
                # (time, score) 列表
                pred_times = [pred_t for pred_t, _ in predictions]
                if t in pred_times:
                    exact_matches += 1
            
            # 计算时间差
            if predictions:
                if isinstance(predictions[0], tuple):
                    best_time = predictions[0][0]
                else:
                    best_time = predictions[0]
                time_diffs.append(abs(best_time - t))
        
        n = len(data)
        if n == 0:
            return {}
        
        # 计算指标
        accuracy = exact_matches / n
        mae = sum(time_diffs) / n if time_diffs else 0
        
        self.results["time_prediction"] = {
            "Accuracy": accuracy,
            "MAE": mae,
        }
        
        return self.results["time_prediction"]
    
    def evaluate_temporal_consistency(self, predict_func, split: str = "test") -> Dict[str, float]:
        """
        评估时序一致性
        
        参数:
            predict_func: 预测函数
            split: 数据集划分
        
        返回:
            评估指标
        """
        if split == "test":
            data = self.dataset.test
        else:
            data = self.dataset.valid if split == "valid" else self.dataset.train
        
        consistent = 0
        inconsistent = 0
        
        for triple in data:
            if len(triple) < 4:
                continue
            
            s, p, o, t = triple[:4]
            
            # 检查时序一致性
            # 简化：检查预测的时间是否在合理范围内
            predictions = predict_func(s, p, t)
            
            # 这里简化处理
            if predictions:
                consistent += 1
            else:
                inconsistent += 1
        
        n = consistent + inconsistent
        if n == 0:
            return {}
        
        consistency_rate = consistent / n
        
        self.results["temporal_consistency"] = {
            "ConsistencyRate": consistency_rate,
        }
        
        return self.results["temporal_consistency"]


class TemporalKGBenchmark:
    """
    时序知识图谱基准测试
    
    支持创建合成基准数据集
    """
    
    def __init__(self, name: str):
        self.name = name
        self.dataset = None
    
    def create_synthetic_dataset(self, num_entities: int = 100,
                                num_predicates: int = 10,
                                num_triples: int = 1000,
                                num_times: int = 50,
                                seed: int = 42) -> TemporalKGDataset:
        """
        创建合成数据集
        
        参数:
            num_entities: 实体数
            num_predicates: 谓词数
            num_triples: 三元组数
            num_times: 时间点数
            seed: 随机种子
        
        返回:
            数据集
        """
        random.seed(seed)
        
        dataset = TemporalKGDataset(f"{self.name}_synthetic")
        
        # 生成实体和谓词
        entities = [f"e{i}" for i in range(num_entities)]
        predicates = [f"p{i}" for i in range(num_predicates)]
        times = list(range(num_times))
        
        # 生成三元组
        all_triples = []
        
        for _ in range(num_triples * 2):  # 生成多一些用于划分
            s = random.choice(entities)
            p = random.choice(predicates)
            o = random.choice(entities)
            t = random.choice(times)
            
            # 避免自环
            while o == s:
                o = random.choice(entities)
            
            all_triples.append((s, p, o, t))
        
        # 划分数据集
        random.shuffle(all_triples)
        
        n_train = int(len(all_triples) * 0.7)
        n_valid = int(len(all_triples) * 0.15)
        
        dataset.train = all_triples[:n_train]
        dataset.valid = all_triples[n_train:n_train+n_valid]
        dataset.test = all_triples[n_train+n_valid:]
        
        # 统计
        for triple in all_triples:
            s, p, o, t = triple
            dataset.entities.add(s)
            dataset.entities.add(o)
            dataset.predicates.add(p)
        
        dataset.time_range = (min(times), max(times))
        
        self.dataset = dataset
        return dataset
    
    def create_temporal_sampling_benchmark(self, base_dataset: TemporalKGDataset,
                                          sample_ratio: float = 0.1) -> TemporalKGDataset:
        """
        创建时序采样基准（强调时间维度）
        
        参数:
            base_dataset: 基础数据集
            sample_ratio: 采样比例
        
        返回:
            采样后的数据集
        """
        dataset = TemporalKGDataset(f"{self.name}_temporal_sampled")
        
        # 按时间分层采样
        # 按时间排序
        all_triples = base_dataset.train + base_dataset.valid + base_dataset.test
        all_triples.sort(key=lambda x: x[3])
        
        # 从每个时间窗口采样
        num_windows = 10
        triples_per_window = int(len(all_triples) * sample_ratio / num_windows)
        
        sampled = []
        window_size = len(all_triples) // num_windows
        
        for i in range(num_windows):
            start = i * window_size
            end = min((i + 1) * window_size, len(all_triples))
            window_triples = all_triples[start:end]
            
            if len(window_triples) > triples_per_window:
                sampled.extend(random.sample(window_triples, triples_per_window))
            else:
                sampled.extend(window_triples)
        
        # 划分
        random.shuffle(sampled)
        n = len(sampled)
        dataset.train = sampled[:int(n*0.7)]
        dataset.valid = sampled[int(n*0.7):int(n*0.85)]
        dataset.test = sampled[int(n*0.85):]
        
        dataset.entities = base_dataset.entities
        dataset.predicates = base_dataset.predicates
        dataset.time_range = base_dataset.time_range
        
        return dataset


def run_benchmark_evaluation(dataset: TemporalKGDataset,
                             model_name: str = "random") -> Dict[str, Any]:
    """
    运行基准评估
    
    参数:
        dataset: 数据集
        model_name: 模型名称
    
    返回:
        评估结果
    """
    evaluator = TemporalKGEvaluator(dataset)
    
    # 随机预测基线
    def random_predict(s, p, t):
        entities = list(dataset.entities)
        predictions = [(e, random.random()) for e in entities if e != s]
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:50]
    
    # 评估
    tail_results = evaluator.evaluate_tail_prediction(random_predict, "test")
    time_results = evaluator.evaluate_time_prediction(
        lambda s, p, o: [random.choice(range(*dataset.time_range))], "test"
    )
    
    return {
        "dataset": dataset.name,
        "model": model_name,
        "tail_prediction": tail_results,
        "time_prediction": time_results,
    }


if __name__ == "__main__":
    print("=== 时序知识图谱基准评估测试 ===")
    
    # 创建基准
    benchmark = TemporalKGBenchmark("TestBenchmark")
    
    # 创建合成数据集
    dataset = benchmark.create_synthetic_dataset(
        num_entities=50,
        num_predicates=5,
        num_triples=500,
        num_times=20,
        seed=42
    )
    
    stats = dataset.statistics()
    print("\n数据集统计:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # 创建时序采样基准
    print("\n创建时序采样基准...")
    sampled_dataset = benchmark.create_temporal_sampling_benchmark(dataset, sample_ratio=0.2)
    
    sampled_stats = sampled_dataset.statistics()
    print(f"采样后数据集: {sampled_stats['num_train']} 训练, "
          f"{sampled_stats['num_valid']} 验证, "
          f"{sampled_stats['num_test']} 测试")
    
    # 评估
    print("\n评估随机预测基线:")
    results = run_benchmark_evaluation(dataset, "random")
    
    print("\n尾实体预测结果:")
    for metric, value in results["tail_prediction"].items():
        print(f"  {metric}: {value:.4f}")
    
    print("\n时间预测结果:")
    for metric, value in results["time_prediction"].items():
        print(f"  {metric}: {value:.4f}")
    
    print("\n=== 测试完成 ===")
