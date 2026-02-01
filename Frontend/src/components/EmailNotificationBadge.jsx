import { Mail, CheckCircle } from 'lucide-react';
import './EmailNotificationBadge.css';

const EmailNotificationBadge = ({ emailData }) => {
    if (!emailData) return null;

    const { recipients = [], subject = '', email_result, timestamp } = emailData;
    const recipientCount = Array.isArray(recipients) ? recipients.length : 0;
    const isSuccess = email_result?.success !== false;

    // Determine recipient type
    const getRecipientType = () => {
        if (!recipients || recipients.length === 0) return 'Unknown';
        const firstRecipient = recipients[0];
        if (typeof firstRecipient === 'string') {
            if (firstRecipient.includes('@')) return 'Email';
            return 'Merchant';
        }
        return 'Recipients';
    };

    const recipientType = getRecipientType();

    return (
        <div className={`email-badge ${isSuccess ? 'email-success' : 'email-pending'}`}>
            <Mail size={14} />
            <span className="email-count">{recipientCount}</span>
            {isSuccess && <CheckCircle size={12} className="email-check" />}
            <div className="email-tooltip">
                <div className="tooltip-header">
                    <Mail size={16} />
                    <span>Email Notification</span>
                </div>
                <div className="tooltip-content">
                    <div className="tooltip-row">
                        <strong>Recipients:</strong> {recipientCount} {recipientType}
                    </div>
                    {subject && (
                        <div className="tooltip-row">
                            <strong>Subject:</strong> {subject}
                        </div>
                    )}
                    {timestamp && (
                        <div className="tooltip-row">
                            <strong>Sent:</strong> {new Date(timestamp).toLocaleString()}
                        </div>
                    )}
                    <div className="tooltip-row">
                        <strong>Status:</strong> {isSuccess ? 'Delivered' : 'Pending'}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EmailNotificationBadge;
