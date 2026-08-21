"""Create the configured PostgreSQL database if it does not exist."""
from decouple import config
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def main():
    name = config('DB_NAME', default='petxpert_db')
    if not name.replace('_', '').isalnum():
        raise SystemExit(f'Unsafe database name: {name}')

    conn = psycopg2.connect(
        dbname='postgres',
        user=config('DB_USER', default='postgres'),
        password=config('DB_PASSWORD', default=''),
        host=config('DB_HOST', default='localhost'),
        port=config('DB_PORT', default='5432'),
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (name,))
    if cur.fetchone():
        print(f'Database already exists: {name}')
    else:
        cur.execute(f'CREATE DATABASE "{name}"')
        print(f'Created database: {name}')
    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
