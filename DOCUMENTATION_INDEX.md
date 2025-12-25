# Documentation Index

Complete index of Paint Controller documentation.

## Quick Navigation

### For New Users

Start here if you're new to Paint Controller:

1. **[QUICKSTART.md](QUICKSTART.md)** ⚡
   - 15-minute setup guide
   - First-run instructions
   - Common issues and solutions
   - Essential commands
   
2. **[README.md](README.md)** 📖
   - Project overview
   - Features and capabilities
   - Installation guide
   - Basic usage examples
   - Troubleshooting

### For Developers

Essential reading for contributors and developers:

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** 🏗️
   - System design and structure
   - Package organization
   - Threading model
   - Data flow patterns
   - Extension points

2. **[API_REFERENCE.md](API_REFERENCE.md)** 📚
   - Complete API documentation
   - All classes and methods
   - Code examples
   - QML integration guide

3. **[CONTRIBUTING.md](CONTRIBUTING.md)** 🤝
   - Development setup
   - Code style guidelines
   - Testing requirements
   - Contribution workflow
   - How to submit changes

### For Automation Users

If you're working with workflows and automation:

1. **[WORKFLOWS.md](WORKFLOWS.md)** ⚙️
   - YAML workflow format
   - Available action types
   - Complete examples
   - Best practices
   - Troubleshooting

## Documentation Structure

```
paint_controller/
├── README.md              # Main documentation (start here)
├── QUICKSTART.md          # Fast setup guide (15 min)
├── ARCHITECTURE.md        # System architecture
├── API_REFERENCE.md       # Complete API docs
├── WORKFLOWS.md           # Workflow system guide
├── CONTRIBUTING.md        # Contribution guidelines
├── requirements.txt       # Python dependencies
├── README_OLD.md          # Old C++ docs (deprecated)
└── DOCUMENTATION_INDEX.md # This file
```

## Documentation by Topic

### Installation & Setup

- [QUICKSTART.md](QUICKSTART.md) - Fast installation (recommended)
- [README.md](README.md) - Detailed installation instructions
- [requirements.txt](requirements.txt) - Python package dependencies

### Architecture & Design

- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete system architecture
  - Package structure
  - Design patterns
  - Threading model
  - Communication patterns
  - UI architecture

### API Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - Full API reference
  - Core classes (RobotController, SettingsManager)
  - Controllers (Winch, Wheel, Lidar, etc.)
  - Handlers (SteamDeck, Emergency, Heartbeat)
  - Services (VideoStream, WorkFlow, ScreenRecorder)
  - Models and Widgets
  - QML integration

### Features & Usage

- [README.md](README.md) - Feature overview and usage
  - Control modes
  - Video streaming
  - System monitoring
  - Emergency stop
  - Configuration

- [WORKFLOWS.md](WORKFLOWS.md) - Workflow automation
  - YAML format
  - Action types
  - Examples
  - Best practices

### Development

- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
  - Development setup
  - Code style
  - Testing
  - Pull request process

- [ARCHITECTURE.md](ARCHITECTURE.md) - Extending the system
  - Adding controllers
  - Creating handlers
  - New workflow actions
  - Custom widgets

### Troubleshooting

- [QUICKSTART.md](QUICKSTART.md) - Common first-run issues
- [README.md](README.md) - Detailed troubleshooting section
- [WORKFLOWS.md](WORKFLOWS.md) - Workflow-specific issues

## Document Sizes

| Document | Size | Lines | Description |
|----------|------|-------|-------------|
| README.md | 16 KB | ~620 | Main documentation |
| ARCHITECTURE.md | 22 KB | ~840 | Architecture guide |
| API_REFERENCE.md | 25 KB | ~1200 | API reference |
| WORKFLOWS.md | 16 KB | ~730 | Workflow guide |
| QUICKSTART.md | 10 KB | ~480 | Quick start |
| CONTRIBUTING.md | 12 KB | ~570 | Contributing guide |
| README_OLD.md | 6 KB | ~200 | Old C++ docs |

**Total Documentation**: ~107 KB, ~4640 lines

## Reading Paths

### Path 1: New User (Minimum)

1. [QUICKSTART.md](QUICKSTART.md) - Get running fast
2. [README.md](README.md) - Understand the features
3. [WORKFLOWS.md](WORKFLOWS.md) - Learn automation (optional)

**Time**: ~30-45 minutes

### Path 2: Developer (Comprehensive)

1. [README.md](README.md) - Overview
2. [QUICKSTART.md](QUICKSTART.md) - Setup
3. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
4. [API_REFERENCE.md](API_REFERENCE.md) - API details
5. [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines

**Time**: ~2-3 hours

### Path 3: Automation Focus

1. [QUICKSTART.md](QUICKSTART.md) - Get running
2. [WORKFLOWS.md](WORKFLOWS.md) - Workflow system
3. [API_REFERENCE.md](API_REFERENCE.md) - WorkFlowRunner API (section)

**Time**: ~1 hour

## External Resources

### ROS 2 Documentation

- [ROS 2 Humble Documentation](https://docs.ros.org/en/humble/)
- [rclpy API](https://docs.ros2.org/latest/api/rclpy/)

### Qt/PySide6 Documentation

- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [Qt Quick/QML](https://doc.qt.io/qt-6/qtquick-index.html)

### Python Resources

- [Python 3.10+ Documentation](https://docs.python.org/3/)
- [PEP 8 Style Guide](https://pep8.org/)

## Maintenance

### Documentation Updates

When updating code, remember to update relevant documentation:

- **New features** → Update README.md, API_REFERENCE.md
- **API changes** → Update API_REFERENCE.md
- **New workflow actions** → Update WORKFLOWS.md
- **Architecture changes** → Update ARCHITECTURE.md
- **Installation changes** → Update README.md, QUICKSTART.md

### Documentation Standards

All documentation should:

- Use clear, concise language
- Include code examples
- Provide context and rationale
- Link to related sections
- Be kept up-to-date with code

## Getting Help

If documentation is unclear or missing:

1. **Search** existing issues on GitHub
2. **Open an issue** describing what's unclear
3. **Submit a PR** to improve documentation
4. **Ask** in GitHub Discussions

## Version Information

- **Documentation Version**: 1.0
- **Paint Controller Version**: 0.1.0
- **Python Version**: 3.10+
- **ROS 2 Version**: Humble or later
- **Last Updated**: December 2024

## License

All documentation is licensed under Apache License 2.0, same as the code.

---

**Maintainer**: c3spray_deck (hychowah@gmail.com)

**Note**: The C++ version documentation (README_OLD.md) is preserved for historical reference only. All active development focuses on the Python version.
