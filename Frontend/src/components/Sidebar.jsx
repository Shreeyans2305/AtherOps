import { Activity, BarChart3, Home, Settings } from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ activeView, onViewChange }) => {
    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: Home },
        { id: 'incidents', label: 'Incidents', icon: Activity },
        { id: 'analytics', label: 'Analytics', icon: BarChart3 },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <div className="logo-icon">⚡</div>
                    <span className="logo-text">AtherOps</span>
                </div>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <button
                            key={item.id}
                            className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                            onClick={() => onViewChange(item.id)}
                        >
                            <Icon size={18} />
                            <span>{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">A</div>
                    <div className="user-details">
                        <div className="user-name">Admin</div>
                        <div className="user-email">admin@atherops.com</div>
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
