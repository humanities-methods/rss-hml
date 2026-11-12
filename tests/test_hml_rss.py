from xml.etree import ElementTree

import pytest
import requests

from hml_rss import (
    build_feed,
    fetch_all_articles,
    fetch_text_body,
    main,
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


API = "https://cuny.manifoldapp.org/api/v1"
JOURNAL_URL = f"{API}/journals?filter[slug]=hml"
PROJECT_0_URL = f"{API}/projects/proj-0-id?include=texts,resources,textCategories"
PROJECT_1_URL = f"{API}/projects/proj-1-id?include=texts,resources,textCategories"

PROJECT_1_API_RESPONSE = {
    "data": {
        "id": "proj-1-id",
        "type": "projects",
        "attributes": {
            "title": "Humanities Methods in Librarianship, no. 1",
            "slug": "hml-no-1",
        },
        "relationships": {
            "texts": {"data": [{"id": "text-4", "type": "texts"}]},
            "resources": {"data": []},
            "textCategories": {"data": []},
        },
    },
    "included": [
        {
            "id": "text-4",
            "type": "texts",
            "attributes": {
                "title": "Reading the Catalog",
                "slug": "reading-the-catalog",
                "published": True,
                "creatorNames": "Sam Roe",
                "createdAt": "2026-02-26T00:00:00.000Z",
                "position": 1,
            },
        },
    ],
}


def sections_url(text_id):
    return f"{API}/texts/{text_id}/relationships/text_sections"


def add_text(api, text_id, bodies):
    """Register a text's section list and one detail response per section.

    bodies maps section id -> the section's attributes dict.
    """
    api.add(
        sections_url(text_id),
        {
            "data": [
                {"id": section_id, "type": "textSections", "attributes": {}}
                for section_id in bodies
            ]
        },
    )
    for section_id, attributes in bodies.items():
        api.add(
            f"{sections_url(text_id)}/{section_id}",
            {
                "data": {
                    "id": section_id,
                    "type": "textSections",
                    "attributes": attributes,
                }
            },
        )


def add_whole_journal(api):
    """Register every URL a full run needs: two issues, three published texts."""
    api.add(JOURNAL_URL, JOURNAL_API_RESPONSE)
    api.add(PROJECT_0_URL, PROJECT_API_RESPONSE)
    api.add(PROJECT_1_URL, PROJECT_1_API_RESPONSE)
    add_text(api, "text-1", {"sec-1a": {"body": "<p>Editorial body.</p>"}})
    add_text(api, "text-2", {"sec-2a": {"body": "<p>Board body.</p>"}})
    add_text(api, "text-4", {"sec-4a": {"body": "<p>Catalog body.</p>"}})


def test_fetch_text_body_returns_the_section_body(fake_api):
    add_text(fake_api, "text-1", {"sec-1": {"body": "<p>The <em>full</em> text.</p>"}})

    assert fetch_text_body("text-1") == "<p>The <em>full</em> text.</p>"


def test_fetch_text_body_joins_sections_in_order_with_newlines(fake_api):
    add_text(
        fake_api,
        "text-1",
        {
            "sec-b": {"body": "<p>Part one.</p>"},
            "sec-a": {"body": "<p>Part two.</p>"},
        },
    )

    assert fetch_text_body("text-1") == "<p>Part one.</p>\n<p>Part two.</p>"


def test_fetch_text_body_skips_sections_with_no_body(fake_api):
    add_text(
        fake_api,
        "text-1",
        {
            "sec-1": {"body": "<p>Part one.</p>"},
            "sec-2": {"body": ""},
            "sec-3": {"name": "No body attribute at all"},
            "sec-4": {"body": "<p>Part four.</p>"},
        },
    )

    assert fetch_text_body("text-1") == "<p>Part one.</p>\n<p>Part four.</p>"


def test_fetch_text_body_is_empty_for_a_text_with_no_sections(fake_api):
    add_text(fake_api, "text-1", {})

    assert fetch_text_body("text-1") == ""


def test_fetch_text_body_raises_when_the_section_list_request_fails(fake_api):
    fake_api.add(sections_url("text-1"), {"errors": ["boom"]}, status=500)

    with pytest.raises(requests.HTTPError):
        fetch_text_body("text-1")


def test_fetch_text_body_raises_when_a_section_request_fails(fake_api):
    add_text(fake_api, "text-1", {"sec-1": {"body": "<p>Part one.</p>"}})
    fake_api.add(f"{sections_url('text-1')}/sec-1", {"errors": ["boom"]}, status=404)

    with pytest.raises(requests.HTTPError):
        fetch_text_body("text-1")


def test_fetch_all_articles_returns_every_published_text_with_its_issue_and_body(
    fake_api,
):
    add_whole_journal(fake_api)

    assert fetch_all_articles() == [
        {
            "id": "text-1",
            "title": "Editorial, Issue 0",
            "url": "https://cuny.manifoldapp.org/read/editorial-issue-0",
            "author": "Jane Doe",
            "date": "2025-10-01T00:00:00.000Z",
            "issue_number": "0",
            "body": "<p>Editorial body.</p>",
        },
        {
            "id": "text-2",
            "title": "Editorial Board",
            "url": "https://cuny.manifoldapp.org/read/masthead",
            "author": "",
            "date": "2025-10-01T00:00:00.000Z",
            "issue_number": "0",
            "body": "<p>Board body.</p>",
        },
        {
            "id": "text-4",
            "title": "Reading the Catalog",
            "url": "https://cuny.manifoldapp.org/read/reading-the-catalog",
            "author": "Sam Roe",
            "date": "2026-02-26T00:00:00.000Z",
            "issue_number": "1",
            "body": "<p>Catalog body.</p>",
        },
    ]


def test_fetch_all_articles_does_not_fetch_bodies_of_unpublished_texts(fake_api):
    add_whole_journal(fake_api)

    fetch_all_articles()

    assert sections_url("text-3") not in fake_api.calls


def test_fetch_all_articles_is_empty_when_the_journal_has_no_issues(fake_api):
    fake_api.add(JOURNAL_URL, {"data": [], "included": []})

    assert fetch_all_articles() == []


@pytest.mark.parametrize(
    "failing_url",
    [JOURNAL_URL, PROJECT_1_URL],
    ids=["journal request", "project request"],
)
def test_fetch_all_articles_raises_when_a_request_fails(fake_api, failing_url):
    add_whole_journal(fake_api)
    fake_api.add(failing_url, {"errors": ["boom"]}, status=503)

    with pytest.raises(requests.HTTPError):
        fetch_all_articles()


def test_main_writes_the_feed_file_with_one_item_per_article(
    fake_api, tmp_path, monkeypatch
):
    add_whole_journal(fake_api)
    monkeypatch.chdir(tmp_path)

    main()

    root = ElementTree.parse(tmp_path / "hml_feed.xml").getroot()
    titles = sorted(item.find("title").text for item in root.findall("channel/item"))
    assert titles == [
        "Editorial Board (Issue 0)",
        "Editorial, Issue 0 (Issue 0)",
        "Reading the Catalog (Issue 1)",
    ]


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
