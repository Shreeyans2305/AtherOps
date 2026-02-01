import { TrendingUp, TrendingDown } from 'lucide-react';
import './MetricCard.css';

const MetricCard = ({ title, value, trend, trendDirection, subtitle, icon: Icon }) => {
    // If trendDirection is provided ('up'/'down'), use it. Fallback to trend value parsing.
    const isPositive = trendDirection ? trendDirection === 'up' : (trend && !trend.startsWith('-'));
    const TrendIcon = isPositive ? TrendingUp : TrendingDown;

    return (
        <div className="metric-card">
            <div className="metric-header">
                <span className="metric-title">{title}</span>
                {Icon && <Icon size={14} className="metric-icon" />}
            </div>

            <div className="metric-value">{value}</div>

            <div className="metric-footer">
                <div className={`metric-trend ${isPositive ? 'positive' : 'negative'}`}>
                    <TrendIcon size={12} />
                    <span>{trend}</span> {/* Display the trend string e.g. "+12%" */}
                </div>
                <span className="metric-subtitle">{subtitle}</span>
            </div>
        </div>
    );
};

export default MetricCard;
