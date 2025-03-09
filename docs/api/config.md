# Configuration API

The configuration utilities in ThinkiPlex provide functions for loading, validating, and managing configuration.

## Config Class

The `Config` class is the main entry point for configuration management in ThinkiPlex. It provides methods for loading, validating, and accessing configuration values.

### Initialization

```python
from thinkiplex.utils.config import Config

# Initialize with default config file path
config = Config()

# Initialize with custom config file path
config = Config(config_file="path/to/config.yaml")
```

### Methods

#### get

Get a configuration value using dot notation.

```python
# Get a configuration value
value = config.get("global.video_quality")

# Get a configuration value with fallback
value = config.get("global.nonexistent", fallback="default")
```

#### get_course_config

Get the configuration for a specific course.

```python
# Get course configuration
course_config = config.get_course_config("course-name")
```

#### get_courses

Get all configured courses.

```python
# Get all courses
courses = config.get_courses()
```

#### set

Set a configuration value using dot notation.

```python
# Set a configuration value
config.set("global.video_quality", "1080p")
```

#### save

Save the configuration to file.

```python
# Save configuration
config.save()
```

#### get_path

Get a path configuration value.

```python
# Get a path
path = config.get_path("global.base_dir")
```

#### validate_config

Validate the configuration against the schema.

```python
# Validate configuration
config.validate_config()
```

## Schema Validation

ThinkiPlex uses Pydantic models for schema validation. The following models are defined:

- `CourseConfig`: Schema for a course configuration
- `GlobalConfig`: Schema for global configuration
- `ThinkiPlexConfig`: Schema for the complete ThinkiPlex configuration

## Error Handling

The following exceptions may be raised during configuration operations:

- `ConfigError`: Base class for configuration errors
- `ValidationError`: Raised when configuration validation fails