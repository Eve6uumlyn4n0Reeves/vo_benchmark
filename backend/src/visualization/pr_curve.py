#
# 功能: PR曲线可视化
#
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import List, Optional, Dict, Any, Tuple
import logging
from pathlib import Path
from src.models.evaluation import PRCurveData

logger = logging.getLogger(__name__)


class PRCurveVisualizer:
    """PR曲线可视化器"""

    def __init__(self, figure_size: Tuple[int, int] = (10, 8), dpi: int = 100):
        """
        初始化PR曲线可视化器

        Args:
            figure_size: 图像尺寸 (width, height)
            dpi: 图像分辨率
        """
        self.figure_size = figure_size
        self.dpi = dpi

    def plot_single_pr_curve(
        self,
        pr_data: PRCurveData,
        title: Optional[str] = None,
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制单个PR曲线

        Args:
            pr_data: PR曲线数据
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(1, 1, figsize=self.figure_size, dpi=self.dpi)

            # 绘制PR曲线
            ax.plot(
                pr_data.recalls,
                pr_data.precisions,
                "b-",
                linewidth=2,
                label=f"{pr_data.algorithm} (AUC={pr_data.auc_score:.3f})",
            )

            # 标记最优点
            ax.scatter(
                pr_data.optimal_recall,
                pr_data.optimal_precision,
                color="red",
                s=100,
                marker="*",
                zorder=5,
                label=f"最优点 (F1={pr_data.max_f1_score:.3f})",
            )

            # 添加随机分类器基线
            ax.plot([0, 1], [0.5, 0.5], "k--", alpha=0.5, label="随机分类器")

            ax.set_xlabel("召回率 (Recall)")
            ax.set_ylabel("精确率 (Precision)")
            ax.set_title(title or f"{pr_data.algorithm} PR曲线")
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_xlim((0.0, 1.0))
            ax.set_ylim((0.0, 1.0))

            # 添加统计信息文本框
            stats_text = (
                f"AUC: {pr_data.auc_score:.3f}\n"
                f"最大F1: {pr_data.max_f1_score:.3f}\n"
                f"最优阈值: {pr_data.optimal_threshold:.3f}\n"
                f"最优精确率: {pr_data.optimal_precision:.3f}\n"
                f"最优召回率: {pr_data.optimal_recall:.3f}"
            )

            ax.text(
                0.02,
                0.02,
                stats_text,
                transform=ax.transAxes,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
                verticalalignment="bottom",
            )

            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"PR曲线图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制PR曲线失败: {e}")
            raise

    def plot_multiple_pr_curves(
        self,
        pr_curves: List[PRCurveData],
        title: str = "PR曲线比较",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制多个PR曲线的比较图

        Args:
            pr_curves: PR曲线数据列表
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(1, 1, figsize=self.figure_size, dpi=self.dpi)

            colors = plt.cm.tab10(np.linspace(0, 1, len(pr_curves)))

            for i, pr_data in enumerate(pr_curves):
                # 绘制PR曲线
                ax.plot(
                    pr_data.recalls,
                    pr_data.precisions,
                    color=colors[i],
                    linewidth=2,
                    label=f"{pr_data.algorithm} (AUC={pr_data.auc_score:.3f})",
                )

                # 标记最优点
                ax.scatter(
                    pr_data.optimal_recall,
                    pr_data.optimal_precision,
                    color=colors[i],
                    s=80,
                    marker="*",
                    zorder=5,
                )

            # 添加随机分类器基线
            ax.plot([0, 1], [0.5, 0.5], "k--", alpha=0.5, label="随机分类器")

            ax.set_xlabel("召回率 (Recall)")
            ax.set_ylabel("精确率 (Precision)")
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1])

            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"多PR曲线比较图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制多PR曲线比较图失败: {e}")
            raise

    def plot_pr_curve_with_thresholds(
        self,
        pr_data: PRCurveData,
        title: Optional[str] = None,
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制带阈值信息的PR曲线

        Args:
            pr_data: PR曲线数据
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
                2, 2, figsize=self.figure_size, dpi=self.dpi
            )

            # 1. PR曲线
            ax1.plot(pr_data.recalls, pr_data.precisions, "b-", linewidth=2)
            ax1.scatter(
                pr_data.optimal_recall,
                pr_data.optimal_precision,
                color="red",
                s=100,
                marker="*",
                zorder=5,
            )
            ax1.set_xlabel("召回率")
            ax1.set_ylabel("精确率")
            ax1.set_title("PR曲线")
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim([0, 1])
            ax1.set_ylim([0, 1])

            # 2. 精确率随阈值变化
            ax2.plot(pr_data.thresholds, pr_data.precisions, "g-", linewidth=2)
            ax2.axvline(
                pr_data.optimal_threshold, color="red", linestyle="--", alpha=0.7
            )
            ax2.set_xlabel("阈值")
            ax2.set_ylabel("精确率")
            ax2.set_title("精确率随阈值变化")
            ax2.grid(True, alpha=0.3)

            # 3. 召回率随阈值变化
            ax3.plot(pr_data.thresholds, pr_data.recalls, "orange", linewidth=2)
            ax3.axvline(
                pr_data.optimal_threshold, color="red", linestyle="--", alpha=0.7
            )
            ax3.set_xlabel("阈值")
            ax3.set_ylabel("召回率")
            ax3.set_title("召回率随阈值变化")
            ax3.grid(True, alpha=0.3)

            # 4. F1分数随阈值变化
            if hasattr(pr_data, "f1_scores") and pr_data.f1_scores:
                ax4.plot(pr_data.thresholds, pr_data.f1_scores, "purple", linewidth=2)
                ax4.axvline(
                    pr_data.optimal_threshold, color="red", linestyle="--", alpha=0.7
                )
                ax4.axhline(
                    pr_data.max_f1_score, color="red", linestyle="--", alpha=0.7
                )
                ax4.set_xlabel("阈值")
                ax4.set_ylabel("F1分数")
                ax4.set_title("F1分数随阈值变化")
                ax4.grid(True, alpha=0.3)
            else:
                ax4.text(
                    0.5,
                    0.5,
                    "F1分数数据不可用",
                    ha="center",
                    va="center",
                    transform=ax4.transAxes,
                    fontsize=12,
                )
                ax4.set_title("F1分数随阈值变化")

            plt.suptitle(title or f"{pr_data.algorithm} PR曲线分析", fontsize=16)
            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"PR曲线阈值分析图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制PR曲线阈值分析图失败: {e}")
            raise

    def create_pr_curve_summary_table(
        self, pr_curves: List[PRCurveData], save_path: Optional[Path] = None
    ) -> str:
        """
        创建PR曲线摘要表格

        Args:
            pr_curves: PR曲线数据列表
            save_path: 保存路径（可选）

        Returns:
            HTML表格字符串
        """
        try:
            # 按AUC分数排序
            sorted_curves = sorted(pr_curves, key=lambda x: x.auc_score, reverse=True)

            html_content = """
            <html>
            <head>
                <title>PR曲线摘要</title>
                <style>
                    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                    .best { background-color: #d4edda; }
                    .worst { background-color: #f8d7da; }
                </style>
            </head>
            <body>
                <h2>PR曲线性能摘要</h2>
                <table>
                    <tr>
                        <th>排名</th>
                        <th>算法</th>
                        <th>AUC分数</th>
                        <th>最大F1分数</th>
                        <th>最优阈值</th>
                        <th>最优精确率</th>
                        <th>最优召回率</th>
                    </tr>
            """

            for i, pr_data in enumerate(sorted_curves):
                row_class = ""
                if i == 0:
                    row_class = "best"
                elif i == len(sorted_curves) - 1:
                    row_class = "worst"

                html_content += f"""
                    <tr class="{row_class}">
                        <td>{i + 1}</td>
                        <td>{pr_data.algorithm}</td>
                        <td>{pr_data.auc_score:.4f}</td>
                        <td>{pr_data.max_f1_score:.4f}</td>
                        <td>{pr_data.optimal_threshold:.4f}</td>
                        <td>{pr_data.optimal_precision:.4f}</td>
                        <td>{pr_data.optimal_recall:.4f}</td>
                    </tr>
                """

            html_content += """
                </table>
                <p><strong>说明：</strong></p>
                <ul>
                    <li>绿色背景表示最佳性能</li>
                    <li>红色背景表示最差性能</li>
                    <li>AUC分数越高越好</li>
                    <li>F1分数是精确率和召回率的调和平均数</li>
                </ul>
            </body>
            </html>
            """

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"PR曲线摘要表格已保存到: {save_path}")

            return html_content

        except Exception as e:
            logger.error(f"创建PR曲线摘要表格失败: {e}")
            raise
