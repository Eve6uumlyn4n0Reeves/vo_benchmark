#
# 功能: 轨迹可视化
#
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    _MATPLOTLIB_AVAILABLE = True
except Exception:  # ImportError and others
    plt = None
    Figure = object  # Fallback type
    _MATPLOTLIB_AVAILABLE = False
from typing import List, Optional, Dict, Any, Tuple
import logging
from pathlib import Path
from src.models.frame import FrameResult
from src.models.types import Pose

logger = logging.getLogger(__name__)


class TrajectoryVisualizer:
    """轨迹可视化器"""

    def __init__(self, figure_size: Tuple[int, int] = (12, 8), dpi: int = 100):
        """
        初始化轨迹可视化器

        Args:
            figure_size: 图像尺寸 (width, height)
            dpi: 图像分辨率
        """
        self.figure_size = figure_size
        self.dpi = dpi

    def plot_trajectory_comparison(
        self,
        ground_truth: List[Pose],
        estimated: List[Pose],
        title: str = "轨迹比较",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制地面真值与估计轨迹的比较图

        Args:
            ground_truth: 地面真值轨迹
            estimated: 估计轨迹
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            if not _MATPLOTLIB_AVAILABLE:
                raise ImportError(
                    "matplotlib 未安装。请安装可视化额外依赖：pip install -r requirements.txt 或 pip install '.[viz]'"
                )

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figure_size, dpi=self.dpi)

            # 提取位置信息
            gt_positions = np.array(
                [pose[:3, 3] for pose in ground_truth if pose is not None]
            )
            est_positions = np.array(
                [pose[:3, 3] for pose in estimated if pose is not None]
            )

            # 2D轨迹图 (X-Z平面)
            ax1.plot(
                gt_positions[:, 0],
                gt_positions[:, 2],
                "b-",
                label="地面真值",
                linewidth=2,
            )
            ax1.plot(
                est_positions[:, 0],
                est_positions[:, 2],
                "r--",
                label="估计轨迹",
                linewidth=2,
            )
            ax1.scatter(
                gt_positions[0, 0],
                gt_positions[0, 2],
                c="green",
                s=100,
                marker="o",
                label="起点",
            )
            ax1.scatter(
                gt_positions[-1, 0],
                gt_positions[-1, 2],
                c="red",
                s=100,
                marker="s",
                label="终点",
            )

            ax1.set_xlabel("X (m)")
            ax1.set_ylabel("Z (m)")
            ax1.set_title("2D轨迹 (X-Z平面)")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.axis("equal")

            # 3D轨迹图
            ax2 = fig.add_subplot(122, projection="3d")
            ax2.plot(
                gt_positions[:, 0],
                gt_positions[:, 1],
                gt_positions[:, 2],
                "b-",
                label="地面真值",
                linewidth=2,
            )
            ax2.plot(
                est_positions[:, 0],
                est_positions[:, 1],
                est_positions[:, 2],
                "r--",
                label="估计轨迹",
                linewidth=2,
            )
            ax2.scatter(
                gt_positions[0, 0],
                gt_positions[0, 1],
                gt_positions[0, 2],
                c="green",
                s=100,
                marker="o",
                label="起点",
            )
            ax2.scatter(
                gt_positions[-1, 0],
                gt_positions[-1, 1],
                gt_positions[-1, 2],
                c="red",
                s=100,
                marker="s",
                label="终点",
            )

            ax2.set_xlabel("X (m)")
            ax2.set_ylabel("Y (m)")
            ax2.set_zlabel("Z (m)")
            ax2.set_title("3D轨迹")
            ax2.legend()

            plt.suptitle(title, fontsize=16)
            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"轨迹比较图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制轨迹比较图失败: {e}")
            raise

    def plot_trajectory_error(
        self,
        frame_results: List[FrameResult],
        title: str = "轨迹误差分析",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制轨迹误差随时间变化图

        Args:
            frame_results: 帧结果列表
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            # 过滤有效的帧结果
            valid_frames = [
                f
                for f in frame_results
                if f.pose_error is not None and f.estimated_pose is not None
            ]

            if not valid_frames:
                raise ValueError("没有有效的轨迹误差数据")

            if not _MATPLOTLIB_AVAILABLE:
                raise ImportError(
                    "matplotlib 未安装。请安装可视化额外依赖：pip install -r requirements.txt 或 pip install '.[viz]'"
                )
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
                2, 2, figsize=self.figure_size, dpi=self.dpi
            )

            # 提取数据
            frame_ids = [f.frame_id for f in valid_frames]
            pose_errors = [f.pose_error for f in valid_frames]
            timestamps = [f.timestamp for f in valid_frames]

            # 计算累积误差
            cumulative_errors = np.cumsum(pose_errors)

            # 1. 位姿误差随帧数变化
            ax1.plot(frame_ids, pose_errors, "b-", linewidth=1.5)
            ax1.set_xlabel("帧ID")
            ax1.set_ylabel("位姿误差 (m)")
            ax1.set_title("位姿误差随帧数变化")
            ax1.grid(True, alpha=0.3)

            # 2. 位姿误差随时间变化
            ax2.plot(timestamps, pose_errors, "r-", linewidth=1.5)
            ax2.set_xlabel("时间 (s)")
            ax2.set_ylabel("位姿误差 (m)")
            ax2.set_title("位姿误差随时间变化")
            ax2.grid(True, alpha=0.3)

            # 3. 累积误差
            ax3.plot(frame_ids, cumulative_errors, "g-", linewidth=1.5)
            ax3.set_xlabel("帧ID")
            ax3.set_ylabel("累积误差 (m)")
            ax3.set_title("累积位姿误差")
            ax3.grid(True, alpha=0.3)

            # 4. 误差分布直方图
            ax4.hist(pose_errors, bins=30, alpha=0.7, color="orange", edgecolor="black")
            ax4.set_xlabel("位姿误差 (m)")
            ax4.set_ylabel("频次")
            ax4.set_title("位姿误差分布")
            ax4.grid(True, alpha=0.3)

            # 添加统计信息
            mean_error = np.mean(pose_errors)
            std_error = np.std(pose_errors)
            max_error = np.max(pose_errors)

            stats_text = f"均值: {mean_error:.3f}m\n标准差: {std_error:.3f}m\n最大值: {max_error:.3f}m"
            ax4.text(
                0.7,
                0.9,
                stats_text,
                transform=ax4.transAxes,
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
                verticalalignment="top",
            )

            plt.suptitle(title, fontsize=16)
            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"轨迹误差图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制轨迹误差图失败: {e}")
            raise

    def plot_multiple_trajectories(
        self,
        trajectories: Dict[str, List[Pose]],
        ground_truth: Optional[List[Pose]] = None,
        title: str = "多轨迹比较",
        save_path: Optional[Path] = None,
    ) -> Figure:
        """
        绘制多条轨迹的比较图

        Args:
            trajectories: 轨迹字典 {算法名: 轨迹}
            ground_truth: 地面真值轨迹（可选）
            title: 图像标题
            save_path: 保存路径（可选）

        Returns:
            matplotlib Figure对象
        """
        try:
            fig, ax = plt.subplots(1, 1, figsize=self.figure_size, dpi=self.dpi)

            colors = plt.cm.tab10(np.linspace(0, 1, len(trajectories)))

            # 绘制地面真值
            if ground_truth:
                gt_positions = np.array(
                    [pose[:3, 3] for pose in ground_truth if pose is not None]
                )
                ax.plot(
                    gt_positions[:, 0],
                    gt_positions[:, 2],
                    "k-",
                    label="地面真值",
                    linewidth=3,
                    alpha=0.8,
                )
                ax.scatter(
                    gt_positions[0, 0],
                    gt_positions[0, 2],
                    c="green",
                    s=100,
                    marker="o",
                    label="起点",
                )
                ax.scatter(
                    gt_positions[-1, 0],
                    gt_positions[-1, 2],
                    c="red",
                    s=100,
                    marker="s",
                    label="终点",
                )

            # 绘制估计轨迹
            for i, (name, trajectory) in enumerate(trajectories.items()):
                positions = np.array(
                    [pose[:3, 3] for pose in trajectory if pose is not None]
                )
                if len(positions) > 0:
                    ax.plot(
                        positions[:, 0],
                        positions[:, 2],
                        color=colors[i],
                        linestyle="--",
                        label=name,
                        linewidth=2,
                    )

            ax.set_xlabel("X (m)")
            ax.set_ylabel("Z (m)")
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.axis("equal")

            plt.tight_layout()

            if save_path:
                fig.savefig(save_path, dpi=self.dpi, bbox_inches="tight")
                logger.info(f"多轨迹比较图已保存到: {save_path}")

            return fig

        except Exception as e:
            logger.error(f"绘制多轨迹比较图失败: {e}")
            raise

    def create_trajectory_animation(
        self,
        ground_truth: List[Pose],
        estimated: List[Pose],
        save_path: Optional[Path] = None,
    ) -> str:
        """
        创建轨迹动画（返回HTML字符串或保存为文件）

        Args:
            ground_truth: 地面真值轨迹
            estimated: 估计轨迹
            save_path: 保存路径（可选）

        Returns:
            HTML字符串或文件路径
        """
        try:
            # 这里可以使用plotly创建交互式动画
            # 由于依赖关系，这里提供一个简化的实现

            html_content = f"""
            <html>
            <head>
                <title>轨迹动画</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            </head>
            <body>
                <div id="trajectory-plot" style="width:100%;height:600px;"></div>
                <script>
                    // 这里可以添加plotly.js代码来创建交互式轨迹动画
                    var data = [
                        {{
                            x: {[pose[0, 3] for pose in ground_truth if pose is not None]},
                            y: {[pose[2, 3] for pose in ground_truth if pose is not None]},
                            mode: 'lines+markers',
                            name: '地面真值',
                            line: {{color: 'blue'}}
                        }},
                        {{
                            x: {[pose[0, 3] for pose in estimated if pose is not None]},
                            y: {[pose[2, 3] for pose in estimated if pose is not None]},
                            mode: 'lines+markers',
                            name: '估计轨迹',
                            line: {{color: 'red', dash: 'dash'}}
                        }}
                    ];
                    
                    var layout = {{
                        title: '轨迹比较',
                        xaxis: {{title: 'X (m)'}},
                        yaxis: {{title: 'Z (m)'}},
                        showlegend: true
                    }};
                    
                    Plotly.newPlot('trajectory-plot', data, layout);
                </script>
            </body>
            </html>
            """

            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"轨迹动画已保存到: {save_path}")
                return str(save_path)

            return html_content

        except Exception as e:
            logger.error(f"创建轨迹动画失败: {e}")
            raise
