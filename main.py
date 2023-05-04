import argparse
import mysql.connector
from tqdm import tqdm
import sys


def main(args):
    host = args.host
    user = args.user
    password = args.password
    database = args.database
    search_value = args.search_value
    column_timeout = args.column_timeout
    table_timeout = args.table_timeout
    ignore_tables = args.ignore_tables.split(',')

    # Add your database connection details here
    connection = mysql.connector.connect(host=host, user=user, password=password, database=database)
    cursor = connection.cursor()

    cursor.execute("SET SESSION max_execution_time = %s;", (table_timeout,))
    cursor.fetchall()

    cursor.execute("SHOW TABLES;")
    tables = [table[0] for table in cursor.fetchall() if table[0] not in ignore_tables]

    for table_name in tqdm(tables, desc="Scanning", unit="table"):
        cursor.execute("SET SESSION max_execution_time = %s;", (column_timeout,))
        cursor.fetchall()

        cursor.execute(f"SHOW COLUMNS FROM {table_name};")
        columns = [column[0] for column in cursor.fetchall()]

        for column_name in columns:
            try:
                if args.use_like:
                    query = f"SELECT * FROM {table_name} WHERE {column_name} LIKE %s;"
                else:
                    query = f"SELECT * FROM {table_name} WHERE {column_name} = %s;"

                cursor.execute(query, (search_value,))
                result = cursor.fetchall()
                if result:
                    tqdm.write(f"Found in table '{table_name}', column '{column_name}': {result}")
                    if args.stop_when_found:
                        sys.exit(0)

            except mysql.connector.errors.Error as e:
                tqdm.write(f"Error scanning {table_name}.{column_name}: {str(e)}")

    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan MySQL database for a value.")
    parser.add_argument("host", help="Host of the MySQL server.")
    parser.add_argument("user", help="Username for the MySQL server.")
    parser.add_argument("password", help="Password for the MySQL server.")
    parser.add_argument("database", help="Name of the database to search.")
    parser.add_argument("search_value", help="Value to search for.")
    parser.add_argument("--stop-when-found", action="store_true", help="Stop searching when the value is found.")
    parser.add_argument("--column-timeout", type=int, default=60, help="Timeout for each column search in seconds.")
    parser.add_argument("--table-timeout", type=int, default=60, help="Timeout for each table search in seconds.")
    parser.add_argument("--ignore-tables", default="", help="Comma-separated list of tables to ignore.")
    parser.add_argument("--use-like", action="store_true", help="Use LIKE instead of exact match.")

    args = parser.parse_args()

    main(args)
