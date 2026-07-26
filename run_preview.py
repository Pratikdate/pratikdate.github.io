import os
import shutil
import http.server
import socketserver
import re
import glob
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

preview_dir = '/tmp/blog_preview'
if os.path.exists(preview_dir):
    shutil.rmtree(preview_dir)
os.makedirs(preview_dir)
os.makedirs(os.path.join(preview_dir, '_blogs'), exist_ok=True)

# Copy assets
if os.path.exists(os.path.join(preview_dir, 'assets')):
    shutil.rmtree(os.path.join(preview_dir, 'assets'))
shutil.copytree('assets', os.path.join(preview_dir, 'assets'))

# Read layouts
with open('_layouts/default.html') as f:
    layout = f.read().replace('{{ site.baseurl }}', '').replace('{{ page.title | default: site.name }}', "Pratik's Blogs")

with open('_layouts/blog.html') as f:
    blog_layout = f.read().replace('{{ site.baseurl }}', '')
    blog_layout = re.sub(r'---.*?---', '', blog_layout, flags=re.DOTALL)

# Parse all markdown files
blogs = []
for md_file in glob.glob('_blogs/*.md'):
    with open(md_file) as f:
        content = f.read()
    
    # Extract frontmatter
    frontmatter_match = re.match(r'---\n(.*?)\n---', content, flags=re.DOTALL)
    title = "Untitled"
    date_str = "2026-01-01"
    
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        for line in fm.split('\n'):
            if line.startswith('title:'):
                title = line.split('title:')[1].strip().strip('"').strip("'")
            if line.startswith('date:'):
                date_str = line.split('date:')[1].strip()
                
    body = content[frontmatter_match.end():] if frontmatter_match else content
    excerpt = body.strip().split('\n\n')[0][:100] + "..."
    
    try:
        import markdown
        body_html = markdown.markdown(body, extensions=['fenced_code'])
    except ImportError:
        # Fallback to simple parser if markdown not installed
        body_html = ""
        for par in body.split('\n\n'):
            par = par.strip()
            if not par: continue
            if par.startswith('### '):
                body_html += f"<h3>{par[4:]}</h3>\n"
            elif par.startswith('```'):
                body_html += f"<pre><code>{par}</code></pre>\n"
            elif par.startswith('* '):
                body_html += f"<ul><li>{par[2:]}</li></ul>\n"
            else:
                body_html += f"<p>{par}</p>\n"
            
    slug = os.path.basename(md_file).replace('.md', '.html')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    blogs.append({
        'title': title,
        'date_str': date_str,
        'date_obj': date_obj,
        'date_formatted': date_obj.strftime('%b %-d, %Y'),
        'excerpt': excerpt,
        'slug': slug,
        'body_html': body_html
    })

# Sort by date descending (and then by filename descending to match Jekyll's reverse sort)
blogs.sort(key=lambda x: (x['date_obj'], x['slug']), reverse=True)

# Generate index.html
with open('index.html') as f:
    index_content = f.read()
index_content = re.sub(r'---.*?---', '', index_content, flags=re.DOTALL).replace('{{ site.baseurl }}', '')

mock_blogs_html = ""
for b in blogs:
    mock_blogs_html += f'''
    <a class="post-row slide-up" href="/_blogs/{b['slug']}">
        <div class="card-header">
            <span class="post-pill">Essay</span>
            <time class="card-date" datetime="{b['date_str']}">{b['date_formatted']}</time>
        </div>
        <div class="post-copy">
            <h2>{b['title']}</h2>
            <p>{b['excerpt']}</p>
            <div class="read-meta">
                <span class="read-link">Read article <span class="arrow">&rarr;</span></span>
            </div>
        </div>
    </a>
    '''



index_content = re.sub(r'{% assign sorted_blogs = site.blogs \| sort: \'date\' \| reverse %}\n\s*{% for blog in sorted_blogs %}.*?{% endfor %}', mock_blogs_html, index_content, flags=re.DOTALL)
final_index = layout.replace('{{ content }}', index_content)
with open(os.path.join(preview_dir, 'index.html'), 'w') as f:
    f.write(final_index)

# Generate individual blog pages
for b in blogs:
    post_html = blog_layout.replace('{{ content }}', b['body_html'])
    post_html = post_html.replace('{{ page.title | default: page.name }}', b['title'])
    post_html = re.sub(r'{% if page.date %}.*?{% endif %}', f'<time class="blog-date">{b["date_formatted"]}</time>', post_html, flags=re.DOTALL)
    
    final_post = layout.replace('{{ content }}', post_html).replace('{{ page.title | default: site.name }}', b['title'])
    with open(os.path.join(preview_dir, '_blogs', b['slug']), 'w') as f:
        f.write(final_post)

# Serve it
os.chdir(preview_dir)
PORT = 8098
print("Serving at port", PORT)
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
