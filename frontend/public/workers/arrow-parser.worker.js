/**
 * Arrow数据解析Worker
 * 在后台线程中解析Arrow格式的轨迹和PR曲线数据
 */

// 动态导入Apache Arrow（支持ES模块和UMD）
let Arrow = null;

// 初始化Arrow库
async function initArrow() {
  if (Arrow) return Arrow;
  
  try {
    // 尝试ES模块导入
    Arrow = await import('https://cdn.skypack.dev/apache-arrow@14.0.1');
    return Arrow;
  } catch (e) {
    console.warn('ES模块导入失败，尝试UMD:', e);
    
    // 回退到UMD版本
    try {
      importScripts('https://unpkg.com/apache-arrow@14.0.1/dist/Arrow.es2015.min.js');
      Arrow = self.Arrow;
      return Arrow;
    } catch (e2) {
      console.error('Arrow库加载失败:', e2);
      throw new Error('无法加载Apache Arrow库');
    }
  }
}

// 解析轨迹数据
async function parseTrajectory(arrayBuffer) {
  const arrow = await initArrow();
  
  try {
    const table = arrow.tableFromIPC(new Uint8Array(arrayBuffer));
    
    const result = {
      estimated_trajectory: [],
      groundtruth_trajectory: [],
      reference_trajectory: [],
      metadata: {}
    };
    
    // 提取元数据
    if (table.schema.metadata) {
      const metadata = {};
      for (const [key, value] of table.schema.metadata) {
        metadata[key] = value;
      }
      result.metadata = metadata;
    }
    
    const numRows = table.numRows;
    
    // 估计轨迹（必需）
    if (table.getChild('x') && table.getChild('y') && table.getChild('z') && table.getChild('t')) {
      const x = table.getChild('x').toArray();
      const y = table.getChild('y').toArray();
      const z = table.getChild('z').toArray();
      const t = table.getChild('t').toArray();
      const frameIds = table.getChild('frame_id')?.toArray() || Array.from({length: numRows}, (_, i) => i);
      
      for (let i = 0; i < numRows; i++) {
        result.estimated_trajectory.push({
          x: x[i],
          y: y[i],
          z: z[i],
          timestamp: t[i],
          frame_id: frameIds[i]
        });
      }
    }
    
    // 真值轨迹（可选）
    if (table.getChild('gt_x') && table.getChild('gt_y') && table.getChild('gt_z') && table.getChild('gt_t')) {
      const gtX = table.getChild('gt_x').toArray();
      const gtY = table.getChild('gt_y').toArray();
      const gtZ = table.getChild('gt_z').toArray();
      const gtT = table.getChild('gt_t').toArray();
      
      for (let i = 0; i < numRows; i++) {
        result.groundtruth_trajectory.push({
          x: gtX[i],
          y: gtY[i],
          z: gtZ[i],
          timestamp: gtT[i]
        });
      }
    }
    
    // 参考轨迹（可选）
    if (table.getChild('ref_x') && table.getChild('ref_y') && table.getChild('ref_z') && table.getChild('ref_t')) {
      const refX = table.getChild('ref_x').toArray();
      const refY = table.getChild('ref_y').toArray();
      const refZ = table.getChild('ref_z').toArray();
      const refT = table.getChild('ref_t').toArray();
      
      for (let i = 0; i < numRows; i++) {
        result.reference_trajectory.push({
          x: refX[i],
          y: refY[i],
          z: refZ[i],
          timestamp: refT[i]
        });
      }
    }
    
    return result;
    
  } catch (error) {
    console.error('解析轨迹Arrow数据失败:', error);
    throw error;
  }
}

// 解析PR曲线数据
async function parsePRCurve(arrayBuffer) {
  const arrow = await initArrow();
  
  try {
    const table = arrow.tableFromIPC(new Uint8Array(arrayBuffer));
    
    const result = {
      precisions: [],
      recalls: [],
      thresholds: [],
      f1_scores: [],
      metadata: {}
    };
    
    // 提取元数据
    if (table.schema.metadata) {
      const metadata = {};
      for (const [key, value] of table.schema.metadata) {
        metadata[key] = value;
      }
      result.metadata = metadata;
      
      // 转换数值型元数据
      if (metadata.auc_score) result.auc_score = parseFloat(metadata.auc_score);
      if (metadata.optimal_precision) result.optimal_precision = parseFloat(metadata.optimal_precision);
      if (metadata.optimal_recall) result.optimal_recall = parseFloat(metadata.optimal_recall);
      if (metadata.optimal_threshold) result.optimal_threshold = parseFloat(metadata.optimal_threshold);
      if (metadata.max_f1_score) result.max_f1_score = parseFloat(metadata.max_f1_score);
      if (metadata.algorithm) result.algorithm = metadata.algorithm;
    }
    
    // 提取列数据
    if (table.getChild('precision')) {
      result.precisions = table.getChild('precision').toArray();
    }
    if (table.getChild('recall')) {
      result.recalls = table.getChild('recall').toArray();
    }
    if (table.getChild('threshold')) {
      result.thresholds = table.getChild('threshold').toArray();
    }
    if (table.getChild('f1')) {
      result.f1_scores = table.getChild('f1').toArray();
    }
    
    // 原始数据（如果存在）
    if (table.getChild('raw_precision')) {
      result.raw_precisions = table.getChild('raw_precision').toArray();
      result.raw_recalls = table.getChild('raw_recall').toArray();
      result.raw_thresholds = table.getChild('raw_threshold').toArray();
      if (table.getChild('raw_f1')) {
        result.raw_f1_scores = table.getChild('raw_f1').toArray();
      }
    }
    
    return result;
    
  } catch (error) {
    console.error('解析PR曲线Arrow数据失败:', error);
    throw error;
  }
}

// 消息处理
self.onmessage = async function(e) {
  const { id, type, data } = e.data;
  
  try {
    let result;
    
    switch (type) {
      case 'parseTrajectory':
        result = await parseTrajectory(data);
        break;
        
      case 'parsePRCurve':
        result = await parsePRCurve(data);
        break;
        
      default:
        throw new Error(`未知的解析类型: ${type}`);
    }
    
    // 发送成功结果
    self.postMessage({
      id,
      success: true,
      result
    });
    
  } catch (error) {
    // 发送错误结果
    self.postMessage({
      id,
      success: false,
      error: {
        message: error.message,
        stack: error.stack
      }
    });
  }
};
