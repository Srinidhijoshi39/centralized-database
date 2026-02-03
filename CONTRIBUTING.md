# Contributing to Centralized Trading Database

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/centralized-trading-database.git
   cd centralized-trading-database
   ```
3. **Set up the development environment**:
   ```bash
   python setup.py
   ```

## 🔧 Development Setup

### Prerequisites
- Python 3.7+
- PostgreSQL 12+
- Git

### Local Development
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov flake8  # For testing
   ```

3. Set up your `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your local database credentials
   ```

4. Run the application:
   ```bash
   python app.py
   ```

## 📝 Code Style

### Python Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Code Formatting
```bash
# Check code style
flake8 .

# Format code (if you have black installed)
black .
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_app.py
```

### Writing Tests
- Write tests for new features
- Ensure tests are isolated and don't depend on external services
- Use descriptive test names
- Mock external dependencies

## 📋 Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**:
   ```bash
   # Run tests
   pytest
   
   # Check code style
   flake8 .
   
   # Test the application manually
   python app.py
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template

### Pull Request Guidelines
- **Title**: Use a clear, descriptive title
- **Description**: Explain what changes you made and why
- **Testing**: Describe how you tested your changes
- **Screenshots**: Include screenshots for UI changes
- **Breaking Changes**: Clearly mark any breaking changes

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**:
   - Python version
   - Operating system
   - Database version

2. **Steps to reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior
   - Error messages or logs

3. **Additional context**:
   - Screenshots if applicable
   - Configuration details
   - Any workarounds you've found

## 💡 Feature Requests

For feature requests:

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** you're trying to solve
3. **Propose a solution** if you have one in mind
4. **Consider the scope** - is this a core feature or plugin?

## 📚 Documentation

### Updating Documentation
- Update README.md for significant changes
- Add docstrings to new functions/classes
- Update API documentation for new endpoints
- Include examples in documentation

### Documentation Style
- Use clear, concise language
- Include code examples
- Keep documentation up-to-date with code changes

## 🔒 Security

### Reporting Security Issues
- **DO NOT** open public issues for security vulnerabilities
- Email security issues to the maintainer
- Include detailed information about the vulnerability
- Allow time for the issue to be addressed before disclosure

### Security Guidelines
- Never commit sensitive data (passwords, keys, etc.)
- Use environment variables for configuration
- Validate all user inputs
- Follow secure coding practices

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: For security issues or private matters

## 🏷️ Commit Message Guidelines

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add session details endpoint
fix(database): resolve connection pool issue
docs(readme): update installation instructions
```

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributors page

Thank you for contributing! 🎉