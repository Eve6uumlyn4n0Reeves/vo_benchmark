#
# 功能: 实验数据清单API端点
#
import logging
from flask import Blueprint, jsonify, request, current_app, send_file
from pathlib import Path
from typing import Optional

from src.storage.experiment import ExperimentStorage

logger = logging.getLogger(__name__)

# 创建蓝图
manifest_bp = Blueprint('manifest', __name__, url_prefix='/api/v1')


@manifest_bp.route('/results/<experiment_id>/<algorithm_key>/manifest', methods=['GET'])
def get_manifest(experiment_id: str, algorithm_key: str):
    """获取实验数据清单
    
    返回包含轨迹、PR曲线、帧数据等资源位置和元信息的清单
    """
    try:
        storage = ExperimentStorage()
        
        # 尝试加载现有清单
        manifest = storage.get_manifest(experiment_id, algorithm_key)
        
        if manifest is None:
            # 如果没有清单，动态生成一个
            manifest = storage.generate_manifest(experiment_id, algorithm_key)
        
        # 添加基础URL前缀
        base_url = request.url_root.rstrip('/')
        manifest = _add_base_urls(manifest, base_url)
        
        return jsonify(manifest)
        
    except Exception as e:
        logger.error(f"获取清单失败: {e}")
        return jsonify({
            "error": "Failed to get manifest",
            "message": str(e)
        }), 500


@manifest_bp.route('/assets/experiments/<path:file_path>', methods=['GET'])
def serve_asset(file_path: str):
    """提供静态资源文件服务
    
    支持Arrow文件、JSON文件等的直接下载
    """
    try:
        storage = ExperimentStorage()
        asset_path = storage.root_dir / "experiments" / file_path
        
        if not asset_path.exists():
            return jsonify({
                "error": "Asset not found",
                "path": file_path
            }), 404
        
        # 安全检查：确保路径在允许的目录内
        try:
            asset_path.resolve().relative_to(storage.root_dir.resolve())
        except ValueError:
            return jsonify({
                "error": "Access denied",
                "message": "Path outside allowed directory"
            }), 403
        
        # 根据文件扩展名设置MIME类型
        mime_type = _get_mime_type(asset_path)
        
        # 设置缓存头
        cache_control = "public, max-age=31536000, immutable"  # 1年缓存
        
        return send_file(
            asset_path,
            mimetype=mime_type,
            as_attachment=False,
            cache_timeout=31536000,
            add_etags=True,
            conditional=True
        )
        
    except Exception as e:
        logger.error(f"提供资源文件失败: {e}")
        return jsonify({
            "error": "Failed to serve asset",
            "message": str(e)
        }), 500


@manifest_bp.route('/results/<experiment_id>/<algorithm_key>/trajectory', methods=['GET'])
def get_trajectory_optimized(experiment_id: str, algorithm_key: str):
    """优化的轨迹数据获取端点
    
    支持参数：
    - max_points: 最大点数限制（默认1500）
    - format: 返回格式 json|arrow（默认json）
    - include_reference: 是否包含参考轨迹（默认false）
    """
    try:
        storage = ExperimentStorage()
        
        # 解析参数
        max_points = request.args.get('max_points', '1500')
        format_type = request.args.get('format', 'json')
        include_reference = request.args.get('include_reference', 'false').lower() == 'true'
        
        # 解析max_points
        if max_points == 'full':
            ui_version = False
        else:
            try:
                max_points_int = int(max_points)
                ui_version = max_points_int <= 1500
            except ValueError:
                ui_version = True
        
        # 优先尝试Arrow格式
        trajectory_data = storage.get_trajectory_arrow(experiment_id, algorithm_key, ui_version)
        
        if trajectory_data is None:
            # 回退到JSON格式
            trajectory_data = storage.get_trajectory(experiment_id, algorithm_key)
            
            if trajectory_data is None:
                return jsonify({
                    "error": "Trajectory not found",
                    "experiment_id": experiment_id,
                    "algorithm_key": algorithm_key
                }), 404
        
        # 如果不包含参考轨迹，移除它
        if not include_reference:
            trajectory_data.pop('reference_trajectory', None)
            trajectory_data.pop('ref', None)
        
        # 如果请求Arrow格式，返回二进制数据
        if format_type == 'arrow':
            # TODO: 直接返回Arrow二进制数据
            pass
        
        return jsonify(trajectory_data)
        
    except Exception as e:
        logger.error(f"获取轨迹数据失败: {e}")
        return jsonify({
            "error": "Failed to get trajectory",
            "message": str(e)
        }), 500


def _add_base_urls(manifest: dict, base_url: str) -> dict:
    """为清单中的URL添加基础URL前缀"""
    def add_base_to_url(url: str) -> str:
        if url.startswith('/'):
            return base_url + url
        return url
    
    # 深度遍历并更新URL
    def update_urls(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'url' and isinstance(value, str):
                    obj[key] = add_base_to_url(value)
                else:
                    update_urls(value)
        elif isinstance(obj, list):
            for item in obj:
                update_urls(item)
    
    result = manifest.copy()
    update_urls(result)
    return result


def _get_mime_type(file_path: Path) -> str:
    """根据文件扩展名获取MIME类型"""
    suffix = file_path.suffix.lower()
    
    mime_types = {
        '.arrow': 'application/vnd.apache.arrow.stream',
        '.json': 'application/json',
        '.gz': 'application/gzip',
        '.parquet': 'application/octet-stream',
    }
    
    # 处理复合扩展名
    if file_path.name.endswith('.json.gz'):
        return 'application/gzip'
    elif file_path.name.endswith('.ui.arrow'):
        return 'application/vnd.apache.arrow.stream'
    
    return mime_types.get(suffix, 'application/octet-stream')


# 注册错误处理器
@manifest_bp.errorhandler(404)
def handle_not_found(e):
    return jsonify({
        "error": "Resource not found",
        "message": "The requested resource was not found"
    }), 404


@manifest_bp.errorhandler(500)
def handle_server_error(e):
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500
