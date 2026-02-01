import { Eye, Users, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import StatusBadge from './StatusBadge';
import ConfidenceIndicator from './ConfidenceIndicator';
import './ObservationCard.css';

const ObservationCard = ({ observation }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="observation-card">
            <div className="observation-header">
                <div className="observation-title-row">
                    <Eye size={18} />
                    <h4>Observation</h4>
                    <StatusBadge status={observation.severity} />
                </div>

                <button
                    className="expand-button"
                    onClick={() => setIsExpanded(!isExpanded)}
                    aria-label={isExpanded ? "Collapse" : "Expand"}
                >
                    {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
            </div>

            <div className="observation-body">
                <p className="observation-description">{observation.description}</p>

                <div className="observation-stats">
                    <div className="stat-item">
                        <AlertCircle size={14} />
                        <span>{observation.event_count} events</span>
                    </div>
                    <div className="stat-item">
                        <Users size={14} />
                        <span>{observation.affected_merchants?.length || 0} merchants</span>
                    </div>
                </div>

                <div className="observation-confidence">
                    <span className="confidence-label-text">Confidence</span>
                    <ConfidenceIndicator confidence={observation.confidence || 0.5} />
                </div>

                {isExpanded && (
                    <div className="observation-details">
                        <div className="detail-section">
                            <strong>Pattern Key:</strong>
                            <code>{observation.pattern_key}</code>
                        </div>

                        <div className="detail-section">
                            <strong>Timeline:</strong>
                            <div className="timeline-info">
                                <span>First seen: {formatTimestamp(observation.first_seen)}</span>
                                <span>Last seen: {formatTimestamp(observation.last_seen)}</span>
                            </div>
                        </div>

                        {observation.affected_merchants && observation.affected_merchants.length > 0 && (
                            <div className="detail-section">
                                <strong>Affected Merchants:</strong>
                                <div className="merchant-list">
                                    {observation.affected_merchants.slice(0, 5).map((merchant, idx) => (
                                        <span key={idx} className="merchant-tag">{merchant}</span>
                                    ))}
                                    {observation.affected_merchants.length > 5 && (
                                        <span className="merchant-tag">+{observation.affected_merchants.length - 5} more</span>
                                    )}
                                </div>
                            </div>
                        )}

                        {observation.events && observation.events.length > 0 && (
                            <div className="detail-section">
                                <strong>Sample Events:</strong>
                                <div className="event-samples">
                                    {observation.events.slice(0, 3).map((event, idx) => (
                                        <div key={idx} className="event-sample">
                                            <span className="event-type">{event.event_type}</span>
                                            <span className="event-message">{event.message?.substring(0, 80)}...</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ObservationCard;
