import { useState } from 'react';
import { X } from 'lucide-react';
import './TicketForm.css';

const TicketForm = ({ onClose, onSubmit }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        merchant_id: '',
        merchant_email: '',
        priority: 'medium',
        category: '',
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Create New Ticket</h2>
                    <button className="close-button" onClick={onClose}>
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="ticket-form">
                    <div className="form-group">
                        <label htmlFor="title">Title *</label>
                        <input
                            type="text"
                            id="title"
                            name="title"
                            value={formData.title}
                            onChange={handleChange}
                            required
                            placeholder="Brief description of the issue"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="description">Description *</label>
                        <textarea
                            id="description"
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            required
                            rows="4"
                            placeholder="Detailed description of the issue"
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="merchant_id">Merchant ID *</label>
                            <input
                                type="text"
                                id="merchant_id"
                                name="merchant_id"
                                value={formData.merchant_id}
                                onChange={handleChange}
                                required
                                placeholder="e.g., store_123"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="merchant_email">Merchant Email</label>
                            <input
                                type="email"
                                id="merchant_email"
                                name="merchant_email"
                                value={formData.merchant_email}
                                onChange={handleChange}
                                placeholder="merchant@example.com"
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="priority">Priority *</label>
                            <select
                                id="priority"
                                name="priority"
                                value={formData.priority}
                                onChange={handleChange}
                                required
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="category">Category</label>
                            <input
                                type="text"
                                id="category"
                                name="category"
                                value={formData.category}
                                onChange={handleChange}
                                placeholder="e.g., API, Payment, Checkout"
                            />
                        </div>
                    </div>

                    <div className="form-actions">
                        <button type="button" className="btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="btn-primary">
                            Create Ticket
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TicketForm;
