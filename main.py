import subprocess
import re
import os
from collections import defaultdict
from datetime import datetime
import difflib

def get_git_history(file_path):
    """Get the Git history for a specific file."""
    try:
        # Get the full git log with line changes for the specific file
        cmd = ["git", "log", "-p", "--follow", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error getting git history: {e}")
        return ""

def extract_content_with_dates(git_history):
    """Extract all content lines with their addition dates from git history."""
    # Regular expressions to match commit dates and added lines
    date_pattern = re.compile(r"Date:\s+(.+)")
    addition_pattern = re.compile(r"^\+\s*(?!\+\+\+)(.+)$", re.MULTILINE)
    
    # Store lines with their earliest addition date
    content_dates = {}
    current_date = None
    
    # Split git history by commits (newest first)
    commits = git_history.split("commit ")
    for commit in commits:
        if not commit.strip():
            continue
            
        # Extract date
        date_match = date_pattern.search(commit)
        if date_match:
            date_str = date_match.group(1).strip()
            try:
                # Parse the git date format
                current_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y %z")
            except ValueError:
                try:
                    # Alternative date format
                    current_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
                except ValueError:
                    # If date parsing fails, use None
                    current_date = None
        
        # Extract added lines
        if current_date:
            added_lines = addition_pattern.findall(commit)
            for line in added_lines:
                line = line.strip()
                # Skip empty lines and diff markers
                if line and not line.startswith("+++"):
                    # Store only the earliest date a line was added (since we're iterating from newest to oldest)
                    if line not in content_dates:
                        content_dates[line] = current_date
    
    return content_dates

def parse_markdown_content(md_file_path):
    """Parse the markdown file to extract all content with structure preservation."""
    try:
        with open(md_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split into lines for processing
        lines = content.split("\n")
        
        # Extract all meaningful content lines with their structural context
        content_items = []
        current_section = "General"
        current_subsection = None
        in_list = False
        list_level = 0
        
        for i, line in enumerate(lines):
            line_content = line.strip()
            
            # Skip empty lines
            if not line_content:
                continue
                
            # Track headers (sections)
            if line_content.startswith("#"):
                header_level = len(re.match(r'^#+', line_content).group())
                header_text = line_content.lstrip("#").strip()
                
                if header_level == 1:
                    current_section = header_text
                    current_subsection = None
                else:
                    current_subsection = header_text
                
                # Add header as content item
                content_items.append({
                    "content": line_content,
                    "section": current_section,
                    "subsection": current_subsection if header_level > 1 else None,
                    "type": "header",
                    "level": header_level,
                    "line_number": i
                })
            
            # Track list items
            elif line_content.startswith(("-", "*", "+")) or re.match(r'^\d+\.', line_content):
                in_list = True
                # Calculate list level based on indentation
                current_indent = len(line) - len(line.lstrip())
                list_level = current_indent // 2
                
                content_items.append({
                    "content": line_content,
                    "section": current_section,
                    "subsection": current_subsection,
                    "type": "list_item",
                    "level": list_level,
                    "line_number": i
                })
            
            # Regular content
            else:
                in_list = False
                content_items.append({
                    "content": line_content,
                    "section": current_section,
                    "subsection": current_subsection,
                    "type": "text",
                    "line_number": i
                })
        
        return content_items
    except Exception as e:
        print(f"Error parsing markdown file: {e}")
        return []

def match_content_to_dates(content_items, content_dates):
    """Match markdown content to their git addition dates using fuzzy matching."""
    matched_items = []
    
    for item in content_items:
        # Direct match
        if item["content"] in content_dates:
            item["date"] = content_dates[item["content"]]
            matched_items.append(item)
            continue

        # Try fuzzy matching for items without direct matches
        best_match = None
        best_score = 0
        
        # Try to match with different normalization techniques
        normalized_content = re.sub(r'\s+', ' ', item["content"]).strip()
        
        for git_line, date in content_dates.items():
            normalized_git_line = re.sub(r'\s+', ' ', git_line).strip()
            
            # Check for exact match after normalization
            if normalized_content == normalized_git_line:
                best_match = git_line
                best_score = 1.0
                break
            
            # Compute similarity ratio for fuzzy matching
            similarity = difflib.SequenceMatcher(None, normalized_content, normalized_git_line).ratio()
            
            # If item contains a link, also try matching just the link portion
            if "[" in normalized_content and "](" in normalized_content:
                link_match = re.search(r'\[(.*?)\]\((.*?)\)', normalized_content)
                if link_match and link_match.group(2) in normalized_git_line:
                    # Boost similarity score for URL matches
                    similarity = max(similarity, 0.8)
            
            if similarity > 0.7 and similarity > best_score:  # 70% similarity threshold
                best_match = git_line
                best_score = similarity
        
        if best_match:
            item["date"] = content_dates[best_match]
            matched_items.append(item)
        else:
            # For items without any match, use context to infer date
            # (assign date based on surrounding content with known dates)
            context_dates = []
            context_range = 3  # Check 3 items before and after
            
            # Look for dated items before this one
            for i in range(1, context_range + 1):
                idx = item["line_number"] - i
                if idx >= 0 and idx < len(content_items):
                    context_item = content_items[idx]
                    if "date" in context_item and context_item["date"]:
                        context_dates.append(context_item["date"])
                        break
            
            # Look for dated items after this one
            for i in range(1, context_range + 1):
                idx = item["line_number"] + i
                if idx < len(content_items):
                    context_item = content_items[idx]
                    if "date" in context_item and context_item["date"]:
                        context_dates.append(context_item["date"])
                        break
            
            # Use the average date or nearest date as an approximation
            if context_dates:
                item["date"] = min(context_dates)  # Use the earliest date as an approximation
                item["date_inferred"] = True
                matched_items.append(item)
    
    return matched_items

def generate_chronological_md(sorted_content, output_file):
    """Generate a new markdown file with content sorted chronologically."""
    # Group items by month/year
    items_by_month = defaultdict(list)
    
    for item in sorted_content:
        if "date" in item and item["date"]:
            month_year = item["date"].strftime("%B %Y")
            items_by_month[month_year].append(item)
    
    # Sort months (newest first)
    sorted_months = sorted(items_by_month.keys(), 
                          key=lambda x: datetime.strptime(x, "%B %Y"), 
                          reverse=True)
    
    # Write to output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Chronological Content\n\n")
        f.write("*Reordered by addition date, newest first*\n\n")
        
        for month in sorted_months:
            f.write(f"\n## {month}\n\n")
            
            # Group items by section within each month
            section_items = defaultdict(list)
            for item in items_by_month[month]:
                section_items[item["section"]].append(item)
            
            # Write items grouped by section
            for section, items in section_items.items():
                # Write a miniature section header
                f.write(f"### From '{section}'\n\n")
                
                # Sort items by date (newest first) within the section
                items.sort(key=lambda x: x["date"], reverse=True)
                
                for item in items:
                    # Format based on item type
                    if item["type"] == "header":
                        # Skip writing section headers that we've already accounted for
                        continue
                    elif item["type"] == "list_item":
                        # Preserve list formatting
                        f.write(f"{item['content']}\n")
                    else:
                        # Regular text
                        f.write(f"{item['content']}\n")
                
                f.write("\n")
        
        f.write("\n\n*This file was automatically generated based on git history.*")
    
    print(f"Chronological markdown written to {output_file}")

def main():
    # Configure these variables for your repository
    repo_path = input("Enter the path to your local repository: ").strip()
    md_file = input("Enter the markdown file name (default: README.md): ").strip() or "README.md"
    output_file = input("Enter the output file name (default: README_CHRONOLOGICAL.md): ").strip() or "README_CHRONOLOGICAL.md"
    
    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)
    
    try:
        # Get git history
        print("Getting git history...")
        git_history = get_git_history(md_file)
        
        # Extract content with dates
        print("Extracting content with dates from git history...")
        content_dates = extract_content_with_dates(git_history)
        
        # Parse markdown file
        print("Parsing markdown file...")
        md_file_path = os.path.join(repo_path, md_file)
        content_items = parse_markdown_content(md_file_path)
        
        # Match content to dates
        print("Matching content to addition dates...")
        matched_items = match_content_to_dates(content_items, content_dates)
        
        # Sort matched items by date (newest first)
        sorted_content = sorted(
            matched_items, 
            key=lambda x: x.get("date", datetime.min), 
            reverse=True
        )
        
        # Generate chronological markdown
        print("Generating chronological markdown...")
        output_file_path = os.path.join(repo_path, output_file)
        generate_chronological_md(sorted_content, output_file_path)
        
        # Report statistics
        total_items = len(content_items)
        matched_items_count = len(matched_items)
        match_rate = (matched_items_count / total_items) * 100 if total_items > 0 else 0
        
        print(f"\nMatching Statistics:")
        print(f"Total content items: {total_items}")
        print(f"Items with dates matched: {matched_items_count} ({match_rate:.1f}%)")
        
        print("\nDone!")
    finally:
        # Return to the original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()