#### VibeCoded with machines of loving grace Claude Sonnet 3.7
# Git-Based Markdown Chronological Sorter

A robust tool that analyzes Git history to reorder markdown content chronologically based on when content was added to the repository.

## Purpose

This tool was motivated to easily see the most recent additions made to `awesome-topic` repos like [Awesome-Reasoning-Foundation-Models](https://github.com/reasoning-survey/Awesome-Reasoning-Foundation-Models), [Awesome-LLM-Reasoning](https://github.com/atfortes/Awesome-LLM-Reasoning) etc
This tool addresses a common problem with documentation repositories: content is typically organized thematically, making it difficult to track what's recently been added. By analyzing Git's commit history for a markdown file, this tool can:

1. Extract when each piece of content was first added to the repository
2. Reorganize all content chronologically by addition date
3. Group content by month/year and original section
4. Generate a new markdown file with this time-based ordering


## Features

- **Comprehensive content extraction**: Captures all content types (headers, list items, regular text)
- **Sophisticated matching algorithms**: Uses exact, normalized, and fuzzy matching to associate content with dates
- **Context-based inference**: Approximates dates for unmatched content based on surrounding dated items
- **Structure preservation**: Maintains original formatting and hierarchical relationships
- **Diagnostic reporting**: Provides matching statistics to evaluate performance

## Installation

### Prerequisites

- Python 3.7+
- Git

### Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a fast, reliable Python package installer and resolver written in Rust.

```bash
# Install uv if you don't have it already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/naveenreddy61/repo-readme-chronological-sorter.git
cd repo-readme-chronological-sorter

# Create a virtual environment and install dependencies using uv and sync using lock file
uv sync
```

## Usage

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the script
python main.py

OR
#using uv
uv run main.py
```


The script will prompt you for:
1. The path to your local repository
2. The markdown file to analyze (defaults to README.md)
3. The output file name (defaults to README_CHRONOLOGICAL.md)

Example:
```
Enter the path to your local repository: /path/to/your/repo
Enter the markdown file name (default: README.md): CONTRIBUTING.md
Enter the output file name (default: README_CHRONOLOGICAL.md): CHRONOLOGICAL_VIEW.md
```

## How It Works

The tool operates in several distinct phases:

1. **Git History Extraction**: Retrieves the complete commit history with line-by-line changes for the specified file using `git log -p --follow`.

2. **Content Dating**: Parses the git history to identify when each line was first added, creating a mapping between content and dates.

3. **Markdown Parsing**: Analyzes the markdown file to extract all meaningful content while preserving structural context (headers, list items, text) and hierarchical relationships.

4. **Content Matching**: Uses a multi-stage approach to match current content with dated content from the git history:
   - Direct exact matching (fastest, most reliable)
   - Normalized matching (handles whitespace variations)
   - Fuzzy matching with similarity scoring (handles minor edits)
   - Special link detection (boosts similarity for URL matches)
   - Contextual date inference (uses surrounding content dates when no match found)

5. **Chronological Reorganization**: Groups dated content by month/year and original section, then generates a new markdown file with this time-based ordering.

## Technical Architecture

```
main.py
├── get_git_history() - Retrieves raw git history for specified file
├── extract_content_with_dates() - Extracts content with commit dates
├── parse_markdown_content() - Analyzes markdown structure
├── match_content_to_dates() - Associates content with addition dates
└── generate_chronological_md() - Creates chronologically ordered output
```

## Examples

### Input: Thematically organized README.md
```markdown
# Project Title

## Installation
Instructions for installation...

## Features
- Feature 1 added recently
- Feature 2 added long ago
- Feature 3 added somewhat recently

## Configuration
Configuration information...
```

### Output: Chronologically organized README_CHRONOLOGICAL.md
```markdown
# Chronological Content

*Reordered by addition date, newest first*

## March 2024

### From 'Features'
- Feature 1 added recently

### From 'Configuration'
Configuration information...

## January 2024

### From 'Features'
- Feature 3 added somewhat recently

## October 2023

### From 'Installation'
Instructions for installation...

### From 'Features'
- Feature 2 added long ago
```

## Troubleshooting

### Common Issues

1. **Low match rate**: If your matching statistics show a low percentage (< 70%), consider:
   - Content may have been significantly edited since original addition
   - The repository might have a complex merge history
   - The file might have been renamed or moved multiple times

2. **Git history errors**: Ensure you're running the script from a valid git repository and the file has been committed.

3. **Character encoding issues**: The script uses UTF-8 encoding. If your markdown contains unusual characters, you may need to modify the encoding parameters.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.