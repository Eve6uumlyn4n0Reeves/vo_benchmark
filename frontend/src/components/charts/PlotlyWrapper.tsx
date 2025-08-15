/**
 * Plotly 包装器组件，处理 Vite 环境下的兼容性问题
 */
import React from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';

interface PlotlyWrapperProps {
  data: any[];
  layout: any;
  config?: any;
  style?: React.CSSProperties;
  useResizeHandler?: boolean;
  onError?: (error: Error) => void;
}

// 动态加载 Plotly 组件的 Hook
const usePlotlyComponent = () => {
  const [PlotComponent, setPlotComponent] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;

    const loadPlotly = async () => {
      try {
        // 尝试多种导入方式
        console.log('开始加载 Plotly 组件...');
        
        // 方法1: 标准动态导入
        const plotlyModule = await import('react-plotly.js');
        console.log('Plotly 模块加载成功:', plotlyModule);
        
        if (mounted) {
          // 尝试不同的导出访问方式
          let PlotlyComponent = null;
          
          if (plotlyModule.default) {
            PlotlyComponent = plotlyModule.default;
            console.log('使用 default 导出');
          } else if ((plotlyModule as any).Plot) {
            PlotlyComponent = (plotlyModule as any).Plot;
            console.log('使用 Plot 导出');
          } else {
            PlotlyComponent = plotlyModule;
            console.log('使用整个模块');
          }
          
          setPlotComponent(() => PlotlyComponent);
          setLoading(false);
          console.log('✅ Plotly 组件设置成功');
        }
      } catch (err) {
        console.error('Plotly 加载失败:', err);
        
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Unknown error');
          setLoading(false);
        }
      }
    };

    loadPlotly();

    return () => {
      mounted = false;
    };
  }, []);

  return { PlotComponent, loading, error };
};

// 错误回退组件
const PlotlyFallback: React.FC<{ data: any[]; layout: any; error?: string }> = ({ 
  data, 
  layout, 
  error 
}) => (
  <Box 
    sx={{ 
      border: '1px solid #e0e0e0', 
      borderRadius: 1, 
      p: 3, 
      backgroundColor: '#fafafa',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: 300
    }}
  >
    <Typography variant="h6" color="primary" gutterBottom>
      📊 {layout?.title?.text || '图表'}
    </Typography>
    
    {data && data[0] && (
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        数据点数: {data[0].x?.length || data[0].y?.length || 0}
      </Typography>
    )}
    
    {error ? (
      <Typography variant="caption" color="error" sx={{ textAlign: 'center' }}>
        图表加载失败: {error}
      </Typography>
    ) : (
      <Typography variant="caption" color="text.secondary">
        图表组件加载中...
      </Typography>
    )}
  </Box>
);

// 加载中组件
const PlotlyLoading: React.FC = () => (
  <Box 
    sx={{ 
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: 300
    }}
  >
    <CircularProgress size={40} sx={{ mb: 2 }} />
    <Typography variant="body2" color="text.secondary">
      正在加载图表组件...
    </Typography>
  </Box>
);

// 主要的 Plotly 包装器组件
export const PlotlyWrapper: React.FC<PlotlyWrapperProps> = ({
  data,
  layout,
  config = { responsive: true },
  style = { width: '100%', height: '100%' },
  useResizeHandler = true,
  onError
}) => {
  const { PlotComponent, loading, error } = usePlotlyComponent();

  // 错误处理
  React.useEffect(() => {
    if (error && onError) {
      onError(new Error(error));
    }
  }, [error, onError]);

  // 加载中状态
  if (loading) {
    return <PlotlyLoading />;
  }

  // 错误状态或没有组件
  if (error || !PlotComponent) {
    return <PlotlyFallback data={data} layout={layout} error={error || undefined} />;
  }

  // 渲染真实的 Plotly 组件
  try {
    return (
      <PlotComponent
        data={data}
        layout={layout}
        config={config}
        style={style}
        useResizeHandler={useResizeHandler}
      />
    );
  } catch (renderError) {
    console.error('Plotly 渲染错误:', renderError);
    return (
      <PlotlyFallback 
        data={data} 
        layout={layout} 
        error={renderError instanceof Error ? renderError.message : 'Render error'} 
      />
    );
  }
};

export default PlotlyWrapper;
