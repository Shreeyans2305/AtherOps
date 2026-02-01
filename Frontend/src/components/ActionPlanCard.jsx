import { Scale, Mail, Code, AlertTriangle, FileText, MessageSquare, CheckCircle, Clock, XCircle } from 'lucide-react';
import { useState } from 'react';
import StatusBadge from './StatusBadge';
import RiskLevelBadge from './RiskLevelBadge';
import EmailNotificationBadge from './EmailNotificationBadge';
import './ActionPlanCard.css';

const ActionPlanCard = ({ plan, executionResult, emailData }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const getActionIcon = (actionType) => {
        switch (actionType) {
            case 'merchant_communication':
                return Mail;
            case 'engineering_escalation':
                return AlertTriangle;
            case 'support_guidance':
                return MessageSquare;
            case 'documentation_update':
                return FileText;
            default:
                return Code;
        }
    };

    const getActionLabel = (actionType) => {
        return actionType?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown Action';
    };

    const getExecutionStatus = () => {
        if (!executionResult) {
            return plan.requires_approval ? 'pending_approval' : 'pending';
        }
        return executionResult.status;
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'success':
                return <CheckCircle size={16} className="status-success" />;
            case 'pending_approval':
                return <Clock size={16} className="status-pending" />;
            case 'failed':
                return <XCircle size={16} className="status-error" />;
            default:
                return <Clock size={16} className="status-pending" />;
        }
    };

    const ActionIcon = getActionIcon(plan.action_type);
    const executionStatus = getExecutionStatus();

    return (
        <div className={`action-plan-card ${executionStatus}`}>
            <div className="action-header">
                <div className="action-title-row">
                    <div className="action-icon">
                        <ActionIcon size={18} />
                    </div>
                    <div className="action-title-info">
                        <h4>{getActionLabel(plan.action_type)}</h4>
                        <div className="action-badges">
                            <StatusBadge status={plan.priority} />
                            <RiskLevelBadge riskLevel={plan.risk_level} />
                            {emailData && <EmailNotificationBadge emailData={emailData} />}
                        </div>
                    </div>
                </div>

                <div className="action-status">
                    {getStatusIcon(executionStatus)}
                </div>
            </div>

            <div className="action-body">
                {plan.requires_approval && !executionResult && (
                    <div className="approval-notice">
                        <AlertTriangle size={16} />
                        <span>Requires human approval before execution</span>
                    </div>
                )}

                {plan.estimated_impact && (
                    <p className="action-impact">{plan.estimated_impact}</p>
                )}

                {plan.action_details && (
                    <div className="action-details-preview">
                        {plan.action_details.subject && (
                            <div className="detail-item">
                                <strong>Subject:</strong> {plan.action_details.subject}
                            </div>
                        )}
                        {plan.action_details.title && (
                            <div className="detail-item">
                                <strong>Title:</strong> {plan.action_details.title}
                            </div>
                        )}
                        {plan.action_details.recipients && (
                            <div className="detail-item">
                                <strong>Recipients:</strong> {plan.action_details.recipients.length} merchant(s)
                            </div>
                        )}
                        {plan.action_details.affected_count !== undefined && (
                            <div className="detail-item">
                                <strong>Affected:</strong> {plan.action_details.affected_count} merchant(s)
                            </div>
                        )}
                    </div>
                )}

                {executionResult && (
                    <div className="execution-result">
                        <div className="result-header">
                            <strong>Execution Result</strong>
                            <span className={`result-status ${executionResult.status}`}>
                                {executionResult.status}
                            </span>
                        </div>

                        {executionResult.result_details && (
                            <div className="result-details">
                                {executionResult.result_details.emails_sent > 0 && (
                                    <div className="result-item">
                                        ✓ Sent {executionResult.result_details.emails_sent} email(s)
                                    </div>
                                )}
                                {executionResult.result_details.ticket_id && (
                                    <div className="result-item">
                                        ✓ Created ticket: {executionResult.result_details.ticket_id}
                                    </div>
                                )}
                                {executionResult.result_details.message && (
                                    <div className="result-item">
                                        {executionResult.result_details.message}
                                    </div>
                                )}
                            </div>
                        )}

                        {executionResult.error && (
                            <div className="result-error">
                                <AlertTriangle size={14} />
                                <span>{executionResult.error}</span>
                            </div>
                        )}
                    </div>
                )}

                {isExpanded && plan.action_details && (
                    <div className="action-full-details">
                        <pre>{JSON.stringify(plan.action_details, null, 2)}</pre>
                    </div>
                )}

                <button
                    className="toggle-details-button"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    {isExpanded ? 'Hide Details' : 'Show Full Details'}
                </button>
            </div>
        </div>
    );
};

export default ActionPlanCard;
