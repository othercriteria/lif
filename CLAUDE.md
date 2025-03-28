# CLAUDE.md - Lif Project Guidelines

## Build and Run Commands
- Install: `./setup.py install`
- Run: `lif.py [width] [height] [options]`
- Help: `lif.py -h`
- Profiling: `lif.py -timing`
- Profiling without I/O: `lif.py -blind [generations]`

## Code Style Guidelines
- Python compatibility: Support 2.7.9+ and 3.4.3+
- Imports: Group standard library imports first, third-party imports second
- Formatting: 4-space indentation, no trailing whitespace
- Naming: snake_case for variables/functions, CamelCase for classes
- Error handling: Use appropriate exception handling where needed
- Types: Use docstrings for function parameter types when appropriate
- Parameters: Use argparse with defaults and help text for command-line parameters
- Documentation: Use markdown for external documentation, inline comments for complex logic
- Model parameters: Store configuration in dictionary at module level
- Visualization: Use curses for terminal-based visualization