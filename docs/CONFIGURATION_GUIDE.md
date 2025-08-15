# Configuration Guide

## Overview

This guide provides comprehensive documentation for all configuration parameters in the VO-Benchmark system, including validation rules, effects, and best practices for different deployment environments.

## Configuration Architecture

The VO-Benchmark system uses a hierarchical configuration system with:
- **Environment Variables**: Runtime configuration
- **Configuration Classes**: Environment-specific defaults
- **Validation System**: Parameter validation and type checking
- **Default Values**: Sensible defaults for all parameters

## Environment Variables

### Core Application Settings

#### SECRET_KEY
- **Type**: String
- **Required**: Yes (Production)
- **Default**: Auto-generated in development
- **Description**: Flask application secret key for session management and CSRF protection
- **Validation**: Must be at least 32 characters
- **Example**: `SECRET_KEY=your-super-secret-key-here-32-chars-min`
- **Security**: Never commit to version control, use environment-specific values

#### FLASK_ENV
- **Type**: String
- **Required**: No
- **Default**: `development`
- **Options**: `development`, `production`, `testing`
- **Description**: Determines application environment and behavior
- **Effects**:
  - `development`: Debug mode enabled, detailed error pages
  - `production`: Debug disabled, optimized for performance
  - `testing`: Special test configurations, in-memory databases

#### FLASK_HOST
- **Type**: String
- **Required**: No
- **Default**: `127.0.0.1` (development), `0.0.0.0` (production)
- **Description**: Host address for the Flask application
- **Validation**: Must be valid IP address or hostname
- **Example**: `FLASK_HOST=0.0.0.0`

#### FLASK_PORT
- **Type**: Integer
- **Required**: No
- **Default**: `5000`
- **Range**: 1-65535
- **Description**: Port number for the Flask application
- **Example**: `FLASK_PORT=8080`

### Database Configuration

#### DATABASE_URL
- **Type**: String (URL)
- **Required**: Yes (Production)
- **Default**: `sqlite:///vo_benchmark.db` (development)
- **Description**: Database connection URL
- **Validation**: Must be valid database URL
- **Examples**:
  - SQLite: `sqlite:///path/to/database.db`
  - PostgreSQL: `postgresql://user:pass@localhost:5432/vo_benchmark`
  - MySQL: `mysql://user:pass@localhost:3306/vo_benchmark`

#### REDIS_URL
#### SQLALCHEMY (Python package)
- **Required**: Yes
- **Reason**: 后端中间件与错误处理使用 `sqlalchemy.exc.SQLAlchemyError`
- **Install**: 已加入 `backend/requirements.txt`，执行后端依赖安装会自动安装

- **Type**: String (URL)
- **Required**: No
- **Default**: `redis://localhost:6379/0`
- **Description**: Redis connection URL for caching and task queues
- **Validation**: Must be valid Redis URL
- **Example**: `REDIS_URL=redis://redis-server:6379/1`

### File Storage Configuration

#### UPLOAD_FOLDER
- **Type**: String (Path)
- **Required**: No
- **Default**: `uploads`
- **Description**: Directory for uploaded files (datasets, images)
- **Validation**: Must be writable directory
- **Example**: `UPLOAD_FOLDER=/data/uploads`
- **Permissions**: Ensure web server has read/write access

#### DEFAULT_OUTPUT_DIR
- **Type**: String (Path)
- **Required**: No
- **Default**: `experiments`
- **Description**: Default directory for experiment results
- **Validation**: Must be writable directory
- **Example**: `DEFAULT_OUTPUT_DIR=/data/experiments`

#### DATASETS_ROOT
- **Type**: String (Path)
- **Required**: No
- **Default**: `datasets`
- **Description**: Root directory for dataset storage
- **Validation**: Must be readable directory
- **Example**: `DATASETS_ROOT=/data/datasets`

### Logging Configuration

#### LOG_LEVEL
- **Type**: String
- **Required**: No
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Minimum logging level
- **Effects**:
  - `DEBUG`: All messages including debug information
  - `INFO`: General information and above
  - `WARNING`: Warnings and errors only
  - `ERROR`: Errors and critical messages only
  - `CRITICAL`: Only critical system failures

#### LOG_TO_STDOUT
- **Type**: Boolean
- **Required**: No
- **Default**: `false`
- **Description**: Whether to log to stdout instead of files
- **Example**: `LOG_TO_STDOUT=true`
- **Use Case**: Container deployments, cloud logging

### Performance Configuration

#### MAX_CONCURRENT_TASKS
- **Type**: Integer
- **Required**: No
- **Default**: `4`
- **Range**: 1-32
- **Description**: Maximum number of concurrent experiment tasks
- **Validation**: Must be positive integer
- **Effects**: Higher values increase CPU/memory usage but improve throughput
- **Recommendation**: Set to number of CPU cores for CPU-bound tasks

#### MAX_CONTENT_LENGTH
- **Type**: Integer (Bytes)
- **Required**: No
- **Default**: `16777216` (16MB)
- **Description**: Maximum size for uploaded files
- **Example**: `MAX_CONTENT_LENGTH=104857600` (100MB)
- **Validation**: Must be positive integer

### CORS Configuration

