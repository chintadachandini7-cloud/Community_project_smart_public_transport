# Smart Public Transport Tracking & Management System

A community-focused smart public transport tracking and management application designed for real-time fleet monitoring, route management, passenger notifications, and multi-role dashboards (Passenger, Conductor, Driver, and Admin).

## 🚍 Key Features

- **Passenger Live Dashboard**: Real-time interactive map with bus tracking, live route and stop visualization, ETA calculations, delay indicators, and filtering by operator (APSRTC, TGSRTC), area, and service type.
- **Driver Dashboard**: Route guidance, trip status updates, delay reporting, and passenger counts.
- **Conductor Dashboard**: Live ticketing/occupancy updates, stop announcements, and passenger alerts.
- **Admin Control Center**: Fleet and route management, driver/conductor assignments, data import/export, and system telemetry.
- **Interactive Maps**: Powered by Leaflet and OpenStreetMap for accurate geo-positioning of buses and transit stops.
- **RESTful API**: Comprehensive backend API endpoints for live telemetry, trip history, schedules, and route coordination.

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, SQLite3
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Leaflet.js
- **Optional Web App**: React + Vite (located in `frontend/`)

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js & npm (optional, for React frontend)

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/chintadachandini2408-lang/Community_project_smart_public_transport.git
   cd Community_project_smart_public_transport
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database & Run Application**:
   ```bash
   python app.py
   ```
   The Flask application will start on `http://127.0.0.1:5000`.

### Dashboards & Navigation
- **Passenger Dashboard**: `http://localhost:5000/`
- **Admin Dashboard**: `http://localhost:5000/admin`
- **Driver Login**: `http://localhost:5000/driver_login`
- **Conductor Login**: `http://localhost:5000/conductor_login`

---
*Developed for the Community Smart Public Transport initiative.*
