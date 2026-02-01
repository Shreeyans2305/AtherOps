import { Shield, AlertTriangle } from 'lucide-react';
import './RiskLevelBadge.css';

const RiskLevelBadge = ({ riskLevel }) => {
    const getRiskConfig = () => {
        switch (riskLevel?.toLowerCase()) {
            case 'low':
                return { icon: Shield, label: 'Low Risk', className: 'risk-low' };
            case 'medium':
                return { icon: AlertTriangle, label: 'Medium Risk', className: 'risk-medium' };
            case 'high':
                return { icon: AlertTriangle, label: 'High Risk', className: 'risk-high' };
            default:
                return { icon: Shield, label: 'Unknown', className: 'risk-unknown' };
        }
    };

    const config = getRiskConfig();
    const Icon = config.icon;

    return (
        <div className={`risk-badge ${config.className}`} title={`Risk Level: ${config.label}`}>
            <Icon size={14} />
            <span>{config.label}</span>
        </div>
    );
};

export default RiskLevelBadge;
