import React from 'react';
import { Card, CardContent, Typography, Box, Stack, FormControlLabel, Switch } from '@mui/material';
import PlotlyWrapper from './PlotlyWrapper';

export interface RadarMetric {
  label: string;
  values: Array<{ name: string; value: number; color?: string }>; // one value per algorithm
}

export interface PlotlyRadarCardProps {
  title: string;
  metrics: RadarMetric[]; // each as one axis
  normalize?: boolean; // default true
  height?: number;
}

export const PlotlyRadarCard: React.FC<PlotlyRadarCardProps> = ({ title, metrics, normalize = true, height = 340 }) => {
  const [norm, setNorm] = React.useState(normalize);

  const labels = metrics.map(m => m.label);
  const algos = metrics[0]?.values?.map(v => v.name) || [];

  const perAlgoTraces = algos.map((algo) => {
    const raw = metrics.map(m => (m.values.find(v => v.name === algo)?.value ?? 0));
    let values = raw;
    if (norm) {
      const min = Math.min(...raw);
      const max = Math.max(...raw);
      const den = max === min ? 1 : (max - min);
      values = raw.map(v => (v - min) / den);
    }
    return {
      type: 'scatterpolar',
      r: values,
      theta: labels,
      fill: 'toself',
      name: algo,
      line: { width: 2 },
      opacity: 0.6,
    } as any;
  });

  const layout: any = {
    polar: {
      radialaxis: {
        visible: true,
        range: [0, 1],
        tickformat: '.0%',
      },
    },
    showlegend: true,
    margin: { l: 40, r: 20, t: 20, b: 20 },
    height,
  };

  const config: any = { responsive: true, displaylogo: false };

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{title}</Typography>
          <FormControlLabel control={<Switch size="small" checked={norm} onChange={(_, v) => setNorm(v)} />} label="归一化(0-1)" />
        </Stack>
        <Box sx={{ width: '100%', height }}>
          <PlotlyWrapper data={perAlgoTraces as any} layout={layout} config={config} style={{ width: '100%', height: '100%' }} />
        </Box>
      </CardContent>
    </Card>
  );
};

export default PlotlyRadarCard;

