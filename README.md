# JobPulse

> A modern, production-ready job search application for BDJobs with a beautiful GUI and comprehensive database support.

![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Hits](https://hits.sh/github.com/Almas-Ali/jobpulse.svg)

![JobPulse Screenshot](https://raw.githubusercontent.com/Almas-Ali/jobpulse/refs/heads/main/screenshots/landing-page.png)

## Overview

JobPulse is a desktop application that provides a streamlined interface for searching and managing job listings from BDJobs.com. Built with modern Python technologies, it features a clean CustomTkinter GUI, SQLAlchemy database integration, and robust API handling.

## ✨ Features

### 🔍 Job Search
- **Quick Search**: Fast keyword and location-based job search from the home screen
- **Advanced Search**: Comprehensive filtering with multiple criteria:
  - Location selection (all major Bangladesh cities)
  - Job type (Full-time, Part-time, Contract, Intern)
  - Job level (Entry, Mid, Top)
  - Posted within timeframe (Today to Last 5 days)
  - Experience range (Min/Max years)
  - Salary range (BDT)
  - Work arrangement (Office/Work from Home)
  - Fresher jobs filter

### 📊 Pagination & Display
- Configurable results per page (5, 10, 20, 50)
- Previous/Next page navigation
- Real-time page information display
- Smooth API-based pagination

### 💾 Job Management
- **Save Jobs**: Bookmark interesting job listings for later review
- **Track Applications**: Mark jobs as applied and track application status
- **Application Status Tracking**:
  - Interested
  - Applied
  - Interview
  - Rejected
  - Accepted
- Add notes to each application

### 📈 Dashboard & Analytics
- Total saved jobs count
- Total applications submitted
- Interview count tracking
- Offers received statistics
- Recent activity timeline

### 🎨 Theme Support
- **4 Theme Options**:
  - Dark Blue (default)
  - Dark Green
  - Light Blue
  - Light Green
- Persistent theme preferences
- Smooth theme switching (requires restart)

### 🗄️ Database Features
- SQLite database for local data storage
- User profile management
- Job data persistence
- Application history tracking
- Configuration storage

## 🚀 Installation

### Prerequisites
- Python 3.13 or higher
- `uv` package manager (recommended) or `pip`

### Using uv (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd jobpulse

# Install with uv
uv sync

# Run the application
uv run main.py
```

### Using pip
```bash
# Clone the repository
git clone <repository-url>
cd jobpulse

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the application
python main.py
```

## 📦 Dependencies

### Core Dependencies
- **httpx** (>=0.27.0): Async HTTP client for API requests
- **pydantic** (>=2.9.0): Data validation and parsing
- **tenacity** (>=9.0.0): Retry logic for robust API calls
- **sqlalchemy** (>=2.0.0): Database ORM
- **customtkinter** (>=5.2.0): Modern GUI framework
- **python-dateutil** (>=2.8.0): Date parsing utilities

### Development Dependencies
- **ruff** (>=0.8.0): Fast Python linter
- **pytest** (>=8.0.0): Testing framework
- **pytest-asyncio** (>=0.24.0): Async testing support

## 🏗️ Project Structure

```
jobpulse/
├── jobpulse/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration constants
│   ├── gui.py               # CustomTkinter GUI implementation
│   ├── http_client.py       # HTTP client with retry logic
│   ├── locations.py         # Bangladesh city/location mappings
│   ├── models.py            # Pydantic data models
│   ├── orm.py               # SQLAlchemy ORM layer
│   └── scraper.py           # BDJobs API integration
├── main.py                  # Application entry point
├── pyproject.toml           # Project metadata and dependencies
├── jobpulse.db              # SQLite database (created on first run)
└── README.md                # This file
```

## 💻 Usage

### Starting the Application
```bash
uv run main.py
```

### Basic Workflow

1. **Search for Jobs**
   - Use Quick Search from home or navigate to Advanced Search
   - Enter keywords (e.g., "Software Engineer")
   - Optionally select location and other filters
   - Click "Search Jobs"

2. **Review Results**
   - Browse job listings with company info, location, and deadlines
   - Click "View Details" to open job on BDJobs website
   - Save interesting jobs with "Save Job" button
   - Mark applied jobs with "Mark Applied" button

3. **Manage Applications**
   - Navigate to "My Applications" to see all tracked jobs
   - Update application status as you progress
   - Add notes for each application

4. **Track Progress**
   - View Dashboard for statistics and insights
   - Monitor saved jobs in "Saved Jobs" section
   - Review recent activity

## 🛠️ Configuration

### Database Location
By default, the SQLite database is created in the project root as `jobpulse.db`. You can customize this in `jobpulse/orm.py`.

### API Configuration
API settings can be modified in `jobpulse/config.py`:
- `DEFAULT_TIMEOUT`: HTTP request timeout (default: 30s)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `MIN_REQUEST_INTERVAL`: Rate limiting delay (default: 0.5s)

### Theme Preferences
Themes are saved in the database and persist across sessions. Change theme from the top menu bar.

## 🔌 API Integration

JobPulse integrates with the BDJobs API:
- Base URL: `https://api.bdjobs.com`
- Endpoint: `/Jobs/api/JobSearch/GetJobSearch`
- Features automatic retry with exponential backoff
- Connection pooling for efficient requests
- Proper error handling and logging

## 📝 Logging

Application logs are saved to:
- `jobpulse.log`: File-based logging
- Console output: Real-time logging

Log levels:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Errors with stack traces

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Md. Almas Ali**
- Email: almas@almasali.net

## 🙏 Acknowledgments

- [BDJobs.com](https://bdjobs.com) for the job listings API
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI framework
- All contributors who help improve this project

## 📋 Roadmap

- [ ] Email notifications for new job matches
- [ ] Resume/CV management
- [ ] Job application templates
- [ ] Export data to CSV/PDF
- [ ] Multi-language support
- [ ] Browser extension integration
- [ ] Job alerts and scheduling

## 🐛 Known Issues

- Theme changes require application restart
- Large result sets may take time to load

## 💡 Tips

- Use advanced search filters to narrow down results
- Regularly update application statuses for better tracking
- Check Dashboard frequently to monitor your job search progress
- Save jobs immediately when you find interesting opportunities

## 🔗 Related Links

- [BDJobs Official Website](https://bdjobs.com)
- [CustomTkinter Documentation](https://customtkinter.tomschimansky.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)

---

**Note**: This application is not officially affiliated with BDJobs.com. It's an independent tool built to enhance the job search experience.
