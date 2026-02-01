import './ConfidenceIndicator.css';

const ConfidenceIndicator = ({ confidence, showPercentage = true }) => {
    const percentage = Math.round(confidence * 100);

    // Determine color based on confidence level
    const getColor = () => {
        if (percentage >= 75) return 'high';
        if (percentage >= 50) return 'medium';
        return 'low';
    };

    const colorClass = getColor();

    return (
        <div className="confidence-indicator">
            <div className="confidence-bar-container">
                <div
                    className={`confidence-bar confidence-${colorClass}`}
                    style={{ width: `${percentage}%` }}
                >
                    {showPercentage && <span className="confidence-text">{percentage}%</span>}
                </div>
            </div>
            {!showPercentage && <span className="confidence-label">{percentage}%</span>}
        </div>
    );
};

export default ConfidenceIndicator;
