import StatusBadge from './StatusBadge';
import './IncidentTable.css';

const IncidentTable = ({ incidents }) => {
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="incident-table-container">
            <div className="table-header">
                <h3 className="table-title">Recent Incidents</h3>
                <span className="table-count">{incidents.length} total</span>
            </div>

            <div className="table-wrapper">
                <table className="incident-table">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Type</th>
                            <th>Status</th>
                            <th>Priority</th>
                            <th>Merchant</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody>
                        {incidents.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="empty-state">
                                    No incidents to display
                                </td>
                            </tr>
                        ) : (
                            incidents.map((incident) => (
                                <tr key={incident.id} className="table-row">
                                    <td className="title-cell">{incident.title}</td>
                                    <td>{incident.category || incident.type || 'General'}</td>
                                    <td>
                                        <StatusBadge status={incident.status} />
                                    </td>
                                    <td>
                                        <StatusBadge status={incident.priority} />
                                    </td>
                                    <td className="merchant-cell">{incident.merchant_id}</td>
                                    <td className="date-cell">{formatDate(incident.created_at)}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default IncidentTable;
