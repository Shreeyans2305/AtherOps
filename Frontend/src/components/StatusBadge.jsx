import './StatusBadge.css';

const StatusBadge = ({ status, type = 'default' }) => {
    const getStatusClass = () => {
        const statusLower = status?.toLowerCase() || '';

        // Priority-based
        if (statusLower.includes('critical')) return 'critical';
        if (statusLower.includes('high')) return 'high';
        if (statusLower.includes('medium')) return 'medium';
        if (statusLower.includes('low')) return 'low';

        // Status-based
        if (statusLower.includes('open')) return 'open';
        if (statusLower.includes('progress')) return 'progress';
        if (statusLower.includes('resolved') || statusLower.includes('success')) return 'success';
        if (statusLower.includes('closed')) return 'closed';
        if (statusLower.includes('failed') || statusLower.includes('error')) return 'error';

        return 'default';
    };

    return (
        <span className={`status-badge ${getStatusClass()}`}>
            {status}
        </span>
    );
};

export default StatusBadge;
