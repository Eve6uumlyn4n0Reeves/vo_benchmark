# VO-Benchmark Implementation Standards

This document establishes coding standards and best practices to prevent technical debt accumulation in the VO-Benchmark project.

## 🚨 Critical Security Standards

### 1. Secret Management
- **NEVER** commit hard-coded secrets, API keys, or passwords
- Use environment variables for all sensitive configuration
- Generate secure random keys using `secrets.token_urlsafe(32)`
- Validate all environment variables at startup

```python
# ❌ BAD
SECRET_KEY = "hardcoded-secret-key"

# ✅ GOOD
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
```

### 2. SQL Injection Prevention
- Always use parameterized queries
- Validate SQL content before execution
- Use SQLAlchemy ORM when possible
- Implement SQL validation for migration files

```python
# ❌ BAD
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ GOOD
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### 3. Input Validation
- Validate all user inputs using Pydantic models
- Implement path traversal protection
- Sanitize file uploads
- Use type hints and runtime validation

## 🔧 Configuration Management

### 1. Environment Variables
- All configuration MUST be externalized
- Provide comprehensive `.env.example` files
- Use type validation for environment variables
- Support multiple environments (dev, staging, prod)

### 2. Hard-coded Values
- **PROHIBITED**: Hard-coded URLs, ports, file paths
- Use configuration classes with environment variable support
- Implement configuration validation at startup
- Document all configuration options

```python
# ❌ BAD
API_URL = "http://localhost:5000/api"

# ✅ GOOD
API_URL = os.environ.get('API_BASE_URL', '/api/v1')
```

### 3. Backend Dependencies
- 后端中间件与错误处理包含对 `sqlalchemy.exc.SQLAlchemyError` 的引用，必须安装 `SQLAlchemy`。
- 已将 `sqlalchemy>=2.0.0` 加入 `backend/requirements.txt`，请确保在部署/开发环境执行依赖安装。

## 🏗️ Code Quality Standards

### 1. Error Handling
- Implement comprehensive error handling middleware
- Use structured error responses with error codes
- Log errors with appropriate levels
- Never expose internal errors to clients in production

```python
# ✅ GOOD Error Handling Pattern
try:
    result = risky_operation()
    return jsonify(result), 200
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    return jsonify({"error": "Invalid input", "details": format_errors(e)}), 400
except BusinessLogicError as e:
    logger.error(f"Business error: {e}")
    return jsonify({"error": e.message, "code": e.code}), 400
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return jsonify({"error": "Internal server error"}), 500
```

### 2. Mock Implementation Prevention
- Complete all TODO comments before merging
- Implement real functionality, not placeholders
- Use feature flags for incomplete features
- Document any temporary implementations

### 3. Type Safety
- Use type hints for all function parameters and return values
- Implement runtime type checking in development
- Use Pydantic for data validation
- Enable strict TypeScript mode for frontend

## 🐳 Container and Deployment Standards

### 1. Docker Configuration
- Use service names instead of localhost in containers
- Make all ports configurable via environment variables
- Implement proper health checks
- Use multi-stage builds for optimization

```yaml
# ✅ GOOD Docker Compose
environment:
  - REACT_APP_API_URL=http://backend:5000/api
  - REACT_APP_WS_URL=ws://backend:5000/ws
```

### 2. Health Checks
- Implement comprehensive health check endpoints
- Include dependency status checks
- Monitor system resources
- Provide readiness and liveness probes

## 📊 API Design Standards

### 1. RESTful Design
- Follow REST conventions consistently
- Use appropriate HTTP status codes
- Implement proper pagination
- Version your APIs

### 2. Documentation
- Use OpenAPI/Swagger for all endpoints
- Provide comprehensive examples
- Document error responses
- Keep documentation up-to-date

### 3. Validation
- Validate all inputs using Pydantic
- Implement rate limiting
- Use CORS properly
- Sanitize outputs

## 🧪 Testing Standards

### 1. Test Coverage
- Minimum 80% code coverage for critical paths
- Unit tests for all business logic
- Integration tests for API endpoints
- End-to-end tests for critical workflows

### 2. Test Quality
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Use fixtures for test data

## 🔍 Code Review Process

### 1. Mandatory Checks
- [ ] No hard-coded values (URLs, ports, secrets)
- [ ] All TODO comments resolved or documented
- [ ] Proper error handling implemented
- [ ] Input validation added
- [ ] Security vulnerabilities addressed
- [ ] Type hints provided
- [ ] Tests written and passing
- [ ] Documentation updated

### 2. Security Review
- [ ] No secrets in code
- [ ] SQL injection protection
- [ ] Input sanitization
- [ ] Authentication/authorization
- [ ] CORS configuration
- [ ] File upload security

## 🚀 Performance Standards

### 1. Database
- Use connection pooling
- Implement query optimization
- Add appropriate indexes
- Monitor slow queries

### 2. Caching
- Implement Redis caching where appropriate
- Use HTTP caching headers
- Cache expensive computations
- Implement cache invalidation

### 3. Monitoring
- Log performance metrics
- Monitor resource usage
- Set up alerts for anomalies
- Track API response times

## 📝 Documentation Standards

### 1. Code Documentation
- Document all public APIs
- Use docstrings for functions and classes
- Explain complex algorithms
- Provide usage examples

### 2. Architecture Documentation
- Maintain system architecture diagrams
- Document data flow
- Explain design decisions
- Keep deployment guides updated

## 🔄 Continuous Integration

### 1. Automated Checks
- Run linting on all commits
- Execute test suite
- Check code coverage
- Scan for security vulnerabilities
- Validate configuration files

### 2. Quality Gates
- Block merges with failing tests
- Require code review approval
- Enforce coding standards
- Check for technical debt patterns

## 📋 Technical Debt Prevention

### 1. Regular Reviews
- Weekly technical debt assessment
- Monthly architecture reviews
- Quarterly security audits
- Annual technology stack evaluation

### 2. Refactoring Guidelines
- Refactor when adding new features
- Address technical debt in sprints
- Maintain refactoring backlog
- Document architectural decisions

## 🛠️ Development Tools

### 1. Required Tools
- **Python**: Black (formatting), Flake8 (linting), MyPy (type checking)
- **TypeScript**: ESLint, Prettier, TypeScript strict mode
- **Git**: Pre-commit hooks, conventional commits
- **IDE**: Configure with project standards

### 2. Recommended Extensions
- Python: pylint, autopep8, python-docstring-generator
- TypeScript: ESLint, Prettier, TypeScript Hero
- Docker: Docker extension for VS Code
- Git: GitLens, Git Graph

## 📞 Support and Questions

For questions about these standards or technical debt concerns:

1. Create an issue in the project repository
2. Tag it with `technical-debt` or `standards`
3. Provide specific examples and context
4. Suggest improvements or alternatives

Remember: **Prevention is better than cure**. Following these standards will save significant time and effort in the long run.
