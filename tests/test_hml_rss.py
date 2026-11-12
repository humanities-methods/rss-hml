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


def journal(journal_id, attributes, relationships):
    return {
        "id": journal_id,
        "type": "journals",
        "attributes": attributes,
        "relationships": relationships,
    }


def issue_refs(*issue_ids):
    return {"data": [{"id": i, "type": "journalIssues"} for i in issue_ids]}


def included_issue(issue_id, number):
    return {
        "id": issue_id,
        "type": "journalIssues",
        "attributes": {
            "number": number,
            "projectId": f"proj-{number}",
            "projectSlug": f"slug-{number}",
            "publicationDate": "2025-01-01",
        },
    }


def issue_numbers(journal_response, **kwargs):
    return [i["number"] for i in parse_journal_issues(journal_response, **kwargs)]


def test_parse_journal_issues_extracts_each_issue_of_the_journal():
    assert parse_journal_issues(JOURNAL_API_RESPONSE) == [
        {
            "id": "issue-0-id",
            "number": "0",
            "project_id": "proj-0-id",
            "project_slug": "hml-no-0",
            "publication_date": "2025-10-01",
        },
        {
            "id": "issue-1-id",
            "number": "1",
            "project_id": "proj-1-id",
            "project_slug": "hml-no-1",
            "publication_date": "2026-02-26",
        },
    ]


def test_parse_journal_issues_finds_the_journal_by_slug_when_slugs_is_missing():
    response = {
        "data": [journal("j1", {"slug": "hml"}, {"journalIssues": issue_refs("a")})],
        "included": [included_issue("a", "7")],
    }

    assert issue_numbers(response) == ["7"]


def test_parse_journal_issues_finds_the_journal_by_a_former_slug():
    response = {
        "data": [
            journal(
                "j1",
                {"slug": "renamed", "slugs": ["renamed", "hml"]},
                {"journalIssues": issue_refs("a")},
            )
        ],
        "included": [included_issue("a", "7")],
    }

    assert issue_numbers(response) == ["7"]


def test_parse_journal_issues_ignores_other_journals_in_the_response():
    response = {
        "data": [
            journal("j1", {"slug": "other"}, {"journalIssues": issue_refs("a")}),
            journal("j2", {"slug": "hml"}, {"journalIssues": issue_refs("b")}),
        ],
        "included": [included_issue("a", "LIV"), included_issue("b", "7")],
    }

    assert issue_numbers(response) == ["7"]


def test_parse_journal_issues_is_empty_when_the_journal_is_not_in_the_response():
    response = {
        "data": [journal("j1", {"slug": "other"}, {"journalIssues": issue_refs("a")})],
        "included": [included_issue("a", "LIV")],
    }

    assert parse_journal_issues(response) == []


def test_parse_journal_issues_looks_up_the_slug_it_is_given():
    response = {
        "data": [
            journal("j1", {"slug": "hml"}, {"journalIssues": issue_refs("a")}),
            journal("j2", {"slug": "other"}, {"journalIssues": issue_refs("b")}),
        ],
        "included": [included_issue("a", "7"), included_issue("b", "LIV")],
    }

    assert issue_numbers(response, journal_slug="other") == ["LIV"]


def test_parse_journal_issues_prefers_the_full_issue_list_over_recent_issues():
    response = {
        "data": [
            journal(
                "j1",
                {"slug": "hml"},
                {
                    "journalIssues": issue_refs("a", "b"),
                    "recentJournalIssues": issue_refs("b"),
                },
            )
        ],
        "included": [included_issue("a", "1"), included_issue("b", "2")],
    }

    assert issue_numbers(response) == ["1", "2"]


def test_parse_journal_issues_is_empty_when_the_journal_has_no_relationships():
    response = {
        "data": [{"id": "j1", "type": "journals", "attributes": {"slug": "hml"}}],
        "included": [included_issue("a", "7")],
    }

    assert parse_journal_issues(response) == []


def test_parse_project_articles_returns_published_texts_only():
    assert parse_project_articles(PROJECT_API_RESPONSE, issue_number="0") == [
        {
            "id": "text-1",
            "title": "Editorial, Issue 0",
            "url": "https://cuny.manifoldapp.org/read/editorial-issue-0",
            "author": "Jane Doe",
            "date": "2025-10-01T00:00:00.000Z",
            "issue_number": "0",
        },
        {
            "id": "text-2",
            "title": "Editorial Board",
            "url": "https://cuny.manifoldapp.org/read/masthead",
            "author": "",
            "date": "2025-10-01T00:00:00.000Z",
            "issue_number": "0",
        },
    ]


def test_parse_project_articles_ignores_published_items_that_are_not_texts():
    response = {
        "included": [
            {
                "id": "r1",
                "type": "resources",
                "attributes": {"title": "A PDF", "slug": "a-pdf", "published": True},
            }
        ]
    }

    assert parse_project_articles(response) == []


