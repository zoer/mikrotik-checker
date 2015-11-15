import re
import requests
import psycopg2
import psycopg2.extras
from flask import Flask
from urllib.parse import urlparse
import os

url = urlparse(os.environ.get("DATABASE_URL", ""))
conn = psycopg2.connect(database=url.path[1:],
                        host=url.hostname,
                        port=url.port,
                        user=url.username,
                        password=url.password)
conn.set_session(autocommit=True)

def create_db():
    """Initialize database"""

    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS versions(
             version varchar PRIMARY KEY,
             changelog text,
             clients varchar[] DEFAULT '{}')""")
    cur.close()

def get_new_versions():
    """Get new versions from the mikrotik.com website"""

    res = requests.get("http://www.mikrotik.com/client/ajax.php?" \
                       "action=getChangelog&id=24")

    if res.status_code == 200:
        matches = re.findall(r"(?s)(What's new in ([^\n\s\(]+).+?)(?=What|$)",
                             res.text)
        return dict([tuple(i) for i in map(reversed, matches)])

    return {}


def save_new_versions(versions):
    cur = conn.cursor()
    for version, changelog in versions.items():
        cur.execute(
            """INSERT INTO versions (version, changelog)
                 SELECT %s, %s WHERE NOT EXISTS (
                   SELECT version FROM versions WHERE version = %s);""",
            (version, changelog, version))
    cur.close()

def update_versions():
    """Get versions list from the mikrotik website and update DB"""

    versions = get_new_versions()
    if bool(versions):
        save_new_versions(versions)

def get_new_version_for_client(client):
    """Get new version for the given client.
    If user have been already reported about the last verion then the result
    will be empty dict"""

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
                SELECT *, %s = ANY(clients) AS known
                  FROM versions ORDER BY version DESC LIMIT 1""",
                (client,))

    row = cur.fetchone()
    if row is None or row['known'] is True: row = {}

    if bool(row):
        cur.execute("UPDATE versions SET clients = array_append(clients, %s)",
                    (client,))

    cur.close()
    return  row

create_db()
app = Flask(__name__)

@app.route("/")
def home():
    return "Nothing here...", 404

@app.route("/check/<client>")
def check(client):
    update_versions()
    version = get_new_version_for_client(client)
    if bool(version):
        return version["changelog"]
    else:
        return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
    conn.close()
