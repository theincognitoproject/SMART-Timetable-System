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
