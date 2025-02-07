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

## Dependency Analysis

The project includes functionality to analyze the update status of dependencies, both for Swift Package Manager and CocoaPods.

### Generate Dependencies Report

To generate a detailed report of the dependencies status:

```bash
sh execute.sh --path /path/to/project --dependencies-only

Of 

python3 main.py --path /path/to/project --dependencies-only
```

This will generate a JSON file in the results directory containing information about all dependencies, including:

Current version
Latest available version
Update status:

- 🟢 Up to date
- 🔴 Major version difference
- 🟡 Minor or patch difference
- ⚫ Status not determined

## Notes

If no path is provided, the script will prompt for a project path
The tool creates a virtual environment to manage dependencies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
