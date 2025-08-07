# Contributing to AI Job Finder

Thank you for your interest in contributing to AI Job Finder! 🎉

## How to Contribute

### 🐛 Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/ai-job-finder/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)

### 💡 Suggesting Features

1. Check existing [Issues](https://github.com/yourusername/ai-job-finder/issues) for similar suggestions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Possible implementation approach

### 🔧 Code Contributions

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test your changes**
   ```bash
   python final_test.py
   ```
5. **Commit with clear messages**
   ```bash
   git commit -m "Add: feature description"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

## Development Setup

1. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/ai-job-finder.git
   cd ai-job-finder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run tests**
   ```bash
   python final_test.py
   ```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

## Areas for Contribution

### 🌐 Job Board Integrations
- Add new job boards (Monster, Glassdoor, etc.)
- Improve existing scrapers
- Handle edge cases and errors

### 🤖 AI Improvements
- Better resume parsing
- Enhanced job matching algorithms
- Skill extraction improvements

### 🎨 UI/UX Enhancements
- Mobile responsiveness
- Better loading states
- Improved job display
- Dark mode support

### 🔧 Performance
- Faster job scraping
- Better caching
- Database optimization
- API rate limiting

### 📱 New Features
- Job alerts/notifications
- Application tracking
- Salary insights
- Company reviews integration

## Testing

Before submitting a PR:

1. **Run the test suite**
   ```bash
   python final_test.py
   ```

2. **Test manually**
   - Upload a sample resume
   - Verify job search works
   - Check apply links function
   - Test on different browsers

3. **Check for errors**
   - No console errors
   - Proper error handling
   - Good user feedback

## Questions?

Feel free to:
- Open an issue for discussion
- Contact the maintainers
- Join our community discussions

Thank you for contributing! 🚀