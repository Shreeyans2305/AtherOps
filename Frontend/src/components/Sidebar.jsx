import { Activity, BarChart3, Home, Settings } from 'lucide-react';
import { UserButton, OrganizationSwitcher } from '@clerk/clerk-react';
import './Sidebar.css';

const Sidebar = ({ activeView, onViewChange, user, organization }) => {
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
                    <img src="/logo.png" alt="AtherOps" className="sidebar-logo-img" />
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
                <div className="org-switcher">
                    <OrganizationSwitcher
                        appearance={{
                            elements: {
                                rootBox: 'org-switcher-root',
                                organizationSwitcherTrigger: 'org-switcher-trigger'
                            }
                        }}
                    />
                </div>
                <div className="user-button-wrapper">
                    <UserButton
                        appearance={{
                            elements: {
                                rootBox: 'user-button-root',
                                userButtonAvatarBox: 'user-avatar-box'
                            }
                        }}
                        showName={true}
                    />
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;

