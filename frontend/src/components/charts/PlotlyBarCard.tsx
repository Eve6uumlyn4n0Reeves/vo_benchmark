import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Stack } from '@mui/material';
import PlotlyWrapper from './PlotlyWrapper';

export interface PlotlyBarCardProps {
  title: string;
  unit?: string;
  series: Array<{ name: string; value: number; color?: string }>; // one bar per algorithm
  fmt?: (v: number) => string;
  yDomain?: [number, number] | 'auto';
  hint?: string; // optional hint text below the chart
  height?: number;
}

export const PlotlyBarCard: React.FC<PlotlyBarCardProps> = ({
  title,
  unit,
  series,
  fmt,
  yDomain = 'auto',
  hint,
  height = 260,
}) => {
  const x = series.map(s => s.name);
  const y = series.map(s => s.value ?? 0);
  const colors = series.map(s => s.color || '#1976d2');

  const data: any[] = [
    {
      type: 'bar',
      x,
      y,
      marker: { color: colors },
      text: y.map(v => (fmt ? fmt(v) : v?.toFixed?.(2) ?? String(v))),
      textposition: 'auto',
      hovertemplate: '%{x}: <b>%{text}</b><extra></extra>',
    },
  ];

  const layout: any = {
    height,
    margin: { l: 40, r: 20, t: 20, b: 40 },
    xaxis: { title: '', automargin: true },
    yaxis: {
      title: unit ? `${unit}` : '',
      rangemode: 'tozero',
      ...(yDomain === 'auto' ? {} : { range: yDomain }),
      tickfont: { size: 12 },
    },
    showlegend: false,
  };

  const config: any = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{title}</Typography>
          {unit && <Chip size="small" label={unit} variant="outlined" />}
        </Stack>
        <Box sx={{ width: '100%', height }}>
          <PlotlyWrapper data={data} layout={layout} config={config} style={{ width: '100%', height: '100%' }} />
        </Box>
        {hint && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>{hint}</Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default PlotlyBarCard;

