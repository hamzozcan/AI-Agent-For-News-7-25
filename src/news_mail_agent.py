from __future__ import annotations

import datetime as dt
import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable
from zoneinfo import ZoneInfo


AI_KEYWORDS = [
    "OpenAI",
    "Claude",
    "Anthropic",
    "DeepSeek",
    "Perplexity",
    "artificial intelligence",
    "yapay zeka",
]

STOCK_SYMBOLS = {
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC",
    "BIST 100": "XU100.IS",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "Alphabet": "GOOGL",
}


@dataclass
class Settings:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    from_email: str
    to_email: str
    newsapi_key: str
    timezone: str = "Europe/Istanbul"

    @classmethod
    def from_env(cls) -> "Settings":
        required = [
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USER",
            "SMTP_PASS",
            "FROM_EMAIL",
            "TO_EMAIL",
            "NEWSAPI_KEY",
        ]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"Eksik ortam değişkenleri: {', '.join(missing)}")

        return cls(
            smtp_host=os.environ["SMTP_HOST"],
            smtp_port=int(os.environ["SMTP_PORT"]),
            smtp_user=os.environ["SMTP_USER"],
            smtp_pass=os.environ["SMTP_PASS"],
            from_email=os.environ["FROM_EMAIL"],
            to_email=os.environ["TO_EMAIL"],
            newsapi_key=os.environ["NEWSAPI_KEY"],
            timezone=os.getenv("TIMEZONE", "Europe/Istanbul"),
        )


def get_newsapi_articles(api_key: str, query: str, page_size: int = 8) -> list[dict]:
    import requests

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": page_size,
        "apiKey": api_key,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("articles", [])


def get_rss_articles(limit: int = 6) -> list[dict]:
    import feedparser

    feeds = [
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    ]
    all_items: list[dict] = []
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:limit]:
            all_items.append(
                {
                    "title": entry.get("title", "Başlıksız"),
                    "url": entry.get("link", ""),
                    "source": {"name": parsed.feed.get("title", "RSS")},
                    "publishedAt": entry.get("published", ""),
                    "description": entry.get("summary", ""),
                }
            )
    return all_items


def clean_html(text: str) -> str:
    import re

    no_tags = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", no_tags).strip()


def get_stock_snapshot(symbols: dict[str, str]) -> list[tuple[str, float, float]]:
    import yfinance as yf

    output = []
    for name, ticker in symbols.items():
        data = yf.Ticker(ticker)
        hist = data.history(period="2d")
        if hist.empty:
            continue
        close = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[0])
        change_pct = ((close - prev) / prev) * 100 if prev else 0
        output.append((name, close, change_pct))
    return output


def deduplicate_articles(articles: Iterable[dict]) -> list[dict]:
    seen = set()
    unique = []
    for article in articles:
        title = article.get("title", "").strip().lower()
        url = article.get("url", "").strip().lower()
        key = (title, url)
        if not title or key in seen:
            continue
        seen.add(key)
        unique.append(article)
    return unique


def format_email_body(news: list[dict], stocks: list[tuple[str, float, float]], tz_name: str) -> str:
    now = dt.datetime.now(ZoneInfo(tz_name))
    lines = [
        f"Günlük AI + Piyasa Bülteni ({now:%d.%m.%Y %H:%M})",
        "=" * 50,
        "",
        "Öne Çıkan Haberler:",
    ]
    for idx, item in enumerate(news[:20], start=1):
        source = item.get("source", {}).get("name", "Bilinmeyen Kaynak")
        title = item.get("title", "Başlıksız")
        desc = clean_html(item.get("description", ""))[:220]
        url = item.get("url", "")
        lines.extend(
            [
                f"{idx}. {title}",
                f"   Kaynak: {source}",
                f"   Özet: {desc}",
                f"   Link: {url}",
                "",
            ]
        )

    lines.append("Piyasa Özeti:")
    for name, close, pct in stocks:
        emoji = "🟢" if pct >= 0 else "🔴"
        lines.append(f"- {name}: {close:.2f} ({emoji} {pct:+.2f}%)")

    lines.extend(
        [
            "",
            "Not: Bu mail otomatik olarak günlük üretilmiştir.",
            "İstersen bir sonraki adımda WhatsApp/Telegram bildirimi de ekleyebilirim.",
        ]
    )
    return "\n".join(lines)


def send_email(settings: Settings, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = settings.from_email
    msg["To"] = settings.to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_pass)
        server.sendmail(settings.from_email, [settings.to_email], msg.as_string())


def collect_news(settings: Settings) -> list[dict]:
    query = " OR ".join(f'"{k}"' for k in AI_KEYWORDS) + " AND (stocks OR market OR borsa)"
    primary = get_newsapi_articles(settings.newsapi_key, query=query, page_size=12)
    backup = get_rss_articles(limit=4)
    return deduplicate_articles(primary + backup)


def run() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    settings = Settings.from_env()
    news = collect_news(settings)
    stocks = get_stock_snapshot(STOCK_SYMBOLS)
    subject = f"Günlük AI + Borsa Haberleri | {dt.datetime.now(ZoneInfo(settings.timezone)):%d.%m.%Y}"
    body = format_email_body(news, stocks, settings.timezone)
    send_email(settings, subject, body)
    print("Mail başarıyla gönderildi.")


if __name__ == "__main__":
    run()
