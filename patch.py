import re

with open('main.py', 'r') as f:
    content = f.read()

with open('index.html', 'r') as f:
    html = f.read()

# Replace HTML_UI = '''...''' with new HTML_UI
new_content = re.sub(r"HTML_UI = '''(.*?)'''", f"HTML_UI = '''{html}'''", content, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(new_content)
