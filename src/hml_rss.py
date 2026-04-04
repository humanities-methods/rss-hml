"""Generate an RSS feed from the CUNY Manifold HML journal API."""

from datetime import datetime, timezone

import requests
from feedgen.feed import FeedGenerator

BASE_URL = "https://cuny.manifoldapp.org"
API_URL = f"{BASE_URL}/api/v1"
JOURNAL_SLUG = "hml"


def parse_journal_issues(journal_response, journal_slug=JOURNAL_SLUG):
    """Extract issue info from the journal API response, filtered to the target journal."""
    journal_data = None
    for j in journal_response["data"]:
        slugs = j["attributes"].get("slugs", [])
        slug = j["attributes"].get("slug", "")
        if journal_slug in slugs or slug == journal_slug:
            journal_data = j
            break
    if journal_data is None:
        return []

    rels = journal_data.get("relationships", {})
    issue_rel = rels.get("journalIssues") or rels.get("recentJournalIssues", {})
    issue_ids = {rel["id"] for rel in issue_rel.get("data", [])}

    included = journal_response.get("included", [])
    issues = []
    for item in included:
        if item["type"] == "journalIssues" and item["id"] in issue_ids:
            attrs = item["attributes"]
            issues.append(
                {
                    "id": item["id"],
                    "number": attrs.get("number"),
                    "project_id": attrs.get("projectId"),
                    "project_slug": attrs.get("projectSlug"),
                    "publication_date": attrs.get("publicationDate"),
                }
            )
    return issues


def parse_project_articles(project_response, issue_number=""):
    """Extract published texts from a project API response."""
    included = project_response.get("included", [])
    articles = []

    for item in included:
        if item["type"] == "texts":
            attrs = item["attributes"]
            if not attrs.get("published", False):
                continue
            articles.append(
                {
                    "title": attrs["title"],
                    "url": f"{BASE_URL}/read/{attrs['slug']}",
                    "author": attrs.get("creatorNames", ""),
                    "date": attrs.get("createdAt", ""),
                    "issue_number": issue_number,
                }
            )

    return articles


def build_feed(articles):
    """Build an RSS feed from a list of article dicts."""
    fg = FeedGenerator()
    fg.title("Humanities Methods in Librarianship")
    fg.link(href=f"{BASE_URL}/journals/{JOURNAL_SLUG}/issues")
    fg.description(
        "Articles from Humanities Methods in Librarianship, "
        "a peer-reviewed open access journal published by CUNY."
    )
    fg.language("en")

    for article in articles:
        fe = fg.add_entry()
        title = article["title"]
        if article.get("issue_number"):
            title = f"{title} (Issue {article['issue_number']})"
        fe.title(title)
        fe.link(href=article["url"])
        fe.guid(article["url"], permalink=True)
        if article.get("author"):
            fe.author(name=article["author"])
        if article.get("date"):
            fe.pubDate(article["date"])

    return fg.rss_str(pretty=True)


def fetch_all_articles():
    """Fetch all articles from all HML journal issues via the Manifold API."""
    journal_url = f"{API_URL}/journals?filter[slug]={JOURNAL_SLUG}"
    resp = requests.get(journal_url)
    resp.raise_for_status()
    issues = parse_journal_issues(resp.json())

    all_articles = []
    for issue in issues:
        project_url = (
            f"{API_URL}/projects/{issue['project_id']}"
            "?include=texts,resources,textCategories"
        )
        resp = requests.get(project_url)
        resp.raise_for_status()
        articles = parse_project_articles(resp.json(), issue_number=issue["number"])
        all_articles.extend(articles)

    return all_articles


def main():
    """Fetch articles and write RSS feed to hml_feed.xml."""
    articles = fetch_all_articles()
    rss_xml = build_feed(articles)
    with open("hml_feed.xml", "wb") as f:
        f.write(rss_xml)
    print(f"Wrote {len(articles)} articles to hml_feed.xml")


if __name__ == "__main__":
    main()
