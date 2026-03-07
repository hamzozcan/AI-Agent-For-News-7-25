# 7/24 AI Haber + Borsa Mail Ajanı

Bu proje, her gün otomatik olarak:

- OpenAI / Claude / DeepSeek / Perplexity ve genel yapay zeka haberlerini toplar,
- Borsa ve büyük piyasa göstergelerini (NASDAQ, S&P500, BIST100 vb.) çeker,
- Tek bir günlük bülten haline getirip belirlediğin mail adresine yollar.

## 1) Kurulum

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` dosyasına gönderen ve alıcı mail bilgilerini gir.

> Gmail kullanıyorsan normal şifre değil, **App Password** kullan.

## 2) Manuel test

```bash
python src/news_mail_agent.py
```

Başarılıysa terminalde `Mail başarıyla gönderildi.` görürsün.

## 3) 7/24 çalıştırma (Linux cron)

`crontab -e` aç ve aşağıdaki satırı ekle (her gün 09:00'da çalışır):

```cron
0 9 * * * cd /workspace/Hamza && /usr/bin/bash -lc 'source .venv/bin/activate && python src/news_mail_agent.py' >> /workspace/Hamza/agent.log 2>&1
```

## 4) Geliştirme/test

```bash
pytest -q
```

## Notlar

- Haber kaynağı olarak NewsAPI + RSS fallback kullanılır.
- Aynı haberleri tekilleştirir.
- İstersen ikinci adımda: Telegram/WhatsApp, PDF rapor, haftalık özet ve özel şirket filtreleri eklenebilir.
