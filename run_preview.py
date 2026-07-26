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

# Generate index.html (About page)
with open('index.html') as f:
    index_content = f.read()
index_content = re.sub(r'---.*?---', '', index_content, flags=re.DOTALL).replace('{{ site.baseurl }}', '')

mock_recent_blogs_html = ""
for b in blogs[:2]:
    slug_name = b['slug'].replace('.html', '')
    mock_recent_blogs_html += f'''
    <a class="post-row" href="/blog/{slug_name}/">
        <div class="card-header">
            <span class="post-pill">Essay</span>
            <time class="card-date" datetime="{b['date_str']}">{b['date_formatted']}</time>
        </div>
        <div class="post-copy">
            <h2>{b['title']}</h2>
            <p>{b['excerpt']}</p>
            <div class="read-meta">
                <span class="read-link">Read essay <span class="arrow">&rarr;</span></span>
            </div>
        </div>
    </a>
    '''

index_content = re.sub(r'{% assign sorted_blogs = site.blogs \| sort: \'date\' \| reverse %}\s*{% for blog in sorted_blogs limit:2 %}.*?{% endfor %}', mock_recent_blogs_html, index_content, flags=re.DOTALL)
final_index = layout.replace('{{ content }}', index_content).replace('{% if page.url == \'/\' or page.url == \'/index.html\' %}active{% endif %}', 'active').replace('{% if page.url contains \'/blog\' %}active{% endif %}', '')
with open(os.path.join(preview_dir, 'index.html'), 'w') as f:
    f.write(final_index)

# Generate blog/index.html (Blog page)
os.makedirs(os.path.join(preview_dir, 'blog'), exist_ok=True)
with open('blog/index.html') as f:
    blog_index_content = f.read()
blog_index_content = re.sub(r'---.*?---', '', blog_index_content, flags=re.DOTALL).replace('{{ site.baseurl }}', '')

mock_all_blogs_html = ""
for b in blogs:
    slug_name = b['slug'].replace('.html', '')
    mock_all_blogs_html += f'''
    <a class="post-row slide-up" href="/blog/{slug_name}/">
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

blog_index_content = re.sub(r'{% assign sorted_blogs = site.blogs \| sort: \'date\' \| reverse %}\s*{% for blog in sorted_blogs %}.*?{% endfor %}', mock_all_blogs_html, blog_index_content, flags=re.DOTALL)
final_blog_index = layout.replace('{{ content }}', blog_index_content).replace('{% if page.url == \'/\' or page.url == \'/index.html\' %}active{% endif %}', '').replace('{% if page.url contains \'/blog\' %}active{% endif %}', 'active')
with open(os.path.join(preview_dir, 'blog', 'index.html'), 'w') as f:
    f.write(final_blog_index)

# Generate individual blog pages at both /blog/<slug>/index.html and /_blogs/<slug>.html
for b in blogs:
    post_html = blog_layout.replace('{{ content }}', b['body_html'])
    post_html = post_html.replace('{{ page.title | default: page.name }}', b['title'])
    post_html = re.sub(r'{% if page.date %}.*?{% endif %}', f'<time class="blog-date">{b["date_formatted"]}</time>', post_html, flags=re.DOTALL)
    
    final_post = layout.replace('{{ content }}', post_html).replace('{{ page.title | default: site.name }}', b['title']).replace('{% if page.url contains \'/blog\' %}active{% endif %}', 'active').replace('{% if page.url == \'/\' or page.url == \'/index.html\' %}active{% endif %}', '')
    
    slug_name = b['slug'].replace('.html', '')
    # Save to /blog/<slug_name>/index.html
    post_dir = os.path.join(preview_dir, 'blog', slug_name)
    os.makedirs(post_dir, exist_ok=True)
    with open(os.path.join(post_dir, 'index.html'), 'w') as f:
        f.write(final_post)
        
    # Save to /_blogs/<slug>.html for fallback
    with open(os.path.join(preview_dir, '_blogs', b['slug']), 'w') as f:
        f.write(final_post)

# Serve it
os.chdir(preview_dir)
socketserver.TCPServer.allow_reuse_address = True

PORT = 8098
while True:
    try:
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", PORT), Handler)
        print(f"Serving preview at http://localhost:{PORT}")
        httpd.serve_forever()
        break
    except OSError:
        PORT += 1