#### CORS_ORIGINS
- **Type**: String (Comma-separated URLs)
- **Required**: No
- **Default**: `http://localhost:3000`
- **Description**: Allowed origins for CORS requests
- **Validation**: Must be valid URLs
- **Example**: `CORS_ORIGINS=http://localhost:3000,https://vo-benchmark.example.com`
- **Security**: Restrict to trusted domains in production

## Configuration Examples

### Development Environment
```bash
# .env.development
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
SECRET_KEY=dev-secret-key-not-for-production
DATABASE_URL=sqlite:///vo_benchmark_dev.db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000
MAX_CONCURRENT_TASKS=2
```

### Production Environment
```bash
# .env.production
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=${SECURE_SECRET_KEY}
DATABASE_URL=postgresql://user:pass@db:5432/vo_benchmark
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
LOG_TO_STDOUT=true
CORS_ORIGINS=https://vo-benchmark.example.com
MAX_CONCURRENT_TASKS=8
UPLOAD_FOLDER=/data/uploads
DEFAULT_OUTPUT_DIR=/data/experiments
DATASETS_ROOT=/data/datasets
```

## 路径与卷挂载对齐

### 生产环境路径建议

为确保 Docker 容器中的路径配置与卷挂载一致，建议使用以下环境变量：

```bash
# 生产环境路径配置
RESULTS_ROOT=/data/results
DATASETS_ROOT=/data/datasets
TEMP_ROOT=/data/tmp

# 对应的 docker-compose.yml 卷挂载
volumes:
  - ./data:/data
  - ./results:/data/results
  - ./backend/config:/app/config:ro
```

### 路径解析逻辑

配置管理器会按以下规则处理路径：

1. **相对路径**: 自动锚定到 backend 目录的绝对路径
2. **绝对路径**: 直接使用，不做转换
3. **环境变量**: 优先级最高，覆盖配置文件设置

### 常见路径配置

| 环境 | RESULTS_ROOT | DATASETS_ROOT | 说明 |
|------|--------------|---------------|------|
| 开发 | `./data/results` | `./data/datasets` | 相对于 backend 目录 |
| Docker | `/data/results` | `/data/datasets` | 容器内绝对路径 |
| 生产 | `/var/vo-benchmark/results` | `/var/vo-benchmark/datasets` | 自定义绝对路径 |

### Testing Environment
```bash
# .env.testing
FLASK_ENV=testing
FLASK_DEBUG=false
SECRET_KEY=test-secret-key-for-testing-only
DATABASE_URL=sqlite:///:memory:
LOG_LEVEL=WARNING
MAX_CONCURRENT_TASKS=1
UPLOAD_FOLDER=/tmp/vo_benchmark_test_uploads
DEFAULT_OUTPUT_DIR=/tmp/vo_benchmark_test_experiments
```

## Validation Rules

### Path Validation
- Must be absolute or relative paths
- Directory paths must exist and be accessible
- File paths must be in allowed directories
- Permissions must allow required operations (read/write)

### URL Validation
- Must be valid URL format
- Protocol must be supported (http, https, redis, postgresql, etc.)
- Host must be resolvable
- Port must be in valid range (1-65535)

### Integer Validation
- Must be valid integer format
- Must be within specified range
- Positive integers must be > 0

### String Validation
- Must meet minimum/maximum length requirements
- Must match allowed patterns (for enums)
- Must not contain dangerous characters

## Best Practices

### Security
1. **Never commit secrets**: Use environment variables for sensitive data
2. **Rotate secrets regularly**: Change SECRET_KEY and database passwords
3. **Restrict CORS origins**: Only allow trusted domains
4. **Use HTTPS in production**: Secure all communications
5. **Validate all inputs**: Use built-in validation system

### Performance
1. **Tune concurrent tasks**: Match to available CPU cores
2. **Configure appropriate timeouts**: Prevent resource exhaustion
3. **Monitor resource usage**: Adjust limits based on actual usage
4. **Use Redis for caching**: Improve response times

### Monitoring
1. **Set appropriate log levels**: Balance detail with performance
2. **Use structured logging**: Enable log aggregation
3. **Monitor configuration changes**: Track configuration drift
4. **Set up health checks**: Monitor system status

### Deployment
1. **Use environment-specific configs**: Separate dev/staging/prod
2. **Validate configuration on startup**: Catch errors early
3. **Document all changes**: Maintain configuration changelog
4. **Test configuration changes**: Validate in staging first

## Troubleshooting

### Common Issues

#### Configuration Not Loading
- Check environment variable names (case-sensitive)
- Verify .env file location and format
- Ensure proper file permissions

#### Database Connection Errors
- Validate DATABASE_URL format
- Check database server availability
- Verify credentials and permissions

#### File Permission Errors
- Check directory permissions for upload/output folders
- Ensure web server user has required access
- Verify disk space availability

#### CORS Errors
- Check CORS_ORIGINS configuration
- Verify frontend URL matches exactly
- Include protocol (http/https) in origins

### Debugging Configuration
1. **Enable debug logging**: Set LOG_LEVEL=DEBUG
2. **Check configuration values**: Use health check endpoints
3. **Validate environment**: Use configuration validation tools
4. **Test incrementally**: Change one parameter at a time
