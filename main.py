import argparse
from tqdm import tqdm
import mysql.connector


def search_all_tables(host, user, password, database, search_value, stop_on_find, show_progress, ignore_tables,
                      like_search):
    """
    Searches all tables in a MySQL database for a given value.

    :param host: MySQL server hostname
    :param user: MySQL user
    :param password: MySQL password
    :param database: MySQL database name
    :param search_value: value to search for
    :param stop_on_find: whether to stop searching after the first match
    :param show_progress: whether to show a progress bar
    :param ignore_tables: a list of tables to ignore
    :param like_search: whether to use partial matching (LIKE)
    """
    connection = mysql.connector.connect(host=host, user=user, password=password, database=database)
    cursor = connection.cursor()

    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    tables = [t for t in tables if t not in ignore_tables]

    progress = tqdm(tables, desc="Scanning", unit="tables", disable=not show_progress)

    for table_name in progress:
        cursor.execute(
            f"SELECT * FROM information_schema.columns WHERE table_schema = '{database}' AND table_name = '{table_name}'")
        columns = [row[3] for row in cursor.fetchall()]

        for column_name in columns:
            if like_search:
                query = f"SELECT * FROM `{table_name}` WHERE `{column_name}` LIKE %s LIMIT 1"
            else:
                query = f"SELECT * FROM `{table_name}` WHERE `{column_name}` = %s LIMIT 1"

            try:
                cursor.execute(query, (search_value,))
                if cursor.fetchone() is not None:
                    tqdm.write(f"Match found in table '{table_name}', column '{column_name}'")
                    if stop_on_find:
                        return
            except mysql.connector.Error as e:
                tqdm.write(f"Error scanning {table_name}.{column_name}: {str(e)}")

    cursor.close()
    connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="Search for a value across all tables and columns in a MySQL database.")
    parser.add_argument("host", help="MySQL server host")
    parser.add_argument("user", help="MySQL user")
    parser.add_argument("password", help="MySQL password")
    parser.add_argument("database", help="MySQL database")
    parser.add_argument("search_value", help="Value to search for")
    parser.add_argument("-s", "--stop-on-find", action="store_true", help="Stop searching when a match is found")
    parser.add_argument("-p", "--hide-progress", action="store_true", help="Hide progress bar")
    parser.add_argument("-i", "--ignore-tables", nargs="*", default=[],
                        help="Ignore specific tables during the search")
    parser.add_argument("-l", "--like-search", action="store_true", help="Use LIKE instead of exact match")

    args = parser.parse_args()

    search_all_tables(args.host, args.user, args.password, args.database, args.search_value, args.stop_on_find,
                      not args.hide_progress, args.ignore_tables, args.like_search)


if __name__ == "__main__":
    main()
