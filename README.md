<div align="center">
  
  # 🕒 SMART Timetable System🎓

  ### Transforming Academic Scheduling with Intelligent Automation

  ![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
  ![React](https://img.shields.io/badge/React-17+-61DAFB?style=for-the-badge&logo=react)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-009688?style=for-the-badge&logo=fastapi)
  ![MySQL](https://img.shields.io/badge/MySQL-8+-4479A1?style=for-the-badge&logo=mysql)

  **Revolutionize Your Academic Scheduling with Cutting-Edge Technology**
</div>

## 🌟 Project Overview

Timetable Scheduler Pro is an advanced, intelligent solution designed to streamline and optimize academic scheduling processes. By leveraging modern web technologies and intelligent algorithms, we transform the complex task of timetable management into a seamless, efficient experience.

## ✨ Key Features

- 🚀 **Intelligent Scheduling**
  - Automated timetable generation
  - Conflict-free class and resource allocation
  - Optimized room and faculty utilization

- 🔍 **Comprehensive Visualization**
  - Interactive timetable views
  - Detailed class, teacher, and venue schedules
  - Dark and light mode support

- 🔒 **Secure & Scalable**
  - Role-based access control
  - Robust authentication
  - Cloud-ready architecture

## 🛠 Tech Stack

### Backend
- **Language**: Python 3.9+
- **Framework**: FastAPI
- **Database**: MySQL 8+
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **Other**: `mysqlclient`, `pymysql`, `python-jose`, `python-dotenv`, `python-multipart`, `pandas`

### Frontend
- **Framework**: React
- **State Management**: React Hooks
- **Styling**: CSS Variables
- **HTTP Client**: Axios

### Deployment
- **Backend**: Uvicorn
- **Frontend**: Vite
- **Database**: MySQL (self-hosted or cloud-based)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 14+
- MySQL Server and SQL knowledge

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server 
uvicorn main:app --reload
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

### Environment Setup

#### Backend/Frontend `.env` Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```
   Or manually create a `.env` file in the project root.

2. **Edit `.env` with your actual credentials:**
   ```env
   # Database Configuration
   DB_HOST=your-db-host.example.com
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_NAME=your_database
   DB_PORT=12345
   DATABASE_URI=mysql://user:pass@host:port/db

   # Auth Configuration
   VITE_AUTH_USERNAME=admin
   VITE_AUTH_PASSWORD=changeme

   # API Configuration
   VITE_API_BASE_URL=http://localhost:8000/api
   REACT_APP_BACKEND_URL=http://localhost:8000/api
   ```

   - **DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT**: MySQL database connection details.
   - **DATABASE_URI**: Full SQLAlchemy/MySQL URI for DB access.
   - **VITE_AUTH_USERNAME, VITE_AUTH_PASSWORD**: Credentials for API authentication (if used).
   - **VITE_API_BASE_URL, REACT_APP_BACKEND_URL**: URLs for backend API access (used by frontend and backend).

> **Never commit your `.env` file to version control.**

### Database Requirements

- MySQL Server 8.0 or higher
- A database named as set in `DB_NAME`
- A `login_details` database with a `users` table:
  ```sql
  CREATE TABLE users (
      id INT PRIMARY KEY AUTO_INCREMENT,
      username VARCHAR(255) UNIQUE NOT NULL,
      password VARCHAR(255) NOT NULL
  );
  ```

### Running the Application

1. **Start the backend server** (if not already running):
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start the frontend development server**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**:
   - Open your browser and navigate to `http://localhost:3000` (or the port specified in your frontend `.env`)
