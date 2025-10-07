# F1 Data API

This is a **FastAPI** application for fetching, storing, and querying Formula 1 (F1) data. The app integrates with the [API](https://api.jolpi.ca/ergast/) for real-time F1 data and supports both local SQLite and PostgreSQL databases.

---

## Features

- **Fetch data from Ergast API**  
  Retrieve F1 drivers, constructors, and races for any season.

- **Filter and search**  
  Filter drivers using fuzzy matching on name, code, or other fields. This is used to filter drivers based on different attributes.

- **Local SQLite database**  
  Store races locally and perform manual CRUD operations.

- **PostgreSQL database**  
  Store drivers manually or import data from the API.  
  Link drivers to constructors.

- **Manual data management**  
  Add, update, and delete races and drivers manually.

