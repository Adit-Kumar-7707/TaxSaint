# TaxSaint Frontend

## Overview

The TaxSaint frontend is the React-based user interface for the TaxSaint financial assistance platform.

It provides separate workflows for:

- Salaried employees
- Business owners

The frontend collects financial information, displays tax results, displays financial alerts, and communicates with the FastAPI backend through REST APIs.

The frontend does not connect directly to the Supabase database.

---

## Technology Stack

- React 19
- Vite
- JavaScript
- REST API
- FastAPI backend
- Supabase PostgreSQL through the backend

---

## Project Structure

```text
TaxSaint/
├── frontend/
│   ├── README.md
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── dist/
│   │   ├── index.html
│   │   └── assets/
│   │       └── index-CS-zHLpy.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       │   ├── ErrorMessage.jsx
│       │   ├── Loading.jsx
│       │   ├── Navbar.jsx
│       │   ├── PageContainer.jsx
│       │   ├── Sidebar.jsx
│       │   └── SuccessMessage.jsx
│       ├── hooks/
│       │   └── useApi.js
│       ├── pages/
│       │   ├── Business.jsx
│       │   ├── Dashboard.jsx
│       │   ├── Profile.jsx
│       │   └── Salaried.jsx
│       └── services/
│           └── api.js
