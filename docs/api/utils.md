# Utilities API

The utilities modules in ThinkiPlex provide support functions and classes for various operations. These include:

- [Configuration](#configuration)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Parallel Processing](#parallel-processing)

## Configuration

See the [Configuration API](config.md) for details on configuration utilities.

## Logging

ThinkiPlex uses the standard Python logging module with some enhancements for consistent logging across the application.

### setup_logging

Set up logging for ThinkiPlex.

```python
from thinkiplex.utils.logging import setup_logging

# Set up logging with default settings
logger = setup_logging()

# Set up logging with custom file and level
logger = setup_logging(log_file="path/to/log.txt", level=logging.DEBUG)
```

### get_logger

Get the ThinkiPlex logger.

```python
from thinkiplex.utils.logging import get_logger

# Get the logger
logger = get_logger()

# Use the logger
logger.info("This is an info message")
logger.error("This is an error message")
```

## Error Handling

ThinkiPlex provides a hierarchy of exception classes for consistent error handling.

### Base Exception

```python
from thinkiplex.utils.exceptions import ThinkiPlexError

# Catch all ThinkiPlex errors
try:
    # Some operation
    pass
except ThinkiPlexError as e:
    print(f"ThinkiPlex error: {e}")
```

### Configuration Errors

```python
from thinkiplex.utils.exceptions import ConfigError, ValidationError

# Catch configuration errors
try:
    # Configuration operation
    pass
except ValidationError as e:
    print(f"Configuration validation error: {e}")
except ConfigError as e:
    print(f"Configuration error: {e}")
```

### Downloader Errors

```python
from thinkiplex.utils.exceptions import DownloaderError, PHPError, DockerError

# Catch downloader errors
try:
    # Downloader operation
    pass
except PHPError as e:
    print(f"PHP error: {e}")
except DockerError as e:
    print(f"Docker error: {e}")
except DownloaderError as e:
    print(f"Downloader error: {e}")
```

### Organizer Errors

```python
from thinkiplex.utils.exceptions import OrganizerError, MediaProcessingError, MetadataError

# Catch organizer errors
try:
    # Organizer operation
    pass
except MediaProcessingError as e:
    print(f"Media processing error: {e}")
except MetadataError as e:
    print(f"Metadata error: {e}")
except OrganizerError as e:
    print(f"Organizer error: {e}")
```

### File System Errors

```python
from thinkiplex.utils.exceptions import FileSystemError

# Catch file system errors
try:
    # File system operation
    pass
except FileSystemError as e:
    print(f"File system error: {e}")
```

### Network Errors

```python
from thinkiplex.utils.exceptions import NetworkError, AuthenticationError

# Catch network errors
try:
    # Network operation
    pass
except AuthenticationError as e:
    print(f"Authentication error: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
```

## Parallel Processing

ThinkiPlex provides utilities for parallel processing of tasks.

### parallel_map

Execute a function on multiple items in parallel.

```python
from thinkiplex.utils.parallel import parallel_map

# Define a function that processes an item
def process_item(item):
    # Process the item
    return item * 2

# Process items in parallel
items = [1, 2, 3, 4, 5]
results = parallel_map(process_item, items, max_workers=4)

# results = [2, 4, 6, 8, 10]
```