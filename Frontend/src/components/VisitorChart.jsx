import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import './VisitorChart.css';

const VisitorChart = ({ data = [] }) => {
    // Custom tooltip
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="chart-tooltip">
                    <p className="tooltip-label">{label}</p>
                    <div className="tooltip-items">
                        {payload.map((entry, index) => (
                            <div key={index} className="tooltip-item" style={{ color: entry.color }}>
                                <span className="tooltip-name">{entry.name}:</span>
                                <span className="tooltip-value">{entry.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="visitor-chart">
            <div className="chart-header">
                <div>
                    <h3 className="chart-title">Live Event Signals</h3>
                    <p className="chart-subtitle">Real-time event tracking (Last 24 hours)</p>
                </div>
            </div>

            <div className="chart-container">
                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorWebsocket" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorTickets" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorWebhooks" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.3} />
                        <XAxis
                            dataKey="label"
                            stroke="var(--color-text-tertiary)"
                            style={{ fontSize: '12px' }}
                            tick={{ fill: 'var(--color-text-tertiary)' }}
                        />
                        <YAxis
                            stroke="var(--color-text-tertiary)"
                            style={{ fontSize: '12px' }}
                            tick={{ fill: 'var(--color-text-tertiary)' }}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend
                            wrapperStyle={{
                                fontSize: '12px',
                                color: 'var(--color-text-secondary)'
                            }}
                        />
                        <Area
                            type="monotone"
                            dataKey="websocket"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorWebsocket)"
                            name="WebSocket Events"
                            animationDuration={300}
                        />
                        <Area
                            type="monotone"
                            dataKey="tickets"
                            stroke="#10b981"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorTickets)"
                            name="Tickets"
                            animationDuration={300}
                        />
                        <Area
                            type="monotone"
                            dataKey="webhooks"
                            stroke="#f59e0b"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorWebhooks)"
                            name="Webhooks"
                            animationDuration={300}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default VisitorChart;
