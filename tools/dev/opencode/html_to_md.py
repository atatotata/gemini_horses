"""
Fix the corrupted MD file by regenerating it from the intact HTML.
Strategy: Read the HTML, extract text section by section, format as Markdown.
"""
import re
import html as html_mod

with open(r'G:\Downloads\Documents\go-model-benchmarks.html', 'r', encoding='utf-8-sig') as f:
    content = f.read()

def strip_tags(text):
    """Remove HTML tags, keeping text content with MD formatting."""
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    text = re.sub(r'<s>(.*?)</s>', r'~~\1~~', text, flags=re.DOTALL)
    text = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    return text.strip()

def table_to_md(table_html):
    """Convert HTML table to Markdown table."""
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    if not rows:
        return ''
    md_rows = []
    for row in rows:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)
        cleaned = [strip_tags(c).replace('\n', ' ').replace('|', '\\|').strip() for c in cells]
        if cleaned:
            md_rows.append('| ' + ' | '.join(cleaned) + ' |')
    if len(md_rows) < 2:
        return '\n'.join(md_rows)
    ncols = max(c.count('|') - 1 for c in md_rows) if md_rows else 0
    sep = '|' + '|'.join(['---'] * ncols) + '|'
    return md_rows[0] + '\n' + sep + '\n' + '\n'.join(md_rows[1:])

def process_details(html_block, indent=''):
    """Process a <details> block into MD."""
    results = []
    # Find all details blocks
    for match in re.finditer(r'<details>(.*?)</details>', html_block, re.DOTALL):
        inner = match.group(1)
        # Extract summary
        sum_match = re.search(r'<summary>(.*?)</summary>', inner, re.DOTALL)
        summary = strip_tags(sum_match.group(1)) if sum_match else ''
        results.append(f'\n<details>\n<summary><strong>{summary}</strong></summary>\n')
        # Extract content after summary
        content_after = inner[sum_match.end():] if sum_match else inner
        results.append(process_content(content_after, indent=''))
        results.append('\n</details>\n')
    return '\n'.join(results)

def process_content(html_block, indent=''):
    """Process content HTML into MD."""
    results = []
    
    # Process tables
    for table_match in re.finditer(r'<div class="table-wrap">\s*<table>(.*?)</table>\s*</div>', html_block, re.DOTALL):
        md_table = table_to_md(table_match.group(1))
        if md_table:
            results.append(f'\n{md_table}\n')
    
    # Process note boxes
    for note_match in re.finditer(r'<div class="note-box">(.*?)</div>', html_block, re.DOTALL):
        text = strip_tags(note_match.group(1))
        results.append(f'\n> **{text}**\n')
    
    # Process paragraphs
    for p_match in re.finditer(r'<p[^>]*>(.*?)</p>', html_block, re.DOTALL):
        text = strip_tags(p_match.group(1))
        if text:
            results.append(f'\n{text}\n')
    
    # Process blockquotes
    for bq_match in re.finditer(r'<blockquote[^>]*>(.*?)</blockquote>', html_block, re.DOTALL):
        text = strip_tags(bq_match.group(1))
        results.append(f'\n> {text}\n')
    
    # Process unordered lists
    for ul_match in re.finditer(r'<ul[^>]*>(.*?)</ul>', html_block, re.DOTALL):
        items = re.findall(r'<li[^>]*>(.*?)</li>', ul_match.group(1), re.DOTALL)
        for item in items:
            text = strip_tags(item)
            results.append(f'- {text}\n')
    
    return '\n'.join(results)

# Extract main content
main_match = re.search(r'<main>(.*?)</main>', content, re.DOTALL)
if not main_match:
    print("ERROR: No <main> tag found")
    exit(1)
main = main_match.group(1)

# Split into sections
sections = re.split(r'<!-- ============ (.*?) ============ -->', main)

output = []

# Header
output.append('# OpenCode Go Model Benchmarks \u2014 Complete Reference (Updated Sep 3, 2026)\n')

# Extract header paragraph
header_match = re.search(r'<header>(.*?)</header>', content, re.DOTALL)
if header_match:
    header = header_match.group(1)
    p_match = re.search(r'<p>(.*?)</p>', header, re.DOTALL)
    if p_match:
        output.append(f'\n{strip_tags(p_match.group(1))}\n')

output.append('\n**Legend:** \\* = vendor-reported only | ^ = scored as predecessor model | ? = anomalous/conflicting | TB = Terminal-Bench | AA = Artificial Analysis Intelligence Index | \u2014 = no data | n/r = not ranked | 0731 = DeepSeek V4 Flash re-post-train (Jul 31, 2026)\n')
output.append('\n---\n')

# Process each section
i = 0
while i < len(sections):
    section = sections[i]
    if i + 1 < len(sections):
        section_name = sections[i + 1]
        i += 2
    else:
        section_name = ''
        i += 1
    
    # Clean section name
    section_name = section_name.strip()
    
    # Process the section content
    if section_name:
        # Find h2 in section
        h2_match = re.search(r'<h2>(.*?)</h2>', section, re.DOTALL)
        if h2_match:
            h2_text = strip_tags(h2_match.group(1))
            output.append(f'\n## {h2_text}\n')
    
    # Process the content
    output.append(process_content(section))

# Write the output
md_text = '\n'.join(output)

# Clean up excessive newlines
md_text = re.sub(r'\n{4,}', '\n\n\n', md_text)

with open(r'G:\Downloads\Documents\go-model-benchmarks.md', 'w', encoding='utf-8') as f:
    f.write(md_text)

print(f"MD file regenerated: {len(md_text)} chars, {md_text.count(chr(10))} lines")
