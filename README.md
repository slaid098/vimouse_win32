# ViMouse for Windows

A Vim-style mouse control application using keyboard shortcuts for Windows.

> This is a Windows-specific implementation inspired by [garywill/vimouse](https://github.com/garywill/vimouse). While the original project was created for Linux, I decided to create something similar for Windows users. Special thanks to @garywill for the original idea and implementation!

## Requirements

- Windows 10 or higher
- Python 3.9+

## Installation

### Automatic Installation (Recommended)

1. Download and extract the archive or clone the repository:
```bash
git clone https://github.com/slaid098/vimouse_win32.git
cd vimouse_win32
```

2. Run `setup.bat`

The installer will automatically:
- Check for Python installation
- Install all required dependencies using uv
- Create a desktop shortcut
- Add the application to Windows startup

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vimouse_win32.git
cd vimouse_win32
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install uv:
```bash
pip install uv
```

4. Install dependencies:
```bash
uv pip install -e .
```

5. To run:
```bash
python main.py
```

## Usage

After installation, the application will:
- Start automatically with Windows
- Be accessible via desktop shortcut

### Keyboard Shortcuts

[Describe your application's main keyboard shortcuts here]

## Uninstallation

1. Remove the desktop shortcut
2. Remove the startup shortcut (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ViMouse.lnk`)
3. Delete the application folder

## Development

For development:

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install development dependencies:
```bash
uv pip install -e ".[dev]"
```

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## License

Copyright (c) 2024 Sergey (slaid098)

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

Like the original [garywill/vimouse](https://github.com/garywill/vimouse) project, we use GPL-3.0 to ensure that all modifications and improvements remain open source and available to the community. 