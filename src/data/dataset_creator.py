import random
import logging
from .database_operations import create_table, is_duplicate, insert_qa_pair
from ..utils.api_client import generate_qa_pair

logger = logging.getLogger(__name__)


def create_dataset(num_entries, db_path, topics, progress_callback, stop_event, api_choice):
    """
    Create a dataset of QA pairs.

    :param num_entries: Number of entries to generate
    :param db_path: Path to the SQLite database
    :param topics: List of topics to generate questions about
    :param progress_callback: Function to call to update progress
    :param stop_event: Threading event to signal when to stop generation
    :param api_choice: Choice of API to use ('ollama' or 'openai')
    :return: Number of entries actually generated
    """
    create_table(db_path)

    generated_count = 0
    error_count = 0
    max_errors = 50  # Increased from 20

    while generated_count < num_entries and not stop_event.is_set():
        topic = random.choice(topics)
        try:
            question, answer, category = generate_qa_pair(
                topic, stop_event, api_choice)
            if question and answer and category:
                if not is_duplicate(question, db_path):
                    insert_qa_pair(db_path, question, answer, category)
                    generated_count += 1
                    error_count = 0  # Reset error count on successful generation
                    logger.info(f"Added new entry: {question[:50]}...")
                else:
                    logger.info(
                        f"Duplicate question detected and skipped: {question[:50]}...")
            else:
                error_count += 1

            progress_callback(generated_count, num_entries)

            if error_count >= max_errors:
                logger.error(
                    f"Stopping generation due to {max_errors} consecutive errors.")
                break

        except Exception as e:
            logger.error(f"Error in generate_and_store: {str(e)}")
            error_count += 1
            if error_count >= max_errors:
                logger.error(
                    f"Stopping generation due to {max_errors} consecutive errors.")
                break

    return generated_count


def generate_dataset_batch(batch_size, db_path, topics, progress_callback, stop_event, api_choice):
    """
    Generate a batch of QA pairs for the dataset.

    :param batch_size: Number of entries to generate in this batch
    :param db_path: Path to the SQLite database
    :param topics: List of topics to generate questions about
    :param progress_callback: Function to call to update progress
    :param stop_event: Threading event to signal when to stop generation
    :param api_choice: Choice of API to use ('ollama' or 'openai')
    :return: Number of entries generated in this batch
    """
    return create_dataset(batch_size, db_path, topics, progress_callback, stop_event, api_choice)


def resume_dataset_creation(total_entries, current_entries, db_path, topics, progress_callback, stop_event, api_choice):
    """
    Resume dataset creation from a previous point.

    :param total_entries: Total number of entries desired
    :param current_entries: Number of entries already in the database
    :param db_path: Path to the SQLite database
    :param topics: List of topics to generate questions about
    :param progress_callback: Function to call to update progress
    :param stop_event: Threading event to signal when to stop generation
    :param api_choice: Choice of API to use ('ollama' or 'openai')
    :return: Total number of entries after resuming
    """
    remaining_entries = total_entries - current_entries
    if remaining_entries <= 0:
        logger.info("Dataset is already complete. No new entries needed.")
        return current_entries

    logger.info(
        f"Resuming dataset creation. Generating {remaining_entries} more entries.")
    new_entries = create_dataset(
        remaining_entries, db_path, topics, progress_callback, stop_event, api_choice)
    return current_entries + new_entries


def get_generation_progress(db_path):
    """
    Get the current progress of dataset generation.

    :param db_path: Path to the SQLite database
    :return: Number of entries currently in the database
    """
    from .database_operations import get_dataset_stats
    stats = get_dataset_stats(db_path)
    return stats["total_pairs"]


if __name__ == "__main__":
    # This allows for testing the dataset creation process independently
    import threading
    logging.basicConfig(level=logging.INFO)

    test_db_path = "test_dataset.db"
    test_topics = ["python", "math", "science"]
    test_num_entries = 10

    def mock_progress(current, total):
        print(f"Progress: {current}/{total}")

    stop_event = threading.Event()

    print("Starting dataset creation test...")
    generated = create_dataset(
        test_num_entries, test_db_path, test_topics, mock_progress, stop_event, 'ollama')
    print(f"Dataset creation test completed. Generated {generated} entries.")

    # Test resuming dataset creation
    current_entries = get_generation_progress(test_db_path)
    print(f"Current entries in database: {current_entries}")

    total_desired = 15
    print(
        f"Resuming dataset creation to reach {total_desired} total entries...")
    final_count = resume_dataset_creation(
        total_desired, current_entries, test_db_path, test_topics, mock_progress, stop_event, 'ollama')
    print(
        f"Dataset creation resumed and completed. Final entry count: {final_count}")
