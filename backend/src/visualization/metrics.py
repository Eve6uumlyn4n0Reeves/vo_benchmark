#
# 功能: 指标可视化
#
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import List, Optional, Dict, Any, Tuple
import logging
from pathlib import Path
from src.models.evaluation import AlgorithmMetrics

logger = logging.getLogger(__name__)


class MetricsVisualizer:
    """指标可视化器"""

    def __init__(self, figure_size: Tuple[int, int] = (12, 8), dpi: int = 100):
        """
        初始化指标可视化器

        Args:
            figure_size: 图像尺寸 (width, height)
            dpi: 图像分辨率
        """
        self.figure_size = figure_size
        self.dpi = dpi

    def plot_algorithm_performance_radar(
        self,
        metrics: AlgorithmMetrics,
        title: Optional[str] = None,
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制算法性能雷达图

        Args:
            metrics: 算法指标
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            # 定义雷达图的指标和值
            categories = ["成功率", "处理速度", "匹配质量", "RANSAC效率", "轨迹精度"]

            # 归一化指标值到0-1范围
            values = [
                metrics.success_rate,  # 成功率
                min(metrics.fps / 30.0, 1.0),  # 处理速度（假设30fps为满分）
                metrics.matching.avg_inlier_ratio,  # 匹配质量
                metrics.ransac.convergence_rate,  # RANSAC效率
                (
                    1.0 - min(metrics.trajectory.ate_rmse / 10.0, 1.0)
                    if metrics.trajectory
                    else 0.5
                ),  # 轨迹精度（假设10m为最差）
            ]

            # 创建雷达图
            fig, ax = plt.subplots(
                figsize=self.figure_size,
                dpi=self.dpi,
                subplot_kw=dict(projection="polar"),
            )

            # 计算角度
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]  # 闭合图形
            angles += angles[:1]

            # 绘制雷达图
            ax.plot(angles, values, "o-", linewidth=2, label=metrics.algorithm_key)
            ax.fill(angles, values, alpha=0.25)

            # 设置标签
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 1)
            ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
            ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])
            ax.grid(True)

            plt.title(title or f"{metrics.algorithm_key} 性能雷达图", size=16, pad=20)
            plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"性能雷达图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制性能雷达图失败: {e}")
            raise

    def plot_metrics_comparison_bar(
        self,
        metrics_list: List[AlgorithmMetrics],
        metric_name: str,
        title: Optional[str] = None,
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制指标比较柱状图

        Args:
            metrics_list: 算法指标列表
            metric_name: 要比较的指标名称
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

            # 提取算法名称和指标值
            algorithm_names = [m.algorithm_key for m in metrics_list]
            values = []

            for metrics in metrics_list:
                if metric_name == "success_rate":
                    values.append(metrics.success_rate)
                elif metric_name == "fps":
                    values.append(metrics.fps)
                elif metric_name == "avg_matches":
                    values.append(metrics.matching.avg_matches)
                elif metric_name == "avg_inlier_ratio":
                    values.append(metrics.matching.avg_inlier_ratio)
                elif metric_name == "ate_rmse" and metrics.trajectory:
                    values.append(metrics.trajectory.ate_rmse)
                elif metric_name == "ransac_iterations":
                    values.append(metrics.ransac.avg_iterations)
                else:
                    values.append(0.0)

            # 创建柱状图
            bars = ax.bar(range(len(algorithm_names)), values, alpha=0.7)

            # 设置颜色（根据值的大小）
            colors = plt.cm.viridis(np.linspace(0, 1, len(values)))
            for bar, color in zip(bars, colors):
                bar.set_color(color)

            # 添加数值标签
            for i, (bar, value) in enumerate(zip(bars, values)):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.3f}",
                    ha="center",
                    va="bottom",
                )

            ax.set_xlabel("算法")
            ax.set_ylabel(metric_name)
            ax.set_title(title or f"{metric_name} 比较")
            ax.set_xticks(range(len(algorithm_names)))
            ax.set_xticklabels(algorithm_names, rotation=45, ha="right")
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"指标比较柱状图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制指标比较柱状图失败: {e}")
            raise

    def plot_performance_heatmap(
        self,
        metrics_list: List[AlgorithmMetrics],
        title: str = "算法性能热力图",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制算法性能热力图

        Args:
            metrics_list: 算法指标列表
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            # 准备数据
            algorithm_names = [m.algorithm_key for m in metrics_list]
            metric_names = [
                "成功率",
                "处理速度(fps)",
                "平均匹配数",
                "内点比例",
                "RANSAC迭代数",
            ]

            # 构建数据矩阵
            data_matrix = []
            for metrics in metrics_list:
                row = [
                    metrics.success_rate,
                    metrics.fps,
                    metrics.matching.avg_matches,
                    metrics.matching.avg_inlier_ratio,
                    metrics.ransac.avg_iterations,
                ]
                data_matrix.append(row)

            data_matrix = np.array(data_matrix)

            # 对每列进行归一化（0-1范围）
            for j in range(data_matrix.shape[1]):
                col = data_matrix[:, j]
                if np.max(col) > np.min(col):
                    data_matrix[:, j] = (col - np.min(col)) / (
                        np.max(col) - np.min(col)
                    )

            # 创建热力图
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

            im = ax.imshow(data_matrix, cmap="YlOrRd", aspect="auto")

            # 设置标签
            ax.set_xticks(range(len(metric_names)))
            ax.set_xticklabels(metric_names, rotation=45, ha="right")
            ax.set_yticks(range(len(algorithm_names)))
            ax.set_yticklabels(algorithm_names)

            # 添加数值标签
            for i in range(len(algorithm_names)):
                for j in range(len(metric_names)):
                    text = ax.text(
                        j,
                        i,
                        f"{data_matrix[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color="black",
                    )

            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label("归一化值", rotation=270, labelpad=20)

            ax.set_title(title)
            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"性能热力图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制性能热力图失败: {e}")
            raise

    def plot_processing_time_analysis(
        self,
        metrics_list: List[AlgorithmMetrics],
        title: str = "处理时间分析",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制处理时间分析图

        Args:
            metrics_list: 算法指标列表
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
                2, 2, figsize=self.figure_size, dpi=self.dpi
            )

            algorithm_names = [m.algorithm_key for m in metrics_list]
            frame_times = [m.avg_frame_time_ms for m in metrics_list]
            fps_values = [m.fps for m in metrics_list]
            total_times = [m.total_time_s for m in metrics_list]

            # 1. 平均帧处理时间
            bars1 = ax1.bar(
                range(len(algorithm_names)), frame_times, alpha=0.7, color="skyblue"
            )
            ax1.set_xlabel("算法")
            ax1.set_ylabel("平均帧处理时间 (ms)")
            ax1.set_title("平均帧处理时间")
            ax1.set_xticks(range(len(algorithm_names)))
            ax1.set_xticklabels(algorithm_names, rotation=45, ha="right")
            ax1.grid(True, alpha=0.3)

            # 添加数值标签
            for bar, value in zip(bars1, frame_times):
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.1f}",
                    ha="center",
                    va="bottom",
                )

            # 2. FPS
            bars2 = ax2.bar(
                range(len(algorithm_names)), fps_values, alpha=0.7, color="lightgreen"
            )
            ax2.set_xlabel("算法")
            ax2.set_ylabel("FPS")
            ax2.set_title("处理帧率")
            ax2.set_xticks(range(len(algorithm_names)))
            ax2.set_xticklabels(algorithm_names, rotation=45, ha="right")
            ax2.grid(True, alpha=0.3)

            # 添加数值标签
            for bar, value in zip(bars2, fps_values):
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.1f}",
                    ha="center",
                    va="bottom",
                )

            # 3. 总处理时间
            bars3 = ax3.bar(
                range(len(algorithm_names)), total_times, alpha=0.7, color="orange"
            )
            ax3.set_xlabel("算法")
            ax3.set_ylabel("总处理时间 (s)")
            ax3.set_title("总处理时间")
            ax3.set_xticks(range(len(algorithm_names)))
            ax3.set_xticklabels(algorithm_names, rotation=45, ha="right")
            ax3.grid(True, alpha=0.3)

            # 添加数值标签
            for bar, value in zip(bars3, total_times):
                height = bar.get_height()
                ax3.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.1f}",
                    ha="center",
                    va="bottom",
                )

            # 4. 时间效率散点图（FPS vs 平均帧时间）
            ax4.scatter(frame_times, fps_values, alpha=0.7, s=100)
            for i, name in enumerate(algorithm_names):
                ax4.annotate(
                    name,
                    (frame_times[i], fps_values[i]),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=8,
                )
            ax4.set_xlabel("平均帧处理时间 (ms)")
            ax4.set_ylabel("FPS")
            ax4.set_title("时间效率关系")
            ax4.grid(True, alpha=0.3)

            plt.suptitle(title, fontsize=16)
            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"处理时间分析图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制处理时间分析图失败: {e}")
            raise
