# 🚀 Smart Volunteer Allocation System
> **Connecting Needs with Expertise—Intelligently and Instantly.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Framework-Django-092E20.svg)](https://www.djangoproject.com/)
[![Status](https://img.shields.io/badge/Status-In--Development-orange.svg)]()
[![License](https://img.shields.io/badge/License-Educational-green.svg)]()

---

## 📌 Overview

### The Problem
Traditional volunteer management is often plagued by manual delays, inefficient communication, and "mismatched" assignments. During critical situations, time spent searching for the right person is time lost for the person in need.

### The Solution
The **Smart Volunteer Allocation System** is an automated, web-based platform that acts as a bridge between help-seekers and volunteers. By utilizing a **Rule-Based Matching Engine**, the system analyzes requests in real-time to assign the most qualified and closest volunteer available, ensuring help is both relevant and rapid.

---

## ✨ Features

* 🧠 **Smart Matching Engine:** Automated rule-based logic that evaluates suitability in seconds.
* 📍 **Multi-Level Matching:** A cascading search logic: **Local (Neighborhood) → City → Global**.
* ⚡ **Urgency-Based Scoring:** High-priority requests are pushed to the top of the processing queue.
* 👥 **Live Availability Tracking:** Volunteers can toggle their status to prevent burnout and over-assignment.
* 🏢 **Future-Ready Architecture:** Built with a modular Django structure, ready for AI integration and REST APIs.

---

## 🧠 Matching Algorithm (Core Logic)

The heart of the system is a dynamic scoring mechanism. When a request is created, the system scans the database and calculates a **Suitability Score** for potential volunteers based on:

### 1. The Scoring Matrix
| Factor | Criteria | Points Awarded |
| :--- | :--- | :--- |
| **Urgency** | High / Medium / Low | 50 / 30 / 10 |
| **Skill Match** | Keyword match in profile | +20 per match |
| **Location Boost** | Matching District/City | +30 (Bonus) |

### 2. Decision Flow
1.  **Phase 1 (Local):** Search for volunteers within the immediate proximity.
2.  **Phase 2 (City):** If no score exceeds the threshold, expand to the entire city.
3.  **Phase 3 (Global):** Fallback to the wider network for remote or highly specialized assistance.

*The volunteer with the highest aggregate score is automatically selected and assigned.*

---

## 🛠️ Tech Stack

### Backend & Database
* **Python:** Core programming language.
* **Django:** High-level web framework for rapid, secure development.
* **SQLite:** Lightweight relational database (Development environment).

### Frontend
* **HTML5 & CSS3:** Semantic structure and custom styling.
* **Bootstrap 5:** For a responsive, mobile-first user interface.

### Tools & Platforms
* **Git & GitHub:** Version control and collaboration.
* **VS Code:** Primary Integrated Development Environment (IDE).

---

## 📂 Project Structure

```text
smart_allocation_system/
│
├── core/                       # Main Project Configuration
│   ├── settings.py             # Global project settings
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py                 # Deployment entry point
│
├── allocation/                 # Application Logic
│   ├── migrations/             # Database migration history
│   ├── templates/              # UI Components (HTML)
│   │   ├── create_request.html
│   │   ├── success.html
│   │   └── dashboard.html
│   ├── admin.py                # Admin panel setup
│   ├── models.py               # Volunteer & Request Schemas
│   ├── views.py                # Matching Logic & Engines
│   ├── forms.py                # User input validation
│   └── urls.py                 # App-specific routes
│
├── manage.py                   # Django CLI tool
├── db.sqlite3                  # Local database
└── README.md                   # Documentation
```
---

## 🚀 Getting Started
---
### 1. Clone the Repository
```text
Bash
git clone [https://github.com/your-username/smart-allocation-system.git](https://github.com/your-username/smart-allocation-system.git)
cd smart-allocation-system
```
---
### 2. Set Up Virtual Environment
---
```text
Bash
python -m venv venv

#Windows 
venv\Scripts\activate

#Mac/Linux
source venv/bin/activate
```
---
### 3. Install Dependencies
---
```text
Bash
pip install django
```
---
### 4. Run Migrations & Start Server
---
```text
Bash
python manage.py migrate
python manage.py runserver
```
---
Visit http://127.0.0.1:8000/ in your browser.


## 📊 Future Enhancements
[ ] AI/ML Matching: Implementing TF-IDF or Word Embeddings for semantic skill matching.

[ ] Advanced Dashboard: Real-time data visualization for admin monitoring.

[ ] Notification System: Real-time SMS and Email alerts using Twilio or SendGrid.

[ ] REST API: Developing endpoints with Django REST Framework for mobile integration.

[ ] Mobile Support: Dedicated Flutter or React Native application.

## 👨‍💻 Team Members

```text
Khyati Agrawal

Pritam Vishvakarma

Heman

Kishan Kumar Sahu
```
## 🎯 Vision
To build a scalable and intelligent ecosystem where help requests are instantly matched with the right people, reducing response times and maximizing the efficiency of social impact initiatives.

"Smart systems create smarter solutions for a better world."

## 📌 Project Status
🚧 In Development – Currently optimizing the matching engine and polishing the dashboard UI.

## ⭐ Contributing
Contributions are what make the open-source community an amazing place to learn and create. Feel free to fork the repo and submit a pull request!

## 📜 License
This project is developed for Educational Purposes.

## 💡 Inspiration
Driven by the goal of combining modern technology with social good to solve real-world logistical challenges.