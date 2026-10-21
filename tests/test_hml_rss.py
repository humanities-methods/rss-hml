from unittest.mock import patch
from xml.etree import ElementTree

from hml_rss import (
    build_feed,
    fetch_all_articles,
    fetch_text_body,
    parse_journal_issues,
    parse_project_articles,
)


JOURNAL_API_RESPONSE = {
    "data": [
        {
            "id": "3d645582-2b7d-4ff6-8c63-e72872e86961",
            "type": "journals",
            "attributes": {
                "title": "Humanities Methods in Librarianship",
                "slug": "hml",
                "slugs": ["hml"],
            },
            "relationships": {
                "recentJournalIssues": {
                    "data": [
                        {"id": "issue-0-id", "type": "journalIssues"},
                        {"id": "issue-1-id", "type": "journalIssues"},
                    ]
                }
            },
        }
    ],
    "included": [
        {
            "id": "issue-0-id",
            "type": "journalIssues",
            "attributes": {
                "number": "0",
                "projectId": "proj-0-id",
                "projectSlug": "hml-no-0",
                "publicationDate": "2025-10-01",
                "creatorNames": "",
            },
        },
        {
            "id": "issue-1-id",
            "type": "journalIssues",
            "attributes": {
                "number": "1",
                "projectId": "proj-1-id",
                "projectSlug": "hml-no-1",
                "publicationDate": "2026-02-26",
                "creatorNames": "",
            },
        },
        {
            "id": "other-journal-issue",
            "type": "journalIssues",
            "attributes": {
                "number": "LIV",
                "projectId": "proj-other",
                "projectSlug": "other-journal-no-liv",
                "publicationDate": "2025-12-01",
                "creatorNames": "",
            },
        },
    ],
}


def test_parse_journal_issues_returns_list():
    issues = parse_journal_issues(JOURNAL_API_RESPONSE)
    assert len(issues) == 2


def test_parse_journal_issues_extracts_fields():
    issues = parse_journal_issues(JOURNAL_API_RESPONSE)
    assert issues[0]["number"] == "0"
    assert issues[0]["project_id"] == "proj-0-id"
    assert issues[0]["project_slug"] == "hml-no-0"
    assert issues[1]["number"] == "1"


PROJECT_API_RESPONSE = {
    "data": {
        "id": "proj-0-id",
        "type": "projects",
        "attributes": {
            "title": "Humanities Methods in Librarianship, no. 0",
            "slug": "hml-no-0",
        },
        "relationships": {
            "texts": {
                "data": [
                    {"id": "text-1", "type": "texts"},
                    {"id": "text-2", "type": "texts"},
                    {"id": "text-3", "type": "texts"},
                ]
            },
            "resources": {
                "data": [
                    {"id": "res-1", "type": "resources"},
                ]
            },
            "textCategories": {
                "data": [
                    {"id": "cat-editorial", "type": "textCategories"},
                    {"id": "cat-front", "type": "textCategories"},
                ]
            },
        },
    },
    "included": [
        {
            "id": "cat-editorial",
            "type": "textCategories",
            "attributes": {"title": "Editorial", "position": 1},
        },
        {
            "id": "cat-front",
            "type": "textCategories",
            "attributes": {"title": "Front matter", "position": 2},
        },
        {
            "id": "text-1",
            "type": "texts",
            "attributes": {
                "title": "Editorial, Issue 0",
                "slug": "editorial-issue-0",
                "published": True,
                "creatorNames": "Jane Doe",
                "createdAt": "2025-10-01T00:00:00.000Z",
                "position": 1,
            },
            "relationships": {
                "category": {"data": {"id": "cat-editorial", "type": "textCategories"}}
            },
        },
        {
            "id": "text-2",
            "type": "texts",
            "attributes": {
                "title": "Editorial Board",
                "slug": "masthead",
                "published": True,
                "creatorNames": "",
                "createdAt": "2025-10-01T00:00:00.000Z",
                "position": 1,
            },
            "relationships": {
                "category": {"data": {"id": "cat-front", "type": "textCategories"}}
            },
        },
        {
            "id": "text-3",
            "type": "texts",
            "attributes": {
                "title": "Submissions",
                "slug": "submissions",
                "published": False,
                "creatorNames": "",
                "createdAt": "2025-10-01T00:00:00.000Z",
                "position": 3,
            },
            "relationships": {
                "category": {"data": {"id": "cat-front", "type": "textCategories"}}
            },
        },
        {
            "id": "res-1",
            "type": "resources",
            "attributes": {
                "title": "Article 1",
                "titlePlaintext": "Article 1",
                "slug": "article-1",
                "kind": "pdf",
                "creatorNames": "",
                "attachmentFileName": "100.pdf",
                "downloadable": True,
                "createdAt": "2025-10-27T00:00:00.000Z",
            },
        },
    ],
}


