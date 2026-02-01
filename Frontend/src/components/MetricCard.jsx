import { TrendingUp, TrendingDown } from 'lucide-react';
import './MetricCard.css';

const MetricCard = ({ title, value, trend, trendValue, subtitle, icon: Icon }) => {
    const isPositive = trend === 'up';
    const TrendIcon = isPositive ? TrendingUp : TrendingDown;

    return (
        <div className="metric-card">
            <div className="metric-header">
                <span className="metric-title">{title}</span>
                {Icon && <Icon size={16} className="metric-icon" />}
            </div>

            <div className="metric-value">{value}</div>

            <div className="metric-footer">
                <div className={`metric-trend ${isPositive ? 'positive' : 'negative'}`}>
                    <TrendIcon size={14} />
                    <span>{trendValue}</span>
                </div>
                <span className="metric-subtitle">{subtitle}</span>
            </div>
        </div>
    );
};

export default MetricCard;
