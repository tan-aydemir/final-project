DROP TABLE IF EXISTS locations;
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    deleted BOOLEAN DEFAULT FALSE
)
