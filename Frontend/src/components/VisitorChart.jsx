import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import './VisitorChart.css';

const VisitorChart = ({ data = [] }) => {
    // Custom tooltip - Sharp Terminal Style
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="chart-tooltip">
                    <p className="tooltip-label">{label}</p>
                    <div className="tooltip-items">
                        {payload.map((entry, index) => (
                            <div key={index} className="tooltip-item" style={{ color: entry.color }}>
                                <span className="tooltip-name">{entry.name}</span>
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
                    <h3 className="chart-title">SYSTEM EVENTS OVERVIEW (24H)</h3>
                    <p className="chart-subtitle">Real-time Signal Analysis</p>
                </div>
            </div>

            <div className="chart-container">
                <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorWebsocket" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorTickets" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} /> {/* Red for tickets */}
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorWebhooks" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="0" stroke="#333" vertical={false} />
                        <XAxis
                            dataKey="label"
                            stroke="#666"
                            tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'monospace' }}
                            tickLine={false}
                            axisLine={false}
                            interval="preserveStartEnd"
                        />
                        <YAxis
                            stroke="#666"
                            tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'monospace' }}
                            tickLine={false}
                            axisLine={false}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#fff', strokeWidth: 1, strokeDasharray: '3 3' }} />
                        <Legend
                            wrapperStyle={{
                                fontSize: '10px',
                                fontFamily: 'monospace',
                                color: '#94a3b8',
                                textTransform: 'uppercase'
                            }}
                        />
                        <Area
                            type="step" /* Step interpolation for digital look */
                            dataKey="websocket"
                            stroke="#3b82f6"
                            strokeWidth={1}
                            fillOpacity={1}
                            fill="url(#colorWebsocket)"
                            name="WS_STREAM"
                            animationDuration={0}
                            isAnimationActive={false} /* Instant updates */
                        />
                        <Area
                            type="step"
                            dataKey="tickets"
                            stroke="#ef4444"
                            strokeWidth={1}
                            fillOpacity={1}
                            fill="url(#colorTickets)"
                            name="INCIDENTS"
                            animationDuration={0}
                            isAnimationActive={false}
                        />
                        <Area
                            type="step"
                            dataKey="webhooks"
                            stroke="#f59e0b"
                            strokeWidth={1}
                            fillOpacity={1}
                            fill="url(#colorWebhooks)"
                            name="WEBHOOKS"
                            animationDuration={0}
                            isAnimationActive={false}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default VisitorChart;
