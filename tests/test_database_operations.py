import pytest
import sqlite3
import json
from unittest.mock import Mock, patch, mock_open
from src.data.database_operations import (
    create_table,
    is_duplicate,
    insert_qa_pair,
    get_all_qa_pairs,
    export_to_json,
    get_dataset_stats
)


@pytest.fixture
def test_db():
    """Create a temporary in-memory SQLite database for testing."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    create_table(cursor)
    yield conn, cursor
    conn.close()


def test_create_table(test_db):
    conn, cursor = test_db
    # Table should already be created by the fixture
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='qa_pairs'")
    assert cursor.fetchone() is not None


def test_is_duplicate(test_db):
    conn, cursor = test_db
    insert_qa_pair(cursor, "Test question?", "Test answer.", "test")
    conn.commit()

    assert is_duplicate("Test question?", cursor) == True
    assert is_duplicate("Different question?", cursor) == False
    # Testing case insensitivity
    assert is_duplicate("test question?", cursor) == True


def test_insert_qa_pair(test_db):
    conn, cursor = test_db
    insert_qa_pair(cursor, "New question?", "New answer.", "new")
    conn.commit()

    cursor.execute("SELECT * FROM qa_pairs")
    result = cursor.fetchone()
    assert result[1] == "New question?"
    assert result[2] == "New answer."
    assert result[3] == "new"


def test_get_all_qa_pairs(test_db):
    conn, cursor = test_db
    insert_qa_pair(cursor, "Q1?", "A1.", "cat1")
    insert_qa_pair(cursor, "Q2?", "A2.", "cat2")
    conn.commit()

    pairs = get_all_qa_pairs(cursor)
    assert len(pairs) == 2
    assert pairs[0]['question'] == "Q1?"
    assert pairs[1]['answer'] == "A2."


@patch('builtins.open', new_callable=mock_open)
def test_export_to_json(mock_file, test_db):
    conn, cursor = test_db
    insert_qa_pair(cursor, "Q1?", "A1.", "cat1")
    insert_qa_pair(cursor, "Q2?", "A2.", "cat2")
    conn.commit()

    mock_progress = Mock()
    export_to_json(':memory:', 'test.json', mock_progress)

    mock_file.assert_called_once_with('test.json', 'w', encoding='utf-8')
    handle = mock_file()

    # Check if json.dump was called twice (once for each QA pair)
    assert handle.write.call_count == 2

    # Check if progress callback was called
    assert mock_progress.call_count == 2


def test_get_dataset_stats(test_db):
    conn, cursor = test_db
    insert_qa_pair(cursor, "Q1?", "A1.", "cat1")
    insert_qa_pair(cursor, "Q2?", "A2.", "cat1")
    insert_qa_pair(cursor, "Q3?", "A3.", "cat2")
    conn.commit()

    stats = get_dataset_stats(':memory:')
    assert stats['total_pairs'] == 3
    assert stats['category_counts'] == {'cat1': 2, 'cat2': 1}


def test_is_duplicate_threshold(test_db):
    conn, cursor = test_db
    insert_qa_pair(cursor, "What is the capital of France?",
                   "Paris.", "geography")
    conn.commit()

    # Test with different thresholds
    assert is_duplicate("What is the capital of France?",
                        cursor, threshold=0.9) == True
    assert is_duplicate("What is the capital of Spain?",
                        cursor, threshold=0.7) == True
    assert is_duplicate("What is the capital of Spain?",
                        cursor, threshold=0.9) == False


@pytest.mark.parametrize("question,expected", [
    ("What is Python?", True),
    ("How does Python work?", False),
    ("What is python?", True),  # Testing case insensitivity
    ("What is Pyth0n?", False),  # Testing small differences
])
def test_is_duplicate_various_questions(test_db, question, expected):
    conn, cursor = test_db
    insert_qa_pair(cursor, "What is Python?",
                   "Python is a programming language.", "programming")
    conn.commit()

    assert is_duplicate(question, cursor) == expected


if __name__ == "__main__":
    pytest.main()