def test_parse_project_articles_treats_a_text_without_a_published_flag_as_unpublished():
    response = {
        "included": [
            {"id": "t1", "type": "texts", "attributes": {"title": "T", "slug": "t"}}
        ]
    }

    assert parse_project_articles(response) == []


def test_parse_project_articles_defaults_missing_author_date_and_issue_to_blank():
    response = {
        "included": [
            {
                "id": "t1",
                "type": "texts",
                "attributes": {"title": "T", "slug": "t", "published": True},
            }
        ]
    }

    assert parse_project_articles(response) == [
        {
            "id": "t1",
            "title": "T",
            "url": "https://cuny.manifoldapp.org/read/t",
            "author": "",
            "date": "",
            "issue_number": "",
        }
    ]


def test_parse_project_articles_is_empty_when_the_project_includes_nothing():
    assert parse_project_articles({"data": {"id": "p", "type": "projects"}}) == []


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


ARTICLE = {
    "id": "text-1",
    "title": "Editorial, Issue 0",
    "url": "https://cuny.manifoldapp.org/read/editorial-issue-0",
    "author": "Jane Doe",
    "date": "2025-10-01T00:00:00.000Z",
    "issue_number": "0",
    "body": "<p>Fish &amp; chips, <em>in full</em>.</p>",
}


def feed_items(articles):
    root = ElementTree.fromstring(build_feed(articles))
    return root.findall("channel/item")


def only_item(**changes):
    """Build a feed from ARTICLE with some fields changed; None removes a field."""
    article = {k: v for k, v in (ARTICLE | changes).items() if v is not None}
    (item,) = feed_items([article])
    return item


def test_build_feed_is_an_rss_document_describing_the_journal():
    root = ElementTree.fromstring(build_feed([ARTICLE]))

    assert root.tag == "rss"
    channel = root.find("channel")
    assert channel.find("title").text == "Humanities Methods in Librarianship"
    assert (
        channel.find("link").text == "https://cuny.manifoldapp.org/journals/hml/issues"
    )
    assert channel.find("language").text == "en"


def test_build_feed_has_no_items_when_there_are_no_articles():
    assert feed_items([]) == []


def test_build_feed_has_one_item_per_article():
    second = ARTICLE | {
        "title": "Editorial Board",
        "url": "https://cuny.manifoldapp.org/read/masthead",
    }

    links = sorted(item.find("link").text for item in feed_items([ARTICLE, second]))

    assert links == [
        "https://cuny.manifoldapp.org/read/editorial-issue-0",
        "https://cuny.manifoldapp.org/read/masthead",
    ]


def test_build_feed_lists_the_last_article_first():
    first = ARTICLE | {"title": "First", "issue_number": ""}
    second = ARTICLE | {"title": "Second", "issue_number": ""}
    third = ARTICLE | {"title": "Third", "issue_number": ""}

    titles = [item.find("title").text for item in feed_items([first, second, third])]

    assert titles == ["Third", "Second", "First"]


def test_build_feed_item_title_names_the_issue():
    assert only_item().find("title").text == "Editorial, Issue 0 (Issue 0)"


@pytest.mark.parametrize("issue_number", ["", None], ids=["blank", "missing"])
def test_build_feed_item_title_is_unchanged_without_an_issue_number(issue_number):
    item = only_item(issue_number=issue_number)

    assert item.find("title").text == "Editorial, Issue 0"


def test_build_feed_item_links_to_the_article():
    item = only_item()

    assert (
        item.find("link").text == "https://cuny.manifoldapp.org/read/editorial-issue-0"
    )


def test_build_feed_item_guid_is_the_article_url_as_a_permalink():
    guid = only_item().find("guid")

    assert guid.text == "https://cuny.manifoldapp.org/read/editorial-issue-0"
    assert guid.get("isPermaLink") == "true"


def test_build_feed_item_publication_date_comes_from_the_article_date():
    assert only_item().find("pubDate").text == "Wed, 01 Oct 2025 00:00:00 +0000"


@pytest.mark.parametrize("date", ["", None], ids=["blank", "missing"])
def test_build_feed_item_has_no_publication_date_without_an_article_date(date):
    assert only_item(date=date).find("pubDate") is None


def test_build_feed_item_description_is_the_article_body_html():
    description = only_item().find("description").text

    assert description == "<p>Fish &amp; chips, <em>in full</em>.</p>"


@pytest.mark.parametrize("body", ["", None], ids=["blank", "missing"])
def test_build_feed_item_has_no_description_without_a_body(body):
    assert only_item(body=body).find("description") is None


@pytest.mark.xfail(
    strict=True,
    reason="feedgen drops an RSS author that has a name but no email, "
    "so the author never reaches the feed outside the body text",
)
def test_build_feed_item_carries_the_author_name():
    item = only_item()

    outside_body = [el.text for el in item if el.tag != "description"]
    assert any("Jane Doe" in (text or "") for text in outside_body)
