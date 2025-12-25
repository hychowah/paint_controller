# Contributing to Paint Controller

Thank you for your interest in contributing to Paint Controller! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)
- [Communication](#communication)

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Ubuntu 22.04 or later
- ROS 2 Humble or later
- Python 3.10+
- Git
- Basic knowledge of:
  - Python programming
  - ROS 2 concepts
  - Qt/QML (for UI contributions)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   cd ~/ros2_workspace/src
   git clone https://github.com/YOUR_USERNAME/paint_controller.git
   cd paint_controller
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/hychowah/paint_controller.git
   ```

## Development Setup

### Install Dependencies

```bash
# System dependencies
sudo apt update
sudo apt install -y \
    libhidapi-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    pkg-config \
    python3-pip

# Python dependencies
pip3 install -r requirements.txt

# Install in development mode
pip3 install -e .
```

### Set Up Development Environment

```bash
# Source ROS 2
source /opt/ros/humble/setup.bash

# Build workspace
cd ~/ros2_workspace
colcon build --packages-select paint_controller_ros2

# Source workspace
source install/setup.bash
```

### Verify Installation

```bash
# Run the application
python3 -m paint_controller

# Or use ROS 2 run
ros2 run paint_controller_ros2 paint_controller
```

## Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with the following specifics:

- **Line length**: 100 characters (soft limit), 120 (hard limit)
- **Indentation**: 4 spaces
- **Quotes**: Single quotes for strings (except docstrings)
- **Docstrings**: Google-style docstrings

### Code Formatting

Use `black` for automatic formatting:

```bash
# Install black
pip3 install black

# Format your code
black python/paint_controller/

# Check without modifying
black --check python/paint_controller/
```

### Linting

Use `flake8` for linting:

```bash
# Install flake8
pip3 install flake8

# Run linter
flake8 python/paint_controller/
```

### Type Hints

Use type hints for all function signatures:

```python
def process_data(value: float, name: str = "default") -> dict:
    """Process data and return result."""
    return {"value": value, "name": name}
```

### Example Code Style

```python
"""Module for controlling the winch system."""

from typing import Optional, List
from PySide6.QtCore import QObject, Signal, Property
from rclpy.node import Node


class WinchController(QObject):
    """Controls winch positioning and movement.
    
    This class provides an interface between the Qt UI and ROS 2
    winch control system. It publishes movement commands and
    subscribes to position feedback.
    
    Attributes:
        position: Current winch position in millimeters
        is_moving: Whether the winch is currently moving
    """
    
    # Qt signals
    position_changed = Signal()
    is_moving_changed = Signal()
    
    def __init__(self, robot_controller: Node):
        """Initialize the winch controller.
        
        Args:
            robot_controller: ROS 2 node for communication
        """
        super().__init__()
        self._robot_controller = robot_controller
        self._position = 0.0
        self._is_moving = False
        self._setup_ros()
    
    def _setup_ros(self) -> None:
        """Set up ROS 2 publishers and subscribers."""
        # Implementation here
        pass
    
    @Property(float, notify=position_changed)
    def position(self) -> float:
        """Get current winch position in millimeters."""
        return self._position
```

## Making Changes

### Branching Strategy

1. Create a feature branch from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. Make your changes with clear, focused commits

3. Keep your branch up to date:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

### Commit Messages

Write clear, descriptive commit messages:

```
Add winch position limits validation

- Add min/max position configuration
- Validate positions before sending commands
- Add unit tests for validation logic
- Update documentation

Fixes #123
```

Format:
- First line: Short summary (50 chars or less)
- Blank line
- Detailed description (wrap at 72 chars)
- Reference issues/PRs at the end

### What to Contribute

We welcome contributions in these areas:

#### New Features
- Hardware controller support
- UI improvements
- Workflow actions
- Safety features
- Documentation

#### Bug Fixes
- Fix reported issues
- Improve error handling
- Fix memory leaks
- Performance improvements

#### Documentation
- API documentation
- User guides
- Examples
- Code comments

#### Testing
- Unit tests
- Integration tests
- Test coverage improvements

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_winch_controller.py

# Run with coverage
pytest --cov=paint_controller --cov-report=html
```

### Writing Tests

Create tests in the `tests/` directory:

```python
"""Tests for WinchController."""

import pytest
from paint_controller.controllers.winch import WinchController


class MockNode:
    """Mock ROS 2 node for testing."""
    
    def create_publisher(self, msg_type, topic, qos):
        return MockPublisher()
    
    def create_subscription(self, msg_type, topic, callback, qos):
        return MockSubscription()


def test_winch_initialization():
    """Test winch controller initialization."""
    node = MockNode()
    controller = WinchController(node)
    
    assert controller.position == 0.0
    assert controller.is_moving is False


def test_move_absolute():
    """Test absolute position movement."""
    node = MockNode()
    controller = WinchController(node)
    
    controller.move_absolute(1000.0, 100.0)
    
    # Add assertions
    assert controller.target_position == 1000.0
```

### Test Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests independent and isolated

## Submitting Changes

### Before Submitting

1. **Update documentation**
   - Update README.md if needed
   - Add/update docstrings
   - Update API_REFERENCE.md for new classes

2. **Run tests**
   ```bash
   pytest
   ```

3. **Check code style**
   ```bash
   black --check python/paint_controller/
   flake8 python/paint_controller/
   ```

4. **Test manually**
   - Run the application
   - Test your changes thoroughly
   - Test on target platform if possible

### Creating a Pull Request

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Go to GitHub and create a Pull Request

3. Fill out the PR template:
   - **Title**: Clear, concise description
   - **Description**: 
     - What changes were made
     - Why they were made
     - How to test them
   - **Related Issues**: Link related issues

4. Example PR description:
   ```markdown
   ## Changes
   - Add position limits to winch controller
   - Add configuration for min/max positions
   - Add validation before movement commands
   
   ## Why
   Prevents winch from moving beyond safe limits, addressing safety
   concerns raised in issue #123.
   
   ## Testing
   1. Configure position limits in settings
   2. Try to move beyond limits
   3. Verify command is rejected with warning
   
   Closes #123
   ```

### Code Review Process

1. **Automated checks**: CI will run tests and linting
2. **Maintainer review**: A maintainer will review your code
3. **Address feedback**: Make requested changes
4. **Approval**: Once approved, your PR will be merged

### After Merging

1. Delete your feature branch:
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. Update your main branch:
   ```bash
   git checkout main
   git pull upstream main
   ```

## Project Structure

Understanding the project structure helps with contributions:

```
paint_controller/
├── python/paint_controller/    # Main Python package
│   ├── core/                   # Core application
│   ├── controllers/            # Hardware controllers
│   ├── handlers/               # Event handlers
│   ├── services/               # Services (video, workflow)
│   ├── ui/                     # UI controllers
│   ├── widgets/                # Custom widgets
│   ├── models/                 # Data models
│   ├── qml/                    # QML UI files
│   └── resource/               # Resources (workflows, etc.)
├── src/                        # C++ code (deprecated)
├── tests/                      # Test files
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── config/                     # Configuration files
└── setup.py                    # Python package setup
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture information.

## Areas for Contribution

### High Priority

1. **Testing**: Increase test coverage
2. **Documentation**: Improve examples and guides
3. **Bug Fixes**: Address open issues
4. **Performance**: Optimize slow operations

### Feature Ideas

1. **New Hardware Support**
   - Additional sensor types
   - New actuator controllers
   - Camera integrations

2. **UI Enhancements**
   - New visualization widgets
   - Improved settings panel
   - Custom themes

3. **Workflow System**
   - New action types
   - Conditional logic
   - Loop support
   - Workflow templates

4. **Safety Features**
   - Collision detection
   - Automatic safety checks
   - Redundant emergency stops

5. **Monitoring**
   - Advanced diagnostics
   - Performance metrics
   - Historical data logging

## Communication

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Email**: Contact maintainers directly for private matters

### Reporting Bugs

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Exact steps to trigger the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - OS version
   - ROS 2 version
   - Python version
   - Relevant hardware
6. **Logs**: Error messages and stack traces
7. **Screenshots**: If applicable

Example bug report:

```markdown
## Bug: Winch controller crashes on large position values

### Description
Application crashes when sending position > 10000mm to winch controller.

### Steps to Reproduce
1. Start paint_controller
2. Navigate to winch control
3. Enter position value 15000
4. Click "Move"

### Expected Behavior
Should either move to position or show error if out of range.

### Actual Behavior
Application crashes with segmentation fault.

### Environment
- Ubuntu 22.04
- ROS 2 Humble
- Python 3.10.6
- Paint Controller v0.1.0

### Logs
```
[ERROR] [winch_controller]: Position value out of range
Segmentation fault (core dumped)
```

### Screenshots
[Attached]
```

### Suggesting Features

When suggesting features:

1. **Use Case**: Why is this needed?
2. **Description**: What should it do?
3. **Alternatives**: Other ways to achieve the goal?
4. **Implementation**: Ideas for how to implement?

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Give and accept constructive feedback
- Focus on what's best for the project
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Unprofessional conduct

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search closed issues
3. Open a new discussion
4. Contact maintainers

## Thank You!

Your contributions help make Paint Controller better for everyone. We appreciate your time and effort!

---

**Maintainer**: c3spray_deck (hychowah@gmail.com)

**Last Updated**: December 2024
