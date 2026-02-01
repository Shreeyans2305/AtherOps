# AtherOps Frontend Dashboard

A minimalist, real-time monitoring dashboard for the AtherOps self-healing e-commerce migration platform.

## Features

- **Real-time Monitoring**: WebSocket connection for live updates from the backend
- **System Metrics**: Total events, active observations, hypotheses, and action plans
- **Data Visualization**: Area charts showing system activity over time
- **Incident Management**: View and track all tickets and incidents
- **Multiple Views**: Dashboard, Incidents, Analytics, and Settings
- **Minimalist Design**: Clean, modern UI with subtle animations

## Getting Started

### Prerequisites

- Node.js 16+ installed
- Backend server running on `http://localhost:8000`

### Installation

```bash
cd Frontend
npm install
```

### Running the Application

```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

## Project Structure

```
Frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx          # Navigation sidebar
│   │   ├── MetricCard.jsx       # KPI metric cards
│   │   ├── VisitorChart.jsx     # Area chart component
│   │   ├── IncidentTable.jsx    # Incidents table
│   │   ├── StatusBadge.jsx      # Status badge component
│   │   └── TicketForm.jsx       # Ticket creation form (optional)
│   ├── services/
│   │   ├── api.js               # REST API service
│   │   └── websocket.js         # WebSocket service
│   ├── App.jsx                  # Main application
│   ├── App.css                  # App styles
│   └── index.css                # Design system & global styles
├── package.json
└── vite.config.js
```

## Backend Integration

The frontend connects to the AtherOps backend via:

### REST API Endpoints

- `GET /stats` - System statistics
- `GET /api/tickets` - All tickets
- `POST /api/tickets` - Create new ticket
- `PATCH /api/tickets/{id}/status` - Update ticket status

### WebSocket Events

- `ws://localhost:8000/ws/dashboard` - Real-time updates
- Events: `initial_state`, `new_event`, `new_ticket_incident`, `ticket_execution_result`

## Creating Tickets

To create a ticket programmatically, you can use the API service:

```javascript
import apiService from './services/api';

const ticketData = {
  title: "API Key Configuration Error",
  description: "Merchant API key is invalid or expired",
  merchant_id: "store_123",
  merchant_email: "merchant@example.com",
  priority: "high",
  category: "API"
};

const result = await apiService.createTicket(ticketData);
```

Or you can add the `TicketForm` component to the UI (already created in `components/TicketForm.jsx`).

## Design System

The application uses a comprehensive design system with:

- **Colors**: Minimalist palette with grays and blue accents
- **Typography**: 7 font sizes with proper weights
- **Spacing**: Consistent spacing scale (xs to 2xl)
- **Components**: Reusable, styled components
- **Animations**: Smooth transitions and hover effects

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
