## Database Models with SQLite and SQLAlchemy

This module defines two tables using SQLAlchemy ORM on top of a SQLite database:

- **connections**
- **tools**

### Requirements

Install dependencies (preferably in a virtual environment):

```bash
pip install -r requirements.txt
```

### Running the model definition and creating the database

By default, the database will be created as a file named `app.db` in the same directory.

To create the tables, run:

```bash
python models.py
```

This will create `app.db` (if it does not exist) and create the `connections` and `tools` tables with the specified constraints.



