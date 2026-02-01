import { Eye, Brain, Scale, Play, CheckCircle, Clock, XCircle } from 'lucide-react';
import './AgentPipelineView.css';

const AgentPipelineView = ({ agentSteps = [] }) => {
    const agents = [
        { id: 'observer', name: 'Observer', icon: Eye, description: 'Detects patterns' },
        { id: 'reasoner', name: 'Reasoner', icon: Brain, description: 'Diagnoses issues' },
        { id: 'decision', name: 'Decision', icon: Scale, description: 'Plans actions' },
        { id: 'executor', name: 'Executor', icon: Play, description: 'Executes fixes' }
    ];

    // Get the latest status for each agent
    const getAgentStatus = (agentId) => {
        const agentStepsFiltered = agentSteps.filter(step => step.agent === agentId);
        if (agentStepsFiltered.length === 0) return { status: 'idle', result: null };

        const latestStep = agentStepsFiltered[agentStepsFiltered.length - 1];
        return {
            status: latestStep.status,
            result: latestStep.result,
            timestamp: latestStep.timestamp,
            ...latestStep
        };
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'running':
                return <div className="status-spinner" />;
            case 'completed':
                return <CheckCircle size={16} className="status-icon-success" />;
            case 'pending_approval':
                return <Clock size={16} className="status-icon-pending" />;
            case 'failed':
                return <XCircle size={16} className="status-icon-error" />;
            default:
                return null;
        }
    };

    const getStatusClass = (status) => {
        switch (status) {
            case 'running':
                return 'agent-running';
            case 'completed':
                return 'agent-completed';
            case 'pending_approval':
                return 'agent-pending';
            case 'failed':
                return 'agent-error';
            default:
                return 'agent-idle';
        }
    };

    return (
        <div className="agent-pipeline">
            <div className="pipeline-header">
                <h3>Agent Pipeline</h3>
                <span className="pipeline-subtitle">Multi-Agent Healing System</span>
            </div>

            <div className="pipeline-flow">
                {agents.map((agent, index) => {
                    const Icon = agent.icon;
                    const agentStatus = getAgentStatus(agent.id);
                    const statusClass = getStatusClass(agentStatus.status);

                    return (
                        <div key={agent.id} className="pipeline-stage">
                            <div className={`agent-card ${statusClass}`}>
                                <div className="agent-icon-container">
                                    <Icon size={24} />
                                    {getStatusIcon(agentStatus.status)}
                                </div>

                                <div className="agent-info">
                                    <h4>{agent.name}</h4>
                                    <p className="agent-description">{agent.description}</p>

                                    {agentStatus.result && (
                                        <div className="agent-result">
                                            {typeof agentStatus.result === 'string'
                                                ? agentStatus.result
                                                : JSON.stringify(agentStatus.result)}
                                        </div>
                                    )}

                                    {agentStatus.confidence !== undefined && (
                                        <div className="agent-meta">
                                            Confidence: {Math.round(agentStatus.confidence * 100)}%
                                        </div>
                                    )}

                                    {agentStatus.observations_count && (
                                        <div className="agent-meta">
                                            {agentStatus.observations_count} patterns detected
                                        </div>
                                    )}

                                    {agentStatus.priority && (
                                        <div className="agent-meta">
                                            Priority: {agentStatus.priority}
                                        </div>
                                    )}

                                    {agentStatus.risk_level && (
                                        <div className="agent-meta">
                                            Risk: {agentStatus.risk_level}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {index < agents.length - 1 && (
                                <div className="pipeline-arrow">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                                        <path d="M5 12h14m-6-6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default AgentPipelineView;
