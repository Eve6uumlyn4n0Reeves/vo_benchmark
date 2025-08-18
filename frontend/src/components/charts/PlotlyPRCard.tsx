import React from 'react';
import { Box, Stack, Typography, Chip } from '@mui/material';
import PlotlyWrapper from './PlotlyWrapper';

export interface PRSeries {
  name: string;
  color?: string;
  recalls: number[];
  precisions: number[];
  thresholds?: number[];
  f1_scores?: number[];
  auc?: number;
}

export interface PlotlyPRCardProps {
  title?: string;
  series: PRSeries[];
  baseline?: { precision?: number; recall?: number };
  height?: number;
}

export const PlotlyPRCard: React.FC<PlotlyPRCardProps> = ({ title = 'PR 曲线对比', series, height = 420 }) => {
  const traces: any[] = [];

  series.forEach((s) => {
    const n = Math.min(s.recalls.length, s.precisions.length);
    const x = s.recalls.slice(0, n);
    const y = s.precisions.slice(0, n);
    traces.push({
      type: 'scatter', mode: 'lines', x, y, name: s.auc != null ? `${s.name} (AUC: ${s.auc.toFixed(3)})` : s.name, line: { width: 2, color: s.color },
      hovertemplate: 'R=%{x:.3f}<br>P=%{y:.3f}<extra></extra>'
    });
  });

  // iso-F1 参考线
  [0.3, 0.5, 0.7, 0.9].forEach((f1) => {
    const x = [0, f1];
    const y = [f1, 0];
    traces.push({ type: 'scatter', mode: 'lines', x, y, name: `F1=${f1}`, line: { dash: 'dot', color: '#bdbdbd', width: 1 }, hoverinfo: 'skip', showlegend: false });
  });

  const layout: any = {
    height,
    margin: { l: 40, r: 10, t: 20, b: 40 },
    xaxis: { title: 'Recall', range: [0,1] },
    yaxis: { title: 'Precision', range: [0,1] },
    showlegend: true,
    legend: { orientation: 'h', x: 0, y: -0.15 },
  };

  const config: any = { responsive: true, displaylogo: false };

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>{title}</Typography>
        {series?.length > 0 && (
          <Stack direction="row" spacing={1}>
            {series.map(s => (
              <Chip key={s.name} label={`${s.name}${s.auc != null ? ` (AUC ${s.auc.toFixed(3)})` : ''}`} size="small" />
            ))}
          </Stack>
        )}
      </Stack>
      <Box sx={{ width: '100%', height }}>
        <PlotlyWrapper data={traces} layout={layout} config={config} style={{ width: '100%', height: '100%' }} />
      </Box>
    </Box>
  );
};

export default PlotlyPRCard;