def test_parse_project_articles_includes_published_texts():
    articles = parse_project_articles(PROJECT_API_RESPONSE, issue_number="0")
    titles = [a["title"] for a in articles]
    assert "Editorial, Issue 0" in titles


def test_parse_project_articles_excludes_unpublished_texts():
    articles = parse_project_articles(PROJECT_API_RESPONSE, issue_number="0")
    titles = [a["title"] for a in articles]
    assert "Submissions" not in titles


def test_parse_project_articles_excludes_resources():
    articles = parse_project_articles(PROJECT_API_RESPONSE, issue_number="0")
    titles = [a["title"] for a in articles]
    assert "Article 1" not in titles


def test_parse_project_articles_has_correct_urls():
    articles = parse_project_articles(PROJECT_API_RESPONSE, issue_number="0")
    text_article = next(a for a in articles if a["title"] == "Editorial, Issue 0")
    assert text_article["url"] == "https://cuny.manifoldapp.org/read/editorial-issue-0"


def test_parse_project_articles_includes_issue_number():
    articles = parse_project_articles(PROJECT_API_RESPONSE, issue_number="0")
    assert all(a["issue_number"] == "0" for a in articles)


TEXT_SECTIONS_RESPONSE = {
    "data": [
        {
            "id": "section-1",
            "type": "textSections",
            "attributes": {
                "name": "Editorial, Issue 0",
                "kind": "section",
            },
        }
    ],
}

TEXT_SECTION_DETAIL_RESPONSE = {
    "data": {
        "id": "section-1",
        "type": "textSections",
        "attributes": {
            "name": "Editorial, Issue 0",
            "body": "<p>This is the <em>full text</em> of the editorial.</p>",
        },
    },
}


def test_fetch_text_body_returns_html():
    def fake_get(url, **kwargs):
        class FakeResp:
            def raise_for_status(self):
                pass

        resp = FakeResp()
        if url.endswith("/text_sections"):
            resp.json = lambda: TEXT_SECTIONS_RESPONSE
        else:
            resp.json = lambda: TEXT_SECTION_DETAIL_RESPONSE
        return resp

    with patch("hml_rss.requests.get", side_effect=fake_get):
        body = fetch_text_body("text-1")
        assert "<p>This is the <em>full text</em> of the editorial.</p>" in body


def test_fetch_text_body_joins_multiple_sections():
    multi_sections = {
        "data": [
            {"id": "sec-1", "type": "textSections", "attributes": {"name": "Part 1", "kind": "section"}},
            {"id": "sec-2", "type": "textSections", "attributes": {"name": "Part 2", "kind": "section"}},
        ],
    }

    def fake_get(url, **kwargs):
        class FakeResp:
            def raise_for_status(self):
                pass

        resp = FakeResp()
        if url.endswith("/text_sections"):
            resp.json = lambda: multi_sections
        elif "sec-1" in url:
            resp.json = lambda: {
                "data": {"id": "sec-1", "type": "textSections", "attributes": {"body": "<p>Part one.</p>"}},
            }
        else:
            resp.json = lambda: {
                "data": {"id": "sec-2", "type": "textSections", "attributes": {"body": "<p>Part two.</p>"}},
            }
        return resp

    with patch("hml_rss.requests.get", side_effect=fake_get):
        body = fetch_text_body("text-1")
        assert "<p>Part one.</p>" in body
        assert "<p>Part two.</p>" in body


