#
# 功能: 定义PR曲线计算函数。
#
from typing import List, Tuple
import numpy as np
import logging
from src.models.evaluation import PRCurveData

logger = logging.getLogger(__name__)


class PRCurveCalculator:
    """PR曲线计算器

    计算精确率-召回率曲线，用于评估特征匹配的质量
    """

    def __init__(self, num_thresholds: int = 100):
        """
        初始化PR曲线计算器

        Args:
            num_thresholds: 阈值数量
        """
        self.num_thresholds = num_thresholds

    def calculate(
        self, algorithm_name: str, scores: List[float], labels: List[bool]
    ) -> PRCurveData:
        """
        计算PR曲线数据

        Args:
            algorithm_name: 算法名称
            scores: 匹配分数列表（越高越好）
            labels: 真值标签列表（True表示正确匹配，False表示错误匹配）

        Returns:
            PR曲线数据
        """
        try:
            if len(scores) != len(labels):
                raise ValueError("分数和标签的长度必须相同")

            if len(scores) == 0:
                logger.warning("输入数据为空，返回默认PR曲线")
                return self._create_empty_pr_curve(algorithm_name)

            # 转换为numpy数组（使用新变量，避免改变参数类型）
            scores_arr = np.asarray(scores)
            labels_arr = np.asarray(labels, dtype=bool)

            # 计算阈值范围
            min_score = float(np.min(scores_arr))
            max_score = float(np.max(scores_arr))
            thresholds = np.linspace(min_score, max_score, self.num_thresholds)

            # 计算每个阈值下的精确率和召回率
            precisions_list: List[float] = []
            recalls_list: List[float] = []
            f1_scores_list: List[float] = []

            for threshold in thresholds:
                precision, recall, f1 = self._compute_precision_recall_f1(
                    scores_arr, labels_arr, float(threshold)
                )
                precisions_list.append(float(precision))
                recalls_list.append(float(recall))
                f1_scores_list.append(float(f1))

            precisions = np.asarray(precisions_list)
            recalls = np.asarray(recalls_list)
            f1_scores = np.asarray(f1_scores_list)

            # 计算AUC分数
            auc_score = float(self._compute_auc(recalls, precisions))

            # 找到最优阈值（最大F1分数）
            max_f1_idx = int(np.argmax(f1_scores))
            optimal_threshold = float(thresholds[max_f1_idx])
            optimal_precision = float(precisions[max_f1_idx])
            optimal_recall = float(recalls[max_f1_idx])
            max_f1_score = float(f1_scores[max_f1_idx])

            return PRCurveData(
                algorithm=algorithm_name,
                precisions=precisions.tolist(),
                recalls=recalls.tolist(),
                thresholds=thresholds.tolist(),
                auc_score=auc_score,
                optimal_threshold=optimal_threshold,
                optimal_precision=optimal_precision,
                optimal_recall=optimal_recall,
                f1_scores=f1_scores.tolist(),
                max_f1_score=max_f1_score,
            )

        except Exception as e:
            logger.error(f"计算PR曲线失败: {e}")
            return self._create_empty_pr_curve(algorithm_name)

    def _compute_precision_recall_f1(
        self, scores: np.ndarray, labels: np.ndarray, threshold: float
    ) -> Tuple[float, float, float]:
        """
        计算给定阈值下的精确率、召回率和F1分数

        Args:
            scores: 匹配分数
            labels: 真值标签
            threshold: 分类阈值

        Returns:
            (precision, recall, f1_score)
        """
        # 根据阈值进行预测
        predictions = scores >= threshold

        # 计算混淆矩阵（确保为 float）
        true_positives = float(np.sum(predictions & labels))
        false_positives = float(np.sum(predictions & ~labels))
        false_negatives = float(np.sum(~predictions & labels))

        # 计算精确率
        precision = 0.0 if (true_positives + false_positives) == 0 else (
            true_positives / (true_positives + false_positives)
        )

        # 计算召回率
        recall = 0.0 if (true_positives + false_negatives) == 0 else (
            true_positives / (true_positives + false_negatives)
        )

        # 计算F1分数
        f1_score = 0.0 if (precision + recall) == 0 else (
            2 * (precision * recall) / (precision + recall)
        )

        return float(precision), float(recall), float(f1_score)

    def _compute_auc(self, recalls: np.ndarray, precisions: np.ndarray) -> float:
        """
        使用梯形法则计算AUC (Area Under Curve)

        Args:
            recalls: 召回率数组
            precisions: 精确率数组

        Returns:
            AUC分数
        """
        try:
            # 按召回率排序
            sorted_indices = np.argsort(recalls)
            sorted_recalls = recalls[sorted_indices]
            sorted_precisions = precisions[sorted_indices]

            # 使用梯形法则计算面积
            auc = float(np.trapz(sorted_precisions, sorted_recalls))

            # 确保AUC在[0, 1]范围内
            return float(max(0.0, min(1.0, auc)))

        except Exception as e:
            logger.error(f"计算AUC失败: {e}")
            return 0.0

    def _create_empty_pr_curve(self, algorithm_name: str) -> PRCurveData:
        """创建空的PR曲线数据"""
        return PRCurveData(
            algorithm=algorithm_name,
            precisions=[0.0],
            recalls=[0.0],
            thresholds=[0.0],
            auc_score=0.0,
            optimal_threshold=0.0,
            optimal_precision=0.0,
            optimal_recall=0.0,
            f1_scores=[0.0],
            max_f1_score=0.0,
        )

    def calculate_from_matches(
        self,
        algorithm_name: str,
        matches: List[Tuple[int, int]],
        match_scores: List[float],
        ground_truth_matches: List[Tuple[int, int]],
        distance_threshold: float = 2.0,
    ) -> PRCurveData:
        """
        从特征匹配结果计算PR曲线

        Args:
            algorithm_name: 算法名称
            matches: 匹配对列表 [(query_idx, train_idx), ...]
            match_scores: 匹配分数列表
            ground_truth_matches: 地面真值匹配对
            distance_threshold: 判断匹配正确性的距离阈值

        Returns:
            PR曲线数据
        """
        try:
            if len(matches) != len(match_scores):
                raise ValueError("匹配对和分数的数量必须相同")

            # 将地面真值匹配转换为集合以便快速查找
            gt_match_set = set(ground_truth_matches)

            # 为每个匹配分配标签
            labels = []
            for match in matches:
                # 检查是否为正确匹配
                is_correct = match in gt_match_set
                labels.append(is_correct)

            return self.calculate(algorithm_name, match_scores, labels)

        except Exception as e:
            logger.error(f"从匹配结果计算PR曲线失败: {e}")
            return self._create_empty_pr_curve(algorithm_name)

    def compare_algorithms(self, pr_curves: List[PRCurveData]) -> dict:
        """
        比较多个算法的PR曲线性能

        Args:
            pr_curves: PR曲线数据列表

        Returns:
            比较结果字典
        """
        if not pr_curves:
            return {}

        algorithms: List[str] = [curve.algorithm for curve in pr_curves]
        auc_scores: List[float] = [float(curve.auc_score) for curve in pr_curves]
        max_f1_scores: List[float] = [float(curve.max_f1_score) for curve in pr_curves]
        optimal_thresholds: List[float] = [float(curve.optimal_threshold) for curve in pr_curves]

        comparison = {
            "algorithms": algorithms,
            "auc_scores": auc_scores,
            "max_f1_scores": max_f1_scores,
            "optimal_thresholds": optimal_thresholds,
        }

        # 找到最佳算法（避免依赖numpy类型）
        best_auc_idx = max(range(len(auc_scores)), key=lambda i: auc_scores[i])
        best_f1_idx = max(range(len(max_f1_scores)), key=lambda i: max_f1_scores[i])

        comparison["best_auc_algorithm"] = algorithms[best_auc_idx]
        comparison["best_f1_algorithm"] = algorithms[best_f1_idx]

        return comparison
