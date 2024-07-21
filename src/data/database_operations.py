import sqlite3
import json
import logging
from difflib import SequenceMatcher
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor(conn):
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def create_table(db_path):
    """
    Create the qa_pairs table if it doesn't exist.

    :param db_path: Path to the SQLite database
    """
    with get_db_connection(db_path) as conn:
        with get_cursor(conn) as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS qa_pairs
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               question TEXT UNIQUE,
                               answer TEXT,
                               category TEXT)''')
            conn.commit()


def is_duplicate(new_question, db_path, threshold=0.9):
    """
    Check if a question is too similar to existing questions in the database.

    :param new_question: The question to check
    :param db_path: Path to the SQLite database
    :param threshold: Similarity threshold (default: 0.9)
    :return: True if the question is a duplicate, False otherwise
    """
    with get_db_connection(db_path) as conn:
        with get_cursor(conn) as cursor:
            cursor.execute("SELECT question FROM qa_pairs")
            existing_questions = [row[0] for row in cursor.fetchall()]

    for existing_question in existing_questions:
        similarity = SequenceMatcher(
            None, new_question.lower(), existing_question.lower()).ratio()
        if similarity > threshold:
            return True
    return False


def insert_qa_pair(db_path, question, answer, category):
    """
    Insert a new QA pair into the database.

    :param db_path: Path to the SQLite database
    :param question: The question to insert
    :param answer: The answer to insert
    :param category: The category of the QA pair
    """
    with get_db_connection(db_path) as conn:
        with get_cursor(conn) as cursor:
            cursor.execute("INSERT INTO qa_pairs (question, answer, category) VALUES (?, ?, ?)",
                           (question, answer, category))
            conn.commit()


def get_all_qa_pairs(db_path):
    """
    Retrieve all QA pairs from the database.

    :param db_path: Path to the SQLite database
    :return: List of dictionaries containing QA pairs
    """
    with get_db_connection(db_path) as conn:
        with get_cursor(conn) as cursor:
            cursor.execute(
                "SELECT id, question, answer, category FROM qa_pairs")
            return [{"id": row[0], "question": row[1], "answer": row[2], "category": row[3]}
                    for row in cursor.fetchall()]


def export_to_json(db_path, json_path, progress_callback):
    """
    Export all QA pairs from the database to a JSON file.

    :param db_path: Path to the SQLite database
    :param json_path: Path to save the JSON file
    :param progress_callback: Function to call to update progress
    """
    qa_pairs = get_all_qa_pairs(db_path)
    total_pairs = len(qa_pairs)

    with open(json_path, 'w', encoding='utf-8') as f:
        for i, qa_pair in enumerate(qa_pairs, 1):
            # Remove newline characters from question and answer
            qa_pair['question'] = qa_pair['question'].replace('\n', ' ')
            qa_pair['answer'] = qa_pair['answer'].replace('\n', ' ')

            json.dump(qa_pair, f, ensure_ascii=False)
            # Write each QA pair on a new line for better readability
            f.write('\n')

            if i % 100 == 0 or i == total_pairs:
                progress_callback(i, total_pairs)
                logger.info(f"Exported {i}/{total_pairs} entries...")

    logger.info(f"Successfully exported {total_pairs} entries to {json_path}")


def get_dataset_stats(db_path):
    """
    Get statistics about the dataset.

    :param db_path: Path to the SQLite database
    :return: Dictionary containing dataset statistics
    """
    with get_db_connection(db_path) as conn:
        with get_cursor(conn) as cursor:
            cursor.execute("SELECT COUNT(*) FROM qa_pairs")
            total_pairs = cursor.fetchone()[0]

            cursor.execute(
                "SELECT category, COUNT(*) FROM qa_pairs GROUP BY category")
            category_counts = dict(cursor.fetchall())

    return {
        "total_pairs": total_pairs,
        "category_counts": category_counts
    }


if __name__ == "__main__":
    # This allows for testing the database operations independently
    logging.basicConfig(level=logging.INFO)

    test_db_path = "test_dataset.db"
    test_json_path = "test_dataset.json"

    create_table(test_db_path)

    # Test inserting a QA pair
    insert_qa_pair(test_db_path, "What is Python?",
                   "Python is a high-level programming language.", "python")

    # Test exporting to JSON
    def mock_progress(current, total):
        print(f"Export progress: {current}/{total}")

    export_to_json(test_db_path, test_json_path, mock_progress)

    # Test getting dataset stats
    stats = get_dataset_stats(test_db_path)
    print("Dataset stats:", stats)

    print("Database operations test completed.")
