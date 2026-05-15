import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

const Charts = ({ metrics }) => {
  if (!metrics) return null;

  const data = [
    { name: 'Perplexity', value: metrics.perplexity, max: 100 },
    { name: 'Burstiness', value: metrics.burstiness, max: 100 },
    { name: 'Entropy', value: metrics.entropy * 10, max: 100 }, // Scale for visualization
    { name: 'Variation', value: metrics.sentence_variation * 100, max: 100 },
    { name: 'AI Model', value: metrics.ai_model_score, max: 100 },
  ];

  const getColor = (name, value) => {
    if (name === 'AI Model') return value > 70 ? '#ef4444' : '#22c55e';
    return '#3b82f6';
  };

  return (
    <div className="w-full h-64 bg-white/5 p-4 rounded-2xl border border-white/10">
      <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Forensic Metric Analysis</h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#9ca3af', fontSize: 12 }}
          />
          <YAxis hide domain={[0, 100]} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }}
            itemStyle={{ color: '#fff' }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.name, entry.value)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Charts;
