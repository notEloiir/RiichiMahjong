import os
import sqlite3


def get_match_log_data(db_dir, year):
    db_file = str(year) + ".db"
    if db_file in os.listdir(db_dir):
        db_path = os.path.join(db_dir, db_file)
        connection = sqlite3.connect(db_path)
        with connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM logs WHERE is_processed != 0 AND is_sanma = 0 AND was_error = 0;")
            match_no = cursor.fetchone()[0]

            cursor.execute("SELECT log_content FROM logs WHERE is_processed != 0 AND is_sanma = 0 AND was_error = 0;")
            return cursor, match_no
    else:
        raise Exception(f"No database for year {year}.")
