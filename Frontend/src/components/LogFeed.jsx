import React, { useEffect, useRef } from 'react';
import './LogFeed.css';

const LogFeed = ({ logs = [], className = '' }) => {
    const bottomRef = useRef(null);

    // Auto-scroll to bottom only if already near bottom or on initial load
    useEffect(() => {
        if (bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    const formatTime = (timestamp) => {
        if (!timestamp) return '00:00:00';
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
            });
        } catch (e) {
            return '00:00:00';
        }
    };

    const getLevel = (log) => {
        // Map backend severity/types to log levels
        const severity = log.severity?.toUpperCase() || 'INFO';
        const type = log.event_type?.toUpperCase() || 'UNKNOWN';

        if (severity === 'CRITICAL' || type === 'ERROR') return 'CRIT';
        if (severity === 'HIGH' || severity === 'WARNING') return 'WARN';
        if (severity === 'MEDIUM') return 'WARN';
        return 'INFO';
    };

    const getSeverityClass = (level) => {
        switch (level) {
            case 'CRIT': return 'severity-critical';
            case 'WARN': return 'severity-warning';
            default: return 'severity-info';
        }
    };

    return (
        <div className={`log-feed-container ${className}`}>
            <div className="log-feed-header">
                <span className="log-header-title">LOG FEED</span>
                <span className="log-header-counter">{logs.length} ENTRIES</span>
            </div>

            <div className="log-rows-container">
                {logs.length === 0 ? (
                    <div className="log-row">
                        <span className="col-message" style={{ color: '#475569' }}>
                            // System initialized. Waiting for stream...
                        </span>
                    </div>
                ) : (
                    logs.map((log, index) => {
                        const level = getLevel(log);
                        const severityClass = getSeverityClass(level);
                        const service = log.source || 'system';
                        const uniqueKey = log.event_id || log.id || `log-${index}`;

                        return (
                            <div key={uniqueKey} className={`log-row ${severityClass}`}>
                                <span className="col-timestamp">{formatTime(log.timestamp)}</span>
                                <span className="col-level">{level}</span>
                                <span className="col-service">[{service}]</span>
                                <span className="col-message">{log.message || 'No content'}</span>
                            </div>
                        );
                    })
                )}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default LogFeed;
