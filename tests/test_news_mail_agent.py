from src.news_mail_agent import deduplicate_articles, format_email_body


def test_deduplicate_articles():
    articles = [
        {"title": "OpenAI yeni model", "url": "https://a.com"},
        {"title": "OpenAI yeni model", "url": "https://a.com"},
        {"title": "DeepSeek güncelleme", "url": "https://b.com"},
    ]
    unique = deduplicate_articles(articles)
    assert len(unique) == 2


def test_format_email_body_contains_sections():
    news = [
        {
            "title": "Claude Enterprise haberi",
            "description": "<b>Önemli güncelleme</b>",
            "url": "https://example.com/news",
            "source": {"name": "Test Source"},
        }
    ]
    body = format_email_body(news, [("NASDAQ", 12345.67, 1.25)], "Europe/Istanbul")
    assert "Öne Çıkan Haberler" in body
    assert "Piyasa Özeti" in body
    assert "Claude Enterprise haberi" in body
