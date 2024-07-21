import pytest
import sqlite3
from unittest.mock import Mock, patch
from src.data.dataset_creator import create_dataset, generate_and_store
from src.utils.api_client import generate_qa_pair


@pytest.fixture
def mock_db():
    """Create a mock database connection and cursor."""
    conn = Mock(spec=sqlite3.Connection)
    cursor = Mock(spec=sqlite3.Cursor)
    conn.cursor.return_value = cursor
    return conn, cursor


@pytest.fixture
def mock_stop_event():
    """Create a mock stop event."""
    return Mock()


def test_create_dataset_success(mock_db, mock_stop_event):
    conn, cursor = mock_db
    topics = ["python", "math", "science"]
    num_entries = 5

    # Mock the generate_and_store function to always return True
    with patch('src.data.dataset_creator.generate_and_store', return_value=True):
        # Mock the progress callback
        mock_progress = Mock()

        result = create_dataset(num_entries, "test.db",
                                topics, mock_progress, mock_stop_event)

        assert result == num_entries
        assert mock_progress.call_count == num_entries


def test_create_dataset_stop_event(mock_db, mock_stop_event):
    conn, cursor = mock_db
    topics = ["python", "math", "science"]
    num_entries = 5

    # Set the stop event after 2 iterations
    mock_stop_event.is_set.side_effect = [
        False, False, True] + [True] * (num_entries - 3)

    with patch('src.data.dataset_creator.generate_and_store', return_value=True):
        mock_progress = Mock()

        result = create_dataset(num_entries, "test.db",
                                topics, mock_progress, mock_stop_event)

        assert result == 2
        assert mock_progress.call_count == 2


def test_create_dataset_error_limit(mock_db, mock_stop_event):
    conn, cursor = mock_db
    topics = ["python", "math", "science"]
    num_entries = 20

    # Simulate errors in generate_and_store
    with patch('src.data.dataset_creator.generate_and_store', side_effect=[False] * 10 + [True] * 10):
        mock_progress = Mock()

        result = create_dataset(num_entries, "test.db",
                                topics, mock_progress, mock_stop_event)

        assert result == 0
        assert mock_progress.call_count == 10


@patch('src.data.dataset_creator.generate_qa_pair')
@patch('src.data.dataset_creator.is_duplicate')
def test_generate_and_store_success(mock_is_duplicate, mock_generate_qa_pair, mock_db, mock_stop_event):
    conn, cursor = mock_db
    mock_generate_qa_pair.return_value = (
        "Test question?", "Test answer.", "test")
    mock_is_duplicate.return_value = False

    result = generate_and_store("test", cursor, conn, mock_stop_event)

    assert result == True
    cursor.execute.assert_called_once()
    conn.commit.assert_called_once()


@patch('src.data.dataset_creator.generate_qa_pair')
@patch('src.data.dataset_creator.is_duplicate')
def test_generate_and_store_duplicate(mock_is_duplicate, mock_generate_qa_pair, mock_db, mock_stop_event):
    conn, cursor = mock_db
    mock_generate_qa_pair.return_value = (
        "Test question?", "Test answer.", "test")
    mock_is_duplicate.return_value = True

    result = generate_and_store("test", cursor, conn, mock_stop_event)

    assert result == False
    cursor.execute.assert_not_called()
    conn.commit.assert_not_called()


@patch('src.data.dataset_creator.generate_qa_pair')
def test_generate_and_store_api_failure(mock_generate_qa_pair, mock_db, mock_stop_event):
    conn, cursor = mock_db
    mock_generate_qa_pair.return_value = (None, None, None)

    result = generate_and_store("test", cursor, conn, mock_stop_event)

    assert result == False
    cursor.execute.assert_not_called()
    conn.commit.assert_not_called()


def test_generate_and_store_stop_event(mock_db, mock_stop_event):
    conn, cursor = mock_db
    mock_stop_event.is_set.return_value = True

    result = generate_and_store("test", cursor, conn, mock_stop_event)

    assert result == False
    mock_generate_qa_pair.assert_not_called()
    cursor.execute.assert_not_called()
    conn.commit.assert_not_called()


if __name__ == "__main__":
    pytest.main()
