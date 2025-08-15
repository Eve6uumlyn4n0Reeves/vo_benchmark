#
# 功能: 算法比较可视化
#
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import List, Optional, Dict, Any, Tuple
import logging
from pathlib import Path
from src.models.evaluation import AlgorithmMetrics

logger = logging.getLogger(__name__)


class ComparisonVisualizer:
    """算法比较可视化器"""

    def __init__(self, figure_size: Tuple[int, int] = (14, 10), dpi: int = 100):
        """
        初始化比较可视化器

        Args:
            figure_size: 图像尺寸 (width, height)
            dpi: 图像分辨率
        """
        self.figure_size = figure_size
        self.dpi = dpi

    def plot_algorithm_ranking(
        self,
        metrics_list: List[AlgorithmMetrics],
        ranking_metric: str = "success_rate",
        title: Optional[str] = None,
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制算法排名图

        Args:
            metrics_list: 算法指标列表
            ranking_metric: 排名依据的指标
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            # 提取排名指标值
            values = []
            for metrics in metrics_list:
                if ranking_metric == "success_rate":
                    values.append(metrics.success_rate)
                elif ranking_metric == "fps":
                    values.append(metrics.fps)
                elif ranking_metric == "avg_inlier_ratio":
                    values.append(metrics.matching.avg_inlier_ratio)
                elif ranking_metric == "ate_rmse" and metrics.trajectory:
                    values.append(metrics.trajectory.ate_rmse)
                else:
                    values.append(0.0)

            # 排序（对于误差指标，值越小越好）
            is_error_metric = ranking_metric in [
                "ate_rmse",
                "rpe_rmse",
                "avg_frame_time_ms",
            ]
            sorted_indices = np.argsort(values)
            if not is_error_metric:
                sorted_indices = sorted_indices[::-1]  # 降序排列

            sorted_metrics = [metrics_list[i] for i in sorted_indices]
            sorted_values = [values[i] for i in sorted_indices]

            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

            # 创建水平柱状图
            y_pos = np.arange(len(sorted_metrics))
            algorithm_names = [m.algorithm_key for m in sorted_metrics]

            # 设置颜色渐变
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(sorted_metrics)))
            if not is_error_metric:
                colors = colors[::-1]  # 对于非误差指标，最好的用绿色

            bars = ax.barh(y_pos, sorted_values, color=colors, alpha=0.8)

            # 添加排名标签
            for i, (bar, value) in enumerate(zip(bars, sorted_values)):
                width = bar.get_width()
                ax.text(
                    width + width * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"#{i+1}: {value:.3f}",
                    ha="left",
                    va="center",
                    fontweight="bold",
                )

            ax.set_yticks(y_pos)
            ax.set_yticklabels(algorithm_names)
            ax.set_xlabel(ranking_metric)
            ax.set_title(title or f"算法排名 (按{ranking_metric})")
            ax.grid(True, alpha=0.3, axis="x")

            # 添加最佳和最差标记
            if len(sorted_metrics) > 1:
                ax.text(
                    0.02,
                    0.98,
                    f"最佳: {algorithm_names[0]}",
                    transform=ax.transAxes,
                    va="top",
                    ha="left",
                    bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.8),
                )
                ax.text(
                    0.02,
                    0.02,
                    f"最差: {algorithm_names[-1]}",
                    transform=ax.transAxes,
                    va="bottom",
                    ha="left",
                    bbox=dict(boxstyle="round", facecolor="lightcoral", alpha=0.8),
                )

            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"算法排名图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制算法排名图失败: {e}")
            raise

    def plot_feature_type_comparison(
        self,
        metrics_list: List[AlgorithmMetrics],
        title: str = "特征类型比较",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制不同特征类型的比较图

        Args:
            metrics_list: 算法指标列表
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            # 按特征类型分组
            feature_groups = {}
            for metrics in metrics_list:
                feature_type = metrics.feature_type
                if feature_type not in feature_groups:
                    feature_groups[feature_type] = []
                feature_groups[feature_type].append(metrics)

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
                2, 2, figsize=self.figure_size, dpi=self.dpi
            )

            feature_types = list(feature_groups.keys())
            colors = plt.cm.Set3(np.linspace(0, 1, len(feature_types)))

            # 1. 成功率比较
            success_rates = []
            for feature_type in feature_types:
                rates = [m.success_rate for m in feature_groups[feature_type]]
                success_rates.append(np.mean(rates))

            bars1 = ax1.bar(feature_types, success_rates, color=colors, alpha=0.7)
            ax1.set_ylabel("平均成功率")
            ax1.set_title("成功率比较")
            ax1.grid(True, alpha=0.3)

            for bar, value in zip(bars1, success_rates):
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.01,
                    f"{value:.3f}",
                    ha="center",
                    va="bottom",
                )

            # 2. 处理速度比较
            fps_values = []
            for feature_type in feature_types:
                fps = [m.fps for m in feature_groups[feature_type]]
                fps_values.append(np.mean(fps))

            bars2 = ax2.bar(feature_types, fps_values, color=colors, alpha=0.7)
            ax2.set_ylabel("平均FPS")
            ax2.set_title("处理速度比较")
            ax2.grid(True, alpha=0.3)

            for bar, value in zip(bars2, fps_values):
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.1f}",
                    ha="center",
                    va="bottom",
                )

            # 3. 匹配质量比较
            inlier_ratios = []
            for feature_type in feature_types:
                ratios = [
                    m.matching.avg_inlier_ratio for m in feature_groups[feature_type]
                ]
                inlier_ratios.append(np.mean(ratios))

            bars3 = ax3.bar(feature_types, inlier_ratios, color=colors, alpha=0.7)
            ax3.set_ylabel("平均内点比例")
            ax3.set_title("匹配质量比较")
            ax3.grid(True, alpha=0.3)

            for bar, value in zip(bars3, inlier_ratios):
                height = bar.get_height()
                ax3.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.01,
                    f"{value:.3f}",
                    ha="center",
                    va="bottom",
                )

            # 4. 轨迹精度比较（如果有轨迹数据）
            trajectory_metrics = []
            for feature_type in feature_types:
                ate_values = [
                    m.trajectory.ate_rmse
                    for m in feature_groups[feature_type]
                    if m.trajectory is not None
                ]
                if ate_values:
                    trajectory_metrics.append(np.mean(ate_values))
                else:
                    trajectory_metrics.append(0.0)

            if any(v > 0 for v in trajectory_metrics):
                bars4 = ax4.bar(
                    feature_types, trajectory_metrics, color=colors, alpha=0.7
                )
                ax4.set_ylabel("平均ATE RMSE (m)")
                ax4.set_title("轨迹精度比较")
                ax4.grid(True, alpha=0.3)

                for bar, value in zip(bars4, trajectory_metrics):
                    if value > 0:
                        height = bar.get_height()
                        ax4.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height + height * 0.01,
                            f"{value:.3f}",
                            ha="center",
                            va="bottom",
                        )
            else:
                ax4.text(
                    0.5,
                    0.5,
                    "无轨迹数据",
                    ha="center",
                    va="center",
                    transform=ax4.transAxes,
                    fontsize=14,
                )
                ax4.set_title("轨迹精度比较")

            plt.suptitle(title, fontsize=16)
            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"特征类型比较图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制特征类型比较图失败: {e}")
            raise

    def plot_ransac_type_comparison(
        self,
        metrics_list: List[AlgorithmMetrics],
        title: str = "RANSAC类型比较",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制不同RANSAC类型的比较图

        Args:
            metrics_list: 算法指标列表
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            # 按RANSAC类型分组
            ransac_groups = {}
            for metrics in metrics_list:
                ransac_type = metrics.ransac_type
                if ransac_type not in ransac_groups:
                    ransac_groups[ransac_type] = []
                ransac_groups[ransac_type].append(metrics)

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
                2, 2, figsize=self.figure_size, dpi=self.dpi
            )

            ransac_types = list(ransac_groups.keys())
            colors = plt.cm.Set2(np.linspace(0, 1, len(ransac_types)))

            # 1. 收敛率比较
            convergence_rates = []
            for ransac_type in ransac_types:
                rates = [m.ransac.convergence_rate for m in ransac_groups[ransac_type]]
                convergence_rates.append(np.mean(rates))

            bars1 = ax1.bar(ransac_types, convergence_rates, color=colors, alpha=0.7)
            ax1.set_ylabel("平均收敛率")
            ax1.set_title("RANSAC收敛率比较")
            ax1.grid(True, alpha=0.3)

            for bar, value in zip(bars1, convergence_rates):
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.01,
                    f"{value:.3f}",
                    ha="center",
                    va="bottom",
                )

            # 2. 平均迭代次数比较
            avg_iterations = []
            for ransac_type in ransac_types:
                iterations = [
                    m.ransac.avg_iterations for m in ransac_groups[ransac_type]
                ]
                avg_iterations.append(np.mean(iterations))

            bars2 = ax2.bar(ransac_types, avg_iterations, color=colors, alpha=0.7)
            ax2.set_ylabel("平均迭代次数")
            ax2.set_title("RANSAC迭代次数比较")
            ax2.grid(True, alpha=0.3)

            for bar, value in zip(bars2, avg_iterations):
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.1f}",
                    ha="center",
                    va="bottom",
                )

            # 3. 处理时间比较
            processing_times = []
            for ransac_type in ransac_types:
                times = [
                    m.ransac.avg_processing_time_ms for m in ransac_groups[ransac_type]
                ]
                processing_times.append(np.mean(times))

            bars3 = ax3.bar(ransac_types, processing_times, color=colors, alpha=0.7)
            ax3.set_ylabel("平均处理时间 (ms)")
            ax3.set_title("RANSAC处理时间比较")
            ax3.grid(True, alpha=0.3)

            for bar, value in zip(bars3, processing_times):
                height = bar.get_height()
                ax3.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + height * 0.01,
                    f"{value:.2f}",
                    ha="center",
                    va="bottom",
                )

            # 4. 成功率比较
            success_rates = []
            for ransac_type in ransac_types:
                rates = [m.ransac.success_rate for m in ransac_groups[ransac_type]]
                success_rates.append(np.mean(rates))

            bars4 = ax4.bar(ransac_types, success_rates, color=colors, alpha=0.7)
            ax4.set_ylabel("平均成功率")
            ax4.set_title("RANSAC成功率比较")
            ax4.grid(True, alpha=0.3)

            for bar, value in zip(bars4, success_rates):
                height = bar.get_height()
                ax4.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.01,
                    f"{value:.3f}",
                    ha="center",
                    va="bottom",
                )

            plt.suptitle(title, fontsize=16)
            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"RANSAC类型比较图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制RANSAC类型比较图失败: {e}")
            raise

    def create_comprehensive_report(
        self, metrics_list: List[AlgorithmMetrics], save_path: Optional[Path] = None
    ) -> str:
        """
        创建综合比较报告

        Args:
            metrics_list: 算法指标列表
            save_path: 保存路径（可选）

        Returns:
            HTML报告字符串
        """
        try:
            # 计算各种统计信息
            best_success_rate = max(metrics_list, key=lambda x: x.success_rate)
            best_fps = max(metrics_list, key=lambda x: x.fps)
            best_inlier_ratio = max(
                metrics_list, key=lambda x: x.matching.avg_inlier_ratio
            )

            # 轨迹精度最佳（ATE RMSE最小）
            trajectory_metrics = [m for m in metrics_list if m.trajectory is not None]
            best_trajectory = (
                min(trajectory_metrics, key=lambda x: x.trajectory.ate_rmse)
                if trajectory_metrics
                else None
            )

            html_content = f"""
            <html>
            <head>
                <title>算法性能综合比较报告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .section {{ margin: 20px 0; }}
                    .best {{ color: #28a745; font-weight: bold; }}
                    .metric {{ margin: 10px 0; padding: 10px; border-left: 3px solid #007bff; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>算法性能综合比较报告</h1>
                    <p>总共测试了 {len(metrics_list)} 个算法配置</p>
                </div>
                
                <div class="section">
                    <h2>最佳性能算法</h2>
                    <div class="metric">
                        <strong>最高成功率:</strong> <span class="best">{best_success_rate.algorithm_key}</span> 
                        ({best_success_rate.success_rate:.3f})
                    </div>
                    <div class="metric">
                        <strong>最快处理速度:</strong> <span class="best">{best_fps.algorithm_key}</span> 
                        ({best_fps.fps:.1f} FPS)
                    </div>
                    <div class="metric">
                        <strong>最佳匹配质量:</strong> <span class="best">{best_inlier_ratio.algorithm_key}</span> 
                        (内点比例: {best_inlier_ratio.matching.avg_inlier_ratio:.3f})
                    </div>
            """

            if best_trajectory:
                html_content += f"""
                    <div class="metric">
                        <strong>最佳轨迹精度:</strong> <span class="best">{best_trajectory.algorithm_key}</span> 
                        (ATE RMSE: {best_trajectory.trajectory.ate_rmse:.3f}m)
                    </div>
                """

            html_content += """
                </div>
                
                <div class="section">
                    <h2>详细性能表格</h2>
                    <table>
                        <tr>
                            <th>算法</th>
                            <th>成功率</th>
                            <th>FPS</th>
                            <th>平均匹配数</th>
                            <th>内点比例</th>
                            <th>RANSAC迭代数</th>
                        </tr>
            """

            for metrics in sorted(
                metrics_list, key=lambda x: x.success_rate, reverse=True
            ):
                html_content += f"""
                        <tr>
                            <td>{metrics.algorithm_key}</td>
                            <td>{metrics.success_rate:.3f}</td>
                            <td>{metrics.fps:.1f}</td>
                            <td>{metrics.matching.avg_matches:.1f}</td>
                            <td>{metrics.matching.avg_inlier_ratio:.3f}</td>
                            <td>{metrics.ransac.avg_iterations:.1f}</td>
                        </tr>
                """

            html_content += """
                    </table>
                </div>
            </body>
            </html>
            """

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"综合比较报告已保存到: {save_path}")

            return html_content

        except Exception as e:
            logger.error(f"创建综合比较报告失败: {e}")
            raise
