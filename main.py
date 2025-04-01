import subprocess
import re
import os
from collections import defaultdict
from datetime import datetime

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

def extract_additions_with_dates(git_history):
    """Extract lines added with their dates from git history."""
    # Regular expressions to match commit dates and added lines
    date_pattern = re.compile(r"Date:\s+(.+)")
    addition_pattern = re.compile(r"^\+\s*(?!\+\+\+)(.+)$", re.MULTILINE)
    
    additions_with_dates = []
    current_date = None
    
    # Split git history by commits
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
                    # If date parsing fails, use a placeholder
                    current_date = None
        
        # Extract added lines
        if current_date:
            added_lines = addition_pattern.findall(commit)
            for line in added_lines:
                if line.strip() and not line.startswith("+++"):
                    additions_with_dates.append((line.strip(), current_date))
    
    return additions_with_dates

def parse_markdown_entries(md_file_path):
    """Parse the markdown file to extract entries with their headers."""
    try:
        with open(md_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split content by headers
        sections = {}
        current_section = "General"
        section_content = []
        
        lines = content.split("\n")
        for line in lines:
            if line.startswith("#"):
                # Save previous section
                if section_content:
                    sections[current_section] = section_content
                
                # Start new section
                current_section = line.strip()
                section_content = [line]
            else:
                section_content.append(line)
        
        # Save the last section
        if section_content:
            sections[current_section] = section_content
        
        return sections
    except Exception as e:
        print(f"Error parsing markdown file: {e}")
        return {}

def extract_links_with_content(md_content):
    """Extract markdown links with their surrounding content."""
    # Pattern to match markdown links: [text](url)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    links_with_content = []
    lines = md_content.split("\n")
    for line in lines:
        links = link_pattern.findall(line)
        for link_text, link_url in links:
            links_with_content.append({
                "link_text": link_text,
                "link_url": link_url,
                "full_line": line
            })
    
    return links_with_content

def match_additions_to_entries(additions_with_dates, md_content):
    """Match git additions to markdown entries and assign dates."""
    links = extract_links_with_content(md_content)
    entry_dates = {}
    
    # Create a set of additions for faster lookup
    additions_set = {addition[0] for addition in additions_with_dates}
    
    for link in links:
        # Try to find the exact line in additions
        if link["full_line"] in additions_set:
            # Find the date
            for addition, date in additions_with_dates:
                if addition == link["full_line"]:
                    entry_dates[link["full_line"]] = date
                    break
        else:
            # Try partial matching for lines that might have been modified
            for addition, date in additions_with_dates:
                if link["link_url"] in addition or link["link_text"] in addition:
                    entry_dates[link["full_line"]] = date
                    break
    
    return entry_dates

def generate_chronological_md(entry_dates, original_sections, output_file):
    """Generate a new markdown file with entries sorted chronologically."""
    # Extract all entries with dates
    all_entries = []
    for section_name, section_lines in original_sections.items():
        section_content = "\n".join(section_lines)
        links = extract_links_with_content(section_content)
        
        for link in links:
            if link["full_line"] in entry_dates:
                all_entries.append({
                    "date": entry_dates[link["full_line"]],
                    "content": link["full_line"],
                    "section": section_name
                })
    
    # Sort entries by date, newest first
    sorted_entries = sorted(all_entries, key=lambda x: x["date"] if x["date"] else datetime.min, reverse=True)
    
    # Write to output file
    with open(output_file, "w", encoding="utf-8") as f:
        # f.write("# Awesome Models - Chronological View\n\n")
        f.write("*Reordered by addition date, newest first*\n\n")
        
        current_month = None
        for entry in sorted_entries:
            if entry["date"]:
                entry_month = entry["date"].strftime("%B %Y")
                if entry_month != current_month:
                    current_month = entry_month
                    f.write(f"\n## {current_month}\n\n")
                
                section_name = entry["section"].replace("#", "").strip()
                f.write(f"- {entry['content']} *(from {section_name})*\n")
            
        f.write("\n\n*This file was automatically generated based on git history.*")
    
    print(f"Chronological markdown written to {output_file}")

def main():
    # Configure these variables for your repository
    repo_path = input("Enter the path to your local 'awesome-models' repository: ").strip()
    md_file = "README.md"
    output_file = "README_CHRONOLOGICAL.md"
    
    # Change to the repository directory
    original_dir = os.getcwd()
    os.chdir(repo_path)
    
    try:
        # Get git history
        print("Getting git history...")
        git_history = get_git_history(md_file)
        
        # Extract additions with dates
        print("Extracting additions...")
        additions_with_dates = extract_additions_with_dates(git_history)
        
        # Parse markdown file
        print("Parsing markdown file...")
        md_file_path = os.path.join(repo_path, md_file)
        original_sections = parse_markdown_entries(md_file_path)
        
        # Match additions to entries
        print("Matching additions to entries...")
        full_content = open(md_file_path, "r", encoding="utf-8").read()
        entry_dates = match_additions_to_entries(additions_with_dates, full_content)
        
        # Generate chronological markdown
        print("Generating chronological markdown...")
        output_file_path = os.path.join(repo_path, output_file)
        generate_chronological_md(entry_dates, original_sections, output_file_path)
        
        print("Done!")
    finally:
        # Return to the original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main()
