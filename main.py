import sys
import argparse
import logging
from src.gui.application import Application
from src.utils.logging_config import setup_logger


def parse_arguments():
    parser = argparse.ArgumentParser(description="QA Dataset Generator")
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--log-file', type=str, help='Path to log file')
    return parser.parse_args()


def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger(log_file=args.log_file, level=log_level)

    logger.debug("Starting application in debug mode")

    try:
        # Initialize and run the main application
        app = Application(logger)
        app.mainloop()
    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
