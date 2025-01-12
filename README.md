## Description

A tool for generating Swift Package Manager (SPM) module dependency diagrams for iOS projects. The tool creates a visual representation of SPM module relationships that can be opened in draw.io.

## Prerequisites

- Python 3.8+
- git
- draw.io (recommended for viewing the generated diagram)

## Usage

### Option 1: Using Shell Script (Recommended)

```bash
# Basic usage
sh execute.sh --path /path/to/ios/project

# With additional options
sh execute.sh -p /path/to/ios/project -c

Or

sh execute.sh --path /path/to/ios/project --cached
```

#### Shell Script Options

- `--path` or `-p`: Path to iOS project
- `--cached` or `-c`: Use only cached versions (skip remote requests)

### Option 2: Direct Python Execution

```bash
# Create and activate virtual environment
python3 -m venv venv_spm_generator
source venv_spm_generator/bin/activate
```

```bash
# Basic usage
python3 main.py --path /path/to/ios/project

# With additional options
python3 main.py -p /path/to/ios/project -c

Or

python3 main.py --path /path/to/ios/project --cached
```

#### Python Script Options

- `--path` or `-p`: Path to iOS project
- `--cached` or `-c`: Use only cached versions (skip remote requests)

## Output

The script generates a .drawio diagram file in the project directory showing SPM module dependencies.

## Notes

If no path is provided, the script will prompt for a project path
The tool creates a virtual environment to manage dependencies

## License

[...]
