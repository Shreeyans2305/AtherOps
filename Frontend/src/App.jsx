import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import MetricCard from './components/MetricCard';
import VisitorChart from './components/VisitorChart';
import EventTimeline from './components/EventTimeline';
import AgentPipelineView from './components/AgentPipelineView';
import ObservationCard from './components/ObservationCard';
import ActionPlanCard from './components/ActionPlanCard';
import ThemeToggle from './components/ThemeToggle';
import apiService from './services/api';
import wsService from './services/websocket';
import useChartData from './hooks/useChartData';
import './App.css';
import './animations.css';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [observations, setObservations] = useState([]);
  const [hypotheses, setHypotheses] = useState([]);
  const [actionPlans, setActionPlans] = useState([]);
  const [executionResults, setExecutionResults] = useState({});
  const [emailNotifications, setEmailNotifications] = useState({});
  const [agentSteps, setAgentSteps] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  // Use custom hook for chart data
  const { chartData, addEvent } = useChartData(recentEvents);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch stats
        const statsData = await apiService.getStats();
        setStats(statsData);

        // Fetch recent events
        const eventsData = await apiService.getRecentEvents(24);
        setRecentEvents(eventsData.events || []);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Setup WebSocket connection
  useEffect(() => {
    wsService.connect();

    // Listen for initial state
    wsService.on('initial_state', (data) => {
      console.log('Received initial state:', data);
      setIsConnected(true);
      if (data.observations) setObservations(data.observations);
      if (data.hypotheses) setHypotheses(Object.values(data.hypotheses));
      if (data.plans) setActionPlans(Object.values(data.plans));
    });

    // Listen for new events
    wsService.on('new_event', (data) => {
      console.log('New event:', data);
      const newEvent = data.event;
      setRecentEvents(prev => [newEvent, ...prev].slice(0, 200)); // Keep last 200
      addEvent(newEvent); // Update chart
      apiService.getStats().then(setStats);
    });

    // Listen for agent steps
    wsService.on('agent_step', (data) => {
      console.log('Agent step:', data);
      setAgentSteps(prev => [...prev, data].slice(-20));
    });

    // Listen for observations
    wsService.on('observation_created', (data) => {
      console.log('Observation created:', data);
      setObservations(prev => [data.observation, ...prev].slice(0, 50));
    });

    // Listen for hypotheses
    wsService.on('hypothesis_generated', (data) => {
      console.log('Hypothesis generated:', data);
      setHypotheses(prev => [data.hypothesis, ...prev].slice(0, 50));
    });

    // Listen for action plans
    wsService.on('action_planned', (data) => {
      console.log('Action planned:', data);
      setActionPlans(prev => [data.plan, ...prev].slice(0, 50));
    });

    // Listen for executions
    wsService.on('action_executed', (data) => {
      console.log('Action executed:', data);
      setExecutionResults(prev => ({
        ...prev,
        [data.plan_id]: data.result
      }));
    });

    // Listen for email notifications
    wsService.on('email_sent', (data) => {
      console.log('Email sent:', data);
      setEmailNotifications(prev => ({
        ...prev,
        [data.plan_id]: data
      }));
    });

    // Cleanup
    return () => {
      wsService.disconnect();
    };
  }, [addEvent]);

  // Calculate metrics from stats
  const getMetrics = () => {
    if (!stats) {
      return {
        totalEvents: '0',
        activeObservations: '0',
        hypotheses: '0',
        actionPlans: '0',
      };
    }

    return {
      totalEvents: stats.total_events?.toLocaleString() || '0',
      activeObservations: stats.active_observations?.toLocaleString() || '0',
      hypotheses: stats.hypotheses?.toLocaleString() || '0',
      actionPlans: stats.action_plans?.toLocaleString() || '0',
    };
  };

  const metrics = getMetrics();

  if (loading) {
    return (
      <div className="app">
        <Sidebar activeView={activeView} onViewChange={setActiveView} />
        <main className="main-content">
          <div className="loading-state">
            <div className="loading-spinner spin"></div>
            <p>Loading AtherOps Dashboard...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />

      <main className="main-content">
        {activeView === 'dashboard' && (
          <div className="dashboard-layout">
            {/* Fixed Header with Metrics */}
            <div className="dashboard-header fade-in">
              <div className="header-content">
                <div>
                  <h1 className="dashboard-title">AtherOps Dashboard</h1>
                  <p className="dashboard-subtitle">Multi-Agent Healing System</p>
                </div>
                <ThemeToggle />
              </div>

              {/* Metrics Grid */}
              <div className="metrics-grid stagger-children">
                <MetricCard
                  title="Total Events"
                  value={metrics.totalEvents}
                  trend="+12%"
                  trendDirection="up"
                  subtitle="Signals received"
                />
                <MetricCard
                  title="Active Observations"
                  value={metrics.activeObservations}
                  trend="+8%"
                  trendDirection="up"
                  subtitle="Patterns detected"
                />
                <MetricCard
                  title="Hypotheses"
                  value={metrics.hypotheses}
                  trend="+5%"
                  trendDirection="up"
                  subtitle="Root causes identified"
                />
                <MetricCard
                  title="Action Plans"
                  value={metrics.actionPlans}
                  trend="+3%"
                  trendDirection="up"
                  subtitle="Actions planned"
                />
              </div>
            </div>

            {/* Agent Pipeline - Compact */}
            <div className="pipeline-section slide-in-top">
              <AgentPipelineView agentSteps={agentSteps} />
            </div>

            {/* Main Content Grid - Fixed Height */}
            <div className="content-grid">
              {/* Left: Event Timeline */}
              <div className="timeline-panel slide-in-left">
                <EventTimeline events={recentEvents.slice(0, 100)} />
              </div>

              {/* Right: Split into Chart and Activity */}
              <div className="main-panel slide-in-right">
                {/* Top: Live Chart */}
                <div className="chart-panel">
                  <VisitorChart data={chartData} />
                </div>

                {/* Bottom: Recent Activity */}
                <div className="activity-panel">
                  <h3 className="panel-title">Recent Activity</h3>
                  <div className="activity-scroll">
                    {observations.slice(0, 3).map((obs, idx) => (
                      <div key={obs.observation_id || idx} className="fade-in">
                        <ObservationCard observation={obs} />
                      </div>
                    ))}

                    {actionPlans.slice(0, 3).map((plan, idx) => (
                      <div key={plan.plan_id || idx} className="fade-in">
                        <ActionPlanCard
                          plan={plan}
                          executionResult={executionResults[plan.plan_id]}
                          emailData={emailNotifications[plan.plan_id]}
                        />
                      </div>
                    ))}

                    {observations.length === 0 && actionPlans.length === 0 && (
                      <div className="empty-state">
                        <p>No recent activity</p>
                        <span>Agent activity will appear here</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'incidents' && (
          <div className="page-layout">
            <div className="page-header fade-in">
              <div>
                <h1 className="dashboard-title">Incidents & Observations</h1>
                <p className="dashboard-subtitle">All detected patterns and issues</p>
              </div>
              <ThemeToggle />
            </div>

            <div className="page-content">
              {observations.map((obs, idx) => (
                <div key={obs.observation_id || idx} className="fade-in">
                  <ObservationCard observation={obs} />
                </div>
              ))}

              {observations.length === 0 && (
                <div className="empty-state">
                  <p>No observations yet</p>
                  <span>Observations will appear here as patterns are detected</span>
                </div>
              )}
            </div>
          </div>
        )}

        {activeView === 'analytics' && (
          <div className="page-layout">
            <div className="page-header fade-in">
              <div>
                <h1 className="dashboard-title">Analytics</h1>
                <p className="dashboard-subtitle">System performance and trends</p>
              </div>
              <ThemeToggle />
            </div>

            <div className="page-content">
              <div className="chart-full-width slide-in-top">
                <VisitorChart data={chartData} />
              </div>

              <div className="metrics-grid stagger-children">
                <MetricCard
                  title="Total Events"
                  value={metrics.totalEvents}
                  trend="+12%"
                  trendDirection="up"
                  subtitle="Last 24 hours"
                />
                <MetricCard
                  title="Patterns Detected"
                  value={metrics.activeObservations}
                  trend="+8%"
                  trendDirection="up"
                  subtitle="Active observations"
                />
                <MetricCard
                  title="Actions Taken"
                  value={metrics.actionPlans}
                  trend="+3%"
                  trendDirection="up"
                  subtitle="Automated fixes"
                />
              </div>
            </div>
          </div>
        )}

        {activeView === 'settings' && (
          <div className="page-layout">
            <div className="page-header fade-in">
              <div>
                <h1 className="dashboard-title">Settings</h1>
                <p className="dashboard-subtitle">Configure AtherOps</p>
              </div>
              <ThemeToggle />
            </div>

            <div className="page-content">
              <div className="settings-placeholder">
                <p>Settings panel coming soon...</p>
              </div>
            </div>
          </div>
        )}
      </main>

      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        <span className="status-dot"></span>
        {isConnected ? 'Connected' : 'Connecting...'}
      </div>
    </div>
  );
}

export default App;
