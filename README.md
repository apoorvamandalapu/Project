# F1 Data API

This is a **FastAPI** application for fetching, storing, and querying Formula 1 (F1) data. The app integrates with the [Ergast API](https://ergast.com/mrd/) for real-time F1 data, supports both local SQLite and PostgreSQL databases, and includes AI agent to answer user queries about F1 data.

---

## Features

- **Fetch data from Ergast API**  
  Retrieve F1 drivers, constructors, and races for any season.

- **Filter and search**  
  Filter drivers using fuzzy matching on name, code, or other fields.

- **Local SQLite database**  
  Store races locally and perform manual CRUD operations.

- **PostgreSQL database**  
  Store drivers manually or import data from the API.  
  Link drivers to constructors.

- **Manual data management**  
  Add, update, and delete races and drivers manually.

- **AI Agent Integration**  
  A Google ADK-based agent can answer user queries about drivers and F1 data.  
  - Uses a database tool to fetch driver and constructor info.
  - Uses API to fetch data. 
---

## Tech Stack

- **Framework:** FastAPI  
- **Database:** SQLite, PostgreSQL  
- **ORM:** SQLAlchemy  
- **HTTP Client:** `requests`  
- **AI Agent:** Google ADK
- **Python Version:** 3.12+  

---

## Setup

1. **Clone the repository**
   ```bash
   git clone <repo_url>
   cd <repo_folder>
