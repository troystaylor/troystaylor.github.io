"""Generate a weekly digest of new blog posts and create a Brevo campaign draft."""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import frontmatter
import markdown
import requests

POSTS_DIR = os.path.join(os.path.dirname(__file__), "..", "_posts")
SITE_URL = "https://troystaylor.github.io"
FILENAME_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")


def get_recent_posts(days=7):
    """Return posts published within the last `days` days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    posts = []

    for filename in sorted(os.listdir(POSTS_DIR)):
        match = FILENAME_DATE_RE.match(filename)
        if not match:
            continue

        post_date = datetime.strptime(match.group(1), "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        if post_date < cutoff:
            continue

        filepath = os.path.join(POSTS_DIR, filename)
        post = frontmatter.load(filepath)
        title = post.get("title", match.group(2).replace("-", " ").title())
        categories = post.get("categories", [])

        # Build the permalink: /:categories/:year-:month-:day-:title.html
        slug = match.group(2)
        cat_path = "/".join(
            c.lower().replace(" ", "%20") for c in categories
        ) if categories else ""
        url = f"{SITE_URL}/{cat_path}/{match.group(1)}-{slug}.html"

        # Extract first ~150 words as summary
        content_text = post.content.strip()
        words = content_text.split()[:150]
        summary = " ".join(words)
        if len(content_text.split()) > 150:
            summary += "..."

        posts.append(
            {
                "title": title,
                "date": post_date.strftime("%B %d, %Y"),
                "url": url,
                "summary": summary,
                "categories": categories,
            }
        )

    return posts


def build_digest_markdown(posts):
    """Build a Markdown newsletter body from a list of posts."""
    lines = [
        "# Power Platform Integrations — Weekly Digest\n",
        f"*Week of {datetime.now(timezone.utc).strftime('%B %d, %Y')}*\n",
    ]

    for post in posts:
        lines.append(f"## [{post['title']}]({post['url']})\n")
        lines.append(f"*{post['date']}*\n")
        if post["categories"]:
            tags = ", ".join(post["categories"])
            lines.append(f"**Categories:** {tags}\n")
        lines.append(f"{post['summary']}\n")
        lines.append(f"[Read more]({post['url']})\n")
        lines.append("---\n")

    lines.append(
        f"\n*You received this because you subscribed to the "
        f"[Power Platform Integrations newsletter]({SITE_URL}).*\n"
    )

    return "\n".join(lines)


def build_html(md_content):
    """Convert Markdown to HTML with a simple wrapper."""
    body = markdown.markdown(md_content, extensions=["extra"])
    return (
        '<div style="max-width: 600px; margin: 0 auto; font-family: '
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; "
        'line-height: 1.6; color: #24292f;">'
        f"{body}"
        "</div>"
    )


def create_brevo_campaign(html_content, subject, api_key, list_id, sender_name, sender_email):
    """Create a scheduled Brevo email campaign (sends 24h later)."""
    send_at = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )

    payload = {
        "name": f"Weekly Digest - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "subject": subject,
        "sender": {"name": sender_name, "email": sender_email},
        "type": "classic",
        "htmlContent": html_content,
        "recipients": {"listIds": [int(list_id)]},
        "scheduledAt": send_at,
    }

    resp = requests.post(
        "https://api.brevo.com/v3/emailCampaigns",
        json=payload,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    campaign_id = resp.json().get("id")
    print(f"Campaign created (id: {campaign_id}), scheduled for {send_at}")
    return campaign_id


def main():
    parser = argparse.ArgumentParser(description="Generate weekly newsletter digest")
    parser.add_argument("--days", type=int, default=7, help="Look back N days for posts")
    parser.add_argument("--dry-run", action="store_true", help="Print digest without calling API")
    args = parser.parse_args()

    api_key = os.environ.get("BREVO_API_KEY", "")
    list_id = os.environ.get("BREVO_LIST_ID", "")
    sender_name = os.environ.get("BREVO_SENDER_NAME", "Power Platform Integrations")
    sender_email = os.environ.get("BREVO_SENDER_EMAIL", "")

    posts = get_recent_posts(days=args.days)

    if not posts:
        print("No new posts in the last {} days. Skipping digest.".format(args.days))
        sys.exit(0)

    print(f"Found {len(posts)} new post(s):")
    for p in posts:
        print(f"  - {p['title']} ({p['date']})")

    md_content = build_digest_markdown(posts)

    if args.dry_run:
        print("\n--- Markdown digest ---")
        print(md_content)
        print("\n--- HTML preview ---")
        print(build_html(md_content))
        return

    if not api_key or not list_id or not sender_email:
        print("Error: BREVO_API_KEY, BREVO_LIST_ID, and BREVO_SENDER_EMAIL must be set.")
        sys.exit(1)

    html_content = build_html(md_content)
    subject = f"Weekly Digest: {posts[0]['title']}"
    if len(posts) > 1:
        subject = f"Weekly Digest: {len(posts)} new posts"

    create_brevo_campaign(html_content, subject, api_key, list_id, sender_name, sender_email)


if __name__ == "__main__":
    main()
