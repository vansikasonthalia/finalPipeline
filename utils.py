# utils.py
import logging

def setup_logger(log_file):
    """Set up the logger with a specific log file."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create handlers
    stream_handler = logging.StreamHandler()  # Output to console
    file_handler = logging.FileHandler(log_file, encoding="utf-8")  # Log to file with UTF-8 encoding
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Apply formatter to handlers
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger
