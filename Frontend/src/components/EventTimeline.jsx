import { useEffect, useRef } from 'react';
import { Clock, AlertCircle, Zap, Ticket } from 'lucide-react';
import StatusBadge from './StatusBadge';
import './EventTimeline.css';

const EventTimeline = ({ events = [] }) => {
    const timelineRef = useRef(null);
    const prevEventsLength = useRef(events.length);

    // Auto-scroll to latest event when new events arrive
    useEffect(() => {
        if (events.length > prevEventsLength.current && timelineRef.current) {
            timelineRef.current.scrollTop = 0; // Scroll to top (newest)
        }
        prevEventsLength.current = events.length;
    }, [events]);

    const getEventIcon = (eventType) => {
        switch (eventType) {
            case 'ticket':
                return Ticket;
            case 'api_error':
            case 'api_call':
                return AlertCircle;
            case 'javascript_error':
                return AlertCircle;
            case 'performance':
                return Zap;
            default:
                return Clock;
        }
    };

    const formatTimestamp = (timestamp) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        // Less than 1 minute
        if (diff < 60000) {
            return 'Just now';
        }
        // Less than 1 hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }
        // Less than 24 hours
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }
        // More than 24 hours
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatEventMessage = (event) => {
        if (event.message) {
            return event.message.length > 100
                ? event.message.substring(0, 100) + '...'
                : event.message;
        }
        return `${event.event_type} event`;
    };

    if (events.length === 0) {
        return (
            <div className="event-timeline">
                <div className="timeline-header">
                    <Clock size={18} />
                    <h3>Event Timeline</h3>
                    <span className="event-count">0</span>
                </div>
                <div className="timeline-empty">
                    <Clock size={32} />
                    <p>No events yet</p>
                    <span>Events will appear here as they occur</span>
                </div>
            </div>
        );
    }

    return (
        <div className="event-timeline">
            <div className="timeline-header">
                <Clock size={18} />
                <h3>Event Timeline</h3>
                <span className="event-count">{events?.length || 0}</span>
            </div>

            <div className="timeline-content" ref={timelineRef}>
                {events?.map((event, index) => {
                    const Icon = getEventIcon(event.event_type || 'unknown');
                    const eventId = event.event_id || event.id || `evt-${index}-${Date.now()}`;

                    return (
                        <div key={eventId} className="timeline-item">
                            <div className="timeline-icon">
                                <Icon size={16} />
                            </div>

                            <div className="timeline-details">
                                <div className="timeline-header-row">
                                    <StatusBadge status={event.severity || 'low'} />
                                    <span className="timeline-time">
                                        {event.timestamp ? formatTimestamp(event.timestamp) : 'Just now'}
                                    </span>
                                </div>

                                <div className="timeline-message">
                                    {formatEventMessage(event)}
                                </div>

                                <div className="timeline-meta">
                                    <span className="timeline-type">{event.event_type || 'event'}</span>
                                    {event.merchant_id && (
                                        <>
                                            <span className="timeline-separator">•</span>
                                            <span className="timeline-merchant">{event.merchant_id}</span>
                                        </>
                                    )}
                                    {event.source && (
                                        <>
                                            <span className="timeline-separator">•</span>
                                            <span className="timeline-source">{event.source}</span>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default EventTimeline;
