import sqlite3
import json
from mcp.server.fastmcp import FastMCP

# --- Database Setup ---
DB_NAME = ":memory:"  # Use an in-memory database for this demo


def setup_database():
    """Creates and populates the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS players")
    cursor.execute(
        """
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            points REAL NOT NULL
        )
        """
    )
    players_data = [
        ("LeBron James", 27.1),
        ("Michael Jordan", 30.1),
        ("Kobe Bryant", 25.0),
        ("Stephen Curry", 24.3),
        ("Kevin Durant", 27.0),
    ]
    cursor.executemany("INSERT INTO players (name, points) VALUES (?, ?)", players_data)
    conn.commit()
    conn.close()


# --- MCP Server ---
mcp = FastMCP(name="SQLiteServer")


@mcp.tool()
def query_nba_stats(sql_query: str) -> str:
    """
    Executes a SQL query against the NBA players database and returns the result as JSON.
    The table is named 'players' with columns 'name' (TEXT) and 'points' (REAL).
    Example query: 'SELECT * FROM players WHERE points > 25;'
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        # Convert rows to a list of dictionaries
        result = [dict(row) for row in rows]
        return json.dumps(result, indent=2)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
    mcp.run(transport="stdio") 