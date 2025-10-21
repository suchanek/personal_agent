#!/usr/bin/env python3
import re
import sys
import os

if len(sys.argv) < 2:
    print("Usage: python3 md2html_mermaid.py <input.md> [output.html]")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.md', '.html')

with open(input_file, 'r') as f:
    content = f.read()

# Convert mermaid code blocks to divs that mermaid.js can render
def replace_mermaid(match):
    code = match.group(1)
    return f'<div class="mermaid">\n{code}\n</div>'

content = re.sub(r'```mermaid\n(.*?)\n```', replace_mermaid, content, flags=re.DOTALL)

# Basic markdown conversions
content = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
content = re.sub(r'^\- (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)
content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)

# Paragraphs
lines = content.split('\n')
result = []
in_list = False
for line in lines:
    if line.strip().startswith('<li>'):
        if not in_list:
            result.append('<ul>')
            in_list = True
        result.append(line)
    else:
        if in_list:
            result.append('</ul>')
            in_list = False
        result.append(line)
if in_list:
    result.append('</ul>')

content = '\n'.join(result)

html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{os.path.basename(input_file).replace('.md', '')}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default'
        }});
    </script>
    <style>
        body {{ max-width: 1000px; margin: 40px auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 1px solid #bdc3c7; padding-bottom: 8px; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; }}
        h4 {{ color: #95a5a6; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; font-size: 0.9em; }}
        ul {{ margin: 10px 0 10px 20px; }}
        li {{ margin: 5px 0; }}
        .mermaid {{ background: #fafafa; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0; border-radius: 5px; }}
        strong {{ color: #2c3e50; }}
        @media print {{
            body {{ margin: 0; padding: 20px; }}
            .mermaid {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
{content}
</body>
</html>'''

with open(output_file, 'w') as f:
    f.write(html)

print(f"Created {output_file}")
