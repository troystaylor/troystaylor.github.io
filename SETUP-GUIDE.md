# Jekyll Blog Setup - Next Steps

Your blog structure has been created! Here's what to do next:

## ✅ What's Been Created

```
troystaylor.github.io/
├── .github/workflows/
│   └── pages-deploy.yml      # GitHub Actions workflow for auto-deployment
├── _posts/
│   └── 2026-01-07-welcome.md # Your first blog post
├── _config.yml               # Jekyll site configuration
├── Gemfile                   # Ruby dependencies
├── .gitignore                # Git ignore rules
├── index.md                  # Homepage
├── README.md                 # Documentation
└── LICENSE                   # Existing license file
```

## 📋 Next Steps

### Option 1: Deploy Directly to GitHub (Recommended)

The easiest way is to push to GitHub and let GitHub Actions build it:

1. **Commit and push:**
   ```bash
   cd C:\Users\troytaylor\troystaylor.github.io
   git add .
   git commit -m "Initial Jekyll blog setup with jekyll-gitbook theme"
   git push origin main
   ```

2. **Enable GitHub Pages:**
   - Go to https://github.com/troystaylor/troystaylor.github.io/settings/pages
   - Under "Build and deployment"
   - Source: **GitHub Actions**
   - The workflow will automatically build and deploy

3. **Wait ~2 minutes** and visit: https://troystaylor.github.io

### Option 2: Test Locally First

If you want to preview locally before deploying:

1. **Install Ruby:**
   - Download from: https://rubyinstaller.org/downloads/
   - Choose Ruby+Devkit 3.3.x (x64)
   - Run installer and check "Add Ruby to PATH"

2. **Install Bundler:**
   ```bash
   gem install bundler
   ```

3. **Install dependencies:**
   ```bash
   cd C:\Users\troytaylor\troystaylor.github.io
   bundle install
   ```

4. **Run locally:**
   ```bash
   bundle exec jekyll serve
   ```

5. **Preview:**
   - Open http://localhost:4000

6. **When satisfied, push to GitHub** (see Option 1)

## 📝 Creating New Posts

To add new blog posts:

1. Create file in `_posts/` with format: `YYYY-MM-DD-title.md`
2. Add front matter:
   ```yaml
   ---
   title: Your Post Title
   author: Troy Taylor
   date: 2026-01-07
   category: Power Platform
   layout: post
   ---
   ```
3. Write your content in Markdown
4. Commit and push to deploy

## 🎨 Customization

Edit `_config.yml` to customize:
- Site title and description
- Your email address
- Google Analytics (optional)
- Disqus comments (optional)
- Table of contents settings

## 🔧 Theme Features

The jekyll-gitbook theme includes:
- GitBook-style navigation
- Full-text search
- Syntax highlighting
- Table of contents
- Responsive design
- Emoji support (via jemoji)

See: https://github.com/sighingnow/jekyll-gitbook

## 📚 Useful Links

- **Your repo:** https://github.com/troystaylor/troystaylor.github.io
- **Jekyll docs:** https://jekyllrb.com/docs/
- **GitHub Pages:** https://docs.github.com/en/pages
- **Theme docs:** https://github.com/sighingnow/jekyll-gitbook

## 🎯 Recommended: Push to GitHub Now

The fastest way to see your blog live is to just push to GitHub:

```bash
cd C:\Users\troytaylor\troystaylor.github.io
git add .
git commit -m "Initial Jekyll blog setup with jekyll-gitbook theme"
git push origin main
```

Then go to your repo settings and enable GitHub Pages with "GitHub Actions" as the source!
