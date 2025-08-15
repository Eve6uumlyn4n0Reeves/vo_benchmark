# Configuration System Migration Guide

## Overview

The VO-Benchmark configuration system has been unified to use `config.manager` as the single source of truth. The old `api.config` module is deprecated and will be removed in a future version.

## Changes Summary

### Before (Deprecated)
```python
from api.config import get_config

config = get_config('development')
app.config.from_object(config)
```

### After (Current)
```python
from config.manager import get_config

unified_config = get_config()
# Configuration is automatically applied to Flask app
```

## Configuration Structure

The unified configuration uses a dataclass-based structure:

```python
@dataclass
class AppConfig:
    # Core settings
    secret_key: str
    debug: bool
    
    # Database configuration
    database: DatabaseConfig
    
    # Redis configuration  
    redis: RedisConfig
    
    # CORS configuration
    cors: CorsConfig
    
    # Logging configuration
    logging: LoggingConfig
    
    # Storage paths
    storage: StorageConfig
    
    # Experiment defaults
    experiment: ExperimentConfig
```

## Environment Variables

The unified configuration system reads from these environment variables:

### Core Settings
- `SECRET_KEY` - Application secret key
- `FLASK_ENV` - Environment (development/production/testing)
- `DEBUG` - Debug mode (true/false)

### Database
- `DATABASE_URL` - Database connection string
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Individual DB settings

### Redis
- `REDIS_URL` - Redis connection string
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` - Individual Redis settings

### CORS
- `CORS_ORIGINS` - Comma-separated list of allowed origins

### Storage
- `DATASETS_ROOT` - Root directory for datasets
- `RESULTS_ROOT` - Root directory for results
- `TEMP_ROOT` - Temporary files directory

### Logging
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_TO_STDOUT` - Log to stdout (true/false)

## Migration Steps

### 1. Update Imports

**Before:**
```python
from api.config import get_config, DevelopmentConfig, ProductionConfig
```

**After:**
```python
from config.manager import get_config, get_client_config
```

### 2. Update Configuration Access

**Before:**
```python
config = get_config('development')
debug_mode = config.DEBUG
database_url = config.DATABASE_URL
```

**After:**
```python
config = get_config()
debug_mode = config.debug
database_url = config.database.url
```

### 3. Update Flask App Configuration

The Flask app configuration is now automatically handled in `create_app()`. No manual configuration loading is needed.

### 4. Update Client Configuration

**Before:**
```python
# Client config was mixed with server config
```

**After:**
```python
from config.manager import get_client_config

client_config = get_client_config()
# Returns only client-safe configuration
```

## Backward Compatibility

The `api.config` module is still available but deprecated. It will:
- Issue deprecation warnings when imported
- Continue to work for existing code
- Be removed in a future version

## Testing

Update your tests to use the new configuration system:

```python
# Test configuration
from config.manager import get_config

def test_config():
    config = get_config()
    assert config.debug is True  # In test environment
    assert config.database.url.startswith('sqlite://')
```

## Timeline

- **Current**: Both systems available, `api.config` deprecated
- **Next release**: Remove `api.config` module
- **Migration deadline**: Update all code before next release

## Troubleshooting

### Common Issues

1. **Import errors**: Update import statements to use `config.manager`
2. **Attribute errors**: Update attribute access (e.g., `config.DEBUG` → `config.debug`)
3. **Configuration not found**: Ensure environment variables are set correctly

### Getting Help

1. Check this migration guide
2. Review the `config.manager` module documentation
3. Look at updated examples in the codebase
4. Test with the new configuration system