def test_build_feed_includes_content():
    articles = [
        {
            "title": "Editorial, Issue 0",
            "url": "https://cuny.manifoldapp.org/read/editorial-issue-0",
            "author": "Jane Doe",
            "date": "2025-10-01T00:00:00.000Z",
            "issue_number": "0",
            "body": "<p>Full text here.</p>",
        },
    ]
    xml_bytes = build_feed(articles)
    root = ElementTree.fromstring(xml_bytes)
    item = root.findall("channel/item")[0]
    desc = item.find("description").text
    assert "<p>Full text here.</p>" in desc


SAMPLE_ARTICLES = [
    {
        "title": "Editorial, Issue 0",
        "url": "https://cuny.manifoldapp.org/read/editorial-issue-0",
        "author": "Jane Doe",
        "date": "2025-10-01T00:00:00.000Z",
        "issue_number": "0",
    },
    {
        "title": "Editorial Board",
        "url": "https://cuny.manifoldapp.org/read/masthead",
        "author": "",
        "date": "2025-10-01T00:00:00.000Z",
        "issue_number": "0",
    },
]


def test_build_feed_returns_valid_xml():
    xml_bytes = build_feed(SAMPLE_ARTICLES)
    root = ElementTree.fromstring(xml_bytes)
    assert root.tag == "rss"


def test_build_feed_has_channel_info():
    xml_bytes = build_feed(SAMPLE_ARTICLES)
    root = ElementTree.fromstring(xml_bytes)
    channel = root.find("channel")
    assert channel is not None
    assert "Humanities Methods" in channel.find("title").text


def test_build_feed_has_items():
    xml_bytes = build_feed(SAMPLE_ARTICLES)
    root = ElementTree.fromstring(xml_bytes)
    items = root.findall("channel/item")
    assert len(items) == 2


def test_build_feed_item_has_title_and_link():
    xml_bytes = build_feed(SAMPLE_ARTICLES)
    root = ElementTree.fromstring(xml_bytes)
    items = root.findall("channel/item")
    titles = [item.find("title").text for item in items]
    assert "Editorial, Issue 0 (Issue 0)" in titles
    links = [item.find("link").text for item in items]
    assert any("editorial-issue-0" in link for link in links)


def test_build_feed_empty_articles():
    xml_bytes = build_feed([])
    root = ElementTree.fromstring(xml_bytes)
    items = root.findall("channel/item")
    assert len(items) == 0


def test_fetch_all_articles_calls_api_for_each_issue():
    """fetch_all_articles should hit the journal API, then each issue's project API."""

    def fake_get(url, **kwargs):
        class FakeResp:
            def raise_for_status(self):
                pass

        resp = FakeResp()
        if "journals" in url:
            resp.json = lambda: JOURNAL_API_RESPONSE
        elif "text_sections" in url and "/" in url.split("text_sections")[1]:
            resp.json = lambda: {
                "data": {
                    "id": "sec-1",
                    "type": "textSections",
                    "attributes": {"body": "<p>Body text.</p>"},
                },
            }
        elif "text_sections" in url:
            resp.json = lambda: {
                "data": [
                    {"id": "sec-1", "type": "textSections", "attributes": {"name": "Section 1"}},
                ],
            }
        elif "projects" in url:
            resp.json = lambda: PROJECT_API_RESPONSE
        return resp

    with patch("hml_rss.requests.get", side_effect=fake_get) as mock_get:
        articles = fetch_all_articles()
        assert len(articles) > 0
        assert all("body" in a for a in articles)
