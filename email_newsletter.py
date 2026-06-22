import os
import smtplib
import html as h
import argparse
import time as time_module
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import pandas as pd
import plotly.graph_objects as go
import pdfkit
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# ================= DATABASE =================
# Set this in environment variables:
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://powerpost:p0werp0stAt2026@101.50.83.121:5432/powerpost")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# ================= FETCH NEWS FOR DATE RANGE =================
def fetch_news_by_theme_range(df, start_date, end_date):
    db = SessionLocal()
    theme_results = defaultdict(list)
    used_links = set()

    try:
        # 1. Fetch theme-based news
        for _, row in df.iterrows():
            theme = row["Theme"].strip()
            keyword = str(row["Keyword"]).strip()

            query = text("""
                SELECT DISTINCT ON (link)
                    title, link, sentiment, summary, article_date, source
                FROM news_articles
                WHERE tsv_content @@ plainto_tsquery('english', :kw)
                AND DATE(article_date AT TIME ZONE 'Asia/Karachi') BETWEEN :start_date AND :end_date
                AND (relevancy <> 'Other')
                ORDER BY link, article_date DESC
            """)

            rows = db.execute(
                query,
                {
                    "kw": keyword,
                    "start_date": start_date.date(),
                    "end_date": end_date.date()
                }
            ).fetchall()

            for r in rows:
                if r.link not in used_links:
                    theme_results[theme].append({
                        "title": r.title,
                        "source": r.source,
                        "link": r.link,
                        "sentiment": r.sentiment,
                        "summary": r.summary or ""
                    })
                    used_links.add(r.link)

        # 2. Fetch remaining relevant news
        other_query = text("""
            SELECT DISTINCT ON (link)
                title, link, sentiment, summary, article_date, source
            FROM news_articles
            WHERE DATE(article_date AT TIME ZONE 'Asia/Karachi') BETWEEN :start_date AND :end_date
              AND (relevancy <> 'Other')
            ORDER BY link, article_date DESC
        """)

        all_rows = db.execute(
            other_query,
            {
                "start_date": start_date.date(),
                "end_date": end_date.date()
            }
        ).fetchall()

        other_news = []

        for r in all_rows:
            if r.link not in used_links:
                other_news.append({
                    "title": r.title,
                    "source": r.source,
                    "link": r.link,
                    "sentiment": r.sentiment,
                    "summary": r.summary or ""
                })
                used_links.add(r.link)

        theme_results["Other"] = other_news

        # 3. Fetch social media posts
        social_media_query = text("""
            SELECT DISTINCT ON (url) *
            FROM social_media_posts
            WHERE DATE(created_at) BETWEEN :start_date AND :end_date
              AND relevancy <> 'Other'
            ORDER BY url, created_at DESC
        """)

        all_rows_sm = db.execute(
            social_media_query,
            {
                "start_date": start_date.date(),
                "end_date": end_date.date()
            }
        ).fetchall()

        social_media = []

        for r in all_rows_sm:
            if r.url not in used_links:
                social_media.append({
                    "title": r.author_name,
                    "source": r.platform,
                    "link": r.url,
                    "sentiment": r.sentiment,
                    "summary": r.content or ""
                })
                used_links.add(r.url)

        theme_results["Social_Media"] = social_media

        return theme_results

    finally:
        db.close()


# ================= GENERATE HTML =================
def generate_html(theme_results, start_date, end_date):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "amad.md")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found at: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    # Format report date
    if start_date.date() == end_date.date():
        report_date_str = start_date.strftime("%d %B %Y")
    else:
        report_date_str = f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %B %Y')}"

    html_template = html_template.replace("{{REPORT_DATE}}", report_date_str)

    placeholder_map = {
        "Net-metering": "NET_METERING",
        "Solarisation": "SOLARIZATION",
        "Privatisation": "PRIVATISATION",
        "Tariff Hike": "TARIFF",
        "Fuel-price adjustments": "FUEL",
        "Load-shedding events": "LOAD",
        "Other": "OTHER"
    }

    global_source_counter = Counter()
    global_sentiment_counter = Counter()

    for theme, placeholder in placeholder_map.items():
        news_items = theme_results.get(theme, [])
        content = ""

        for item in news_items:
            raw_summary = item.get("summary") or ""
            safe_summary = h.escape(raw_summary[:450])

            safe_title = h.escape(str(item.get("title", "")))
            safe_source = h.escape(str(item.get("source", "")))
            safe_link = h.escape(str(item.get("link", "")), quote=True)

            sentiment = (item.get("sentiment") or "neutral").lower()
            global_sentiment_counter[sentiment] += 1

            sentiment_color = (
                "green" if sentiment == "positive"
                else "red" if sentiment == "negative"
                else "gray"
            )

            content += f"""
            <div class="news-item" style="margin-bottom: 15px; page-break-inside: avoid;">
                <a href="{safe_link}" class="news-title">{safe_title}</a>
                <p class="news-summary">{safe_summary}...</p>
                <table style="width:100%; font-size:11px; margin-top:5px;">
                  <tr>
                    <td style="text-align:left;">
                      <a href="{safe_link}" style="color:#0b6b3a; font-weight:bold; text-decoration:none;">Read More →</a>
                    </td>
                    <td style="text-align:center; color:#999;">{safe_source}</td>
                    <td style="text-align:right; font-weight:bold; color:{sentiment_color};">{sentiment.capitalize()}</td>
                  </tr>
                </table>
            </div>
            """

            global_source_counter.update([item.get("source", "Unknown")])

        if not content:
            content = "<p class='no-news'>No news updates for this category in this date range.</p>"

        html_template = html_template.replace(f"{{{{{placeholder}}}}}", content)

    # ================= SOCIAL MEDIA COLUMNS =================
    sm_items = theme_results.get("Social_Media", [])
    n = len(sm_items)

    cols = [
        sm_items[:(n + 2) // 3],
        sm_items[(n + 2) // 3:2 * (n + 2) // 3],
        sm_items[2 * (n + 2) // 3:]
    ]

    for i, col in enumerate(cols, start=1):
        col_content = ""

        for item in col:
            raw_summary = item.get("summary") or ""
            safe_summary = h.escape(raw_summary[:50])

            safe_title = h.escape(str(item.get("title", "")))
            safe_source = h.escape(str(item.get("source", "")))
            safe_link = h.escape(str(item.get("link", "")), quote=True)

            sentiment = (item.get("sentiment") or "neutral").lower()

            sentiment_color = (
                "green" if sentiment == "positive"
                else "red" if sentiment == "negative"
                else "gray"
            )

            col_content += f"""
            <div class="news-item" style="page-break-inside: avoid;">
                <a href="{safe_link}" class="news-title">{safe_title}</a>
                <p class="news-summary">{safe_summary}...</p>
                <table style="width:100%; font-size:11px; margin-top:5px;">
                    <tr>
                        <td style="text-align:left;">
                            <a href="{safe_link}" style="color:#0b6b3a; font-weight:bold; text-decoration:none;">Read More →</a>
                        </td>
                        <td style="text-align:center; color:#999;">{safe_source}</td>
                        <td style="text-align:right; font-weight:bold; color:{sentiment_color};">{sentiment.capitalize()}</td>
                    </tr>
                </table>
            </div>
            """

        if not col_content:
            col_content = "<p class='no-news'>--</p>"

        html_template = html_template.replace(f"{{{{Social_Media_{i}}}}}", col_content)

    # ================= PIE CHARTS =================
    def save_pie_chart(counter, filename, title):
        pos = counter.get("positive", 0)
        neg = counter.get("negative", 0)
        neu = counter.get("neutral", 0)

        labels = []
        values = []

        if pos:
            labels.append(f"Positive ({pos})")
            values.append(pos)

        if neg:
            labels.append(f"Negative ({neg})")
            values.append(neg)

        if neu:
            labels.append(f"Neutral ({neu})")
            values.append(neu)

        if not values:
            labels = ["No Data"]
            values = [1]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    textinfo="label+percent",
                    marker=dict(colors=["#2ecc71", "#e74c3c", "#f1c40f"])
                )
            ]
        )

        fig.update_layout(
            title=title,
            title_x=0.5,
            width=400,
            height=350,
            margin=dict(l=10, r=10, t=40, b=10)
        )

        path = os.path.join(base_dir, filename)
        fig.write_image(path, scale=2)

        return path.replace("\\", "/")

    news_chart_path = save_pie_chart(
        global_sentiment_counter,
        "news_sentiment.png",
        "Consolidated News Sentiment"
    )

    sm_counter = Counter((d.get("sentiment") or "neutral").lower() for d in sm_items)

    social_chart_path = save_pie_chart(
        sm_counter,
        "social_sentiment.png",
        "Consolidated Social Sentiment"
    )

    pie_html = f"""
    <div style="text-align:center; width:100%; page-break-inside: avoid;">
        <table style="width:100%; text-align:center;">
            <tr>
                <td><img src="file:///{news_chart_path}" width="350" height="300"></td>
                <td><img src="file:///{social_chart_path}" width="350" height="300"></td>
            </tr>
        </table>
    </div>
    """

    html_template = html_template.replace("{{Sentiment_piechart}}", pie_html)

    # ================= EXECUTIVE SUMMARIES =================
    db = SessionLocal()

    try:
        query = text("""
            SELECT DISTINCT ON (DATE(article_date AT TIME ZONE 'Asia/Karachi'))
                DATE(article_date AT TIME ZONE 'Asia/Karachi') as d,
                daily_summary
            FROM news_articles
            WHERE DATE(article_date AT TIME ZONE 'Asia/Karachi') BETWEEN :start_date AND :end_date
            AND daily_summary IS NOT NULL
            AND daily_summary <> ''
            ORDER BY DATE(article_date AT TIME ZONE 'Asia/Karachi') DESC
        """)

        res = db.execute(
            query,
            {
                "start_date": start_date.date(),
                "end_date": end_date.date()
            }
        ).fetchall()

        if res:
            summary_val = ""

            for r in res:
                safe_daily_summary = h.escape(str(r.daily_summary))
                summary_val += f"<strong>{r.d.strftime('%d %B %Y')}:</strong><p>{safe_daily_summary}</p><br>"
        else:
            summary_val = "No summaries available for this date range."

    except Exception as e:
        summary_val = f"Error loading summaries: {h.escape(str(e))}"

    finally:
        db.close()

    html_template = html_template.replace(
        "{{summary}}",
        f"""
        <div style="font-size:14px; line-height:1.6;">
            <h1>Executive Summaries</h1>
            {summary_val}
        </div>
        """
    )

    # ================= LOGOS GRID =================
    logos_paths = {
        "bbc": "logos/bbc.png",
        "business recorder": "logos/br.png",
        "dawn": "logos/dawn.png",
        "tribune": "logos/tribune.png",
        "the news": "logos/Thenews-logo.png",
        "profit pakistan": "logos/profit pakistan.png",
        "propakistani": "logos/propakistani.png",
        "the guardian": "logos/guardian.png",
        "facebook": "logos/fb.png",
        "instagram": "logos/ig.png",
        "linkedin": "logos/li.png",
        "twitter": "logos/tw.png"
    }

    sm_counts = Counter(d["source"] for d in sm_items)
    sorted_sources = global_source_counter.most_common()

    def build_logo_rows(counter, exclude_set=None):
        logo_row = "<tr>"
        count_row = "<tr>"

        items = counter.items() if isinstance(counter, dict) else counter

        if not items:
            return ""

        for src, count in items:
            if exclude_set and src in exclude_set:
                continue

            source_key = str(src).lower()
            relative_path = logos_paths.get(source_key, "logos/default.png")
            absolute_path = os.path.join(base_dir, relative_path).replace("\\", "/")

            logo_row += f"""
            <td style="text-align:center; padding:10px; border:1px solid #333;">
                <img src="file:///{absolute_path}" style="height:45px; object-fit:contain;">
            </td>
            """

            count_row += f"""
            <td style="text-align:center; font-size:18px; font-weight:bold; color:#0b5394; padding:8px; border:1px solid #333;">
                {count}
            </td>
            """

        return logo_row + "</tr>" + count_row + "</tr>"

    final_logos = (
        build_logo_rows(sorted_sources, exclude_set=set(sm_counts.keys()))
        + build_logo_rows(sm_counts)
    )

    html_template = html_template.replace("{{Logos}}", final_logos)

    return html_template


# ================= GENERATE PDF =================
def generate_pdf(html_content, start_date, end_date):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    html_path = os.path.join(base_dir, "amag_tmp.html")

    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html_content)

    # Set this in environment variables if needed:
    # WKHTMLTOPDF_PATH=C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
    wkhtmltopdf_path = os.getenv(
        "WKHTMLTOPDF_PATH",
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    news_letters_dir = os.path.join(base_dir, "news_letters")

    if not os.path.exists(news_letters_dir):
        os.makedirs(news_letters_dir)

    range_str = f"{start_date.strftime('%d%m%Y')}_to_{end_date.strftime('%d%m%Y')}"

    pdf_name = f"Combined_Media_Energy_Monitor_{range_str}.pdf"
    pdf_path = os.path.join(news_letters_dir, pdf_name)

    options = {
        "page-size": "A4",
        "orientation": "Landscape",
        "margin-top": "8mm",
        "margin-bottom": "8mm",
        "margin-left": "8mm",
        "margin-right": "8mm",
        "enable-local-file-access": "",
        "print-media-type": "",
        "encoding": "UTF-8",
        "disable-smart-shrinking": ""
    }

    pdfkit.from_file(
        html_path,
        pdf_path,
        configuration=config,
        options=options
    )

    return pdf_path


# ================= EMAIL INFRASTRUCTURE =================
def email_report(to_emails, subject, body, pdf_path=None, use_bcc=True):
    """
    Sends newsletter email to multiple recipients.

    use_bcc=True:
        Recipients will not see each other's email addresses.
        Best for newsletter.

    use_bcc=False:
        All recipients will be visible in the To field.
    """

   
    SMTP_HOST = os.getenv("SMTP_HOST", "zimbramail.nayatel.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "power.post@ppmc.gov.pk")
    SMTP_PASS = os.getenv("SMTP_PASS", "ppmc@1122")

    if not SMTP_HOST:
        raise ValueError("SMTP_HOST environment variable is missing.")

    if not SMTP_USER:
        raise ValueError("SMTP_USER environment variable is missing.")

    if not SMTP_PASS:
        raise ValueError("SMTP_PASS environment variable is missing.")

    # If only one email is passed as string, convert it to list
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    # Clean emails
    to_emails = [email.strip() for email in to_emails if email and email.strip()]

    if not to_emails:
        raise ValueError("No recipient emails provided.")

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["Subject"] = subject

    if use_bcc:
        # Best for newsletter privacy
        msg["To"] = "Undisclosed Recipients"
        all_recipients = to_emails
    else:
        # Recipients can see each other
        msg["To"] = ", ".join(to_emails)
        all_recipients = to_emails

    msg.attach(MIMEText(body, "html"))

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(pdf_path)}"
        )

        msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, all_recipients, msg.as_string())

    print(f"Consolidated Email sent successfully to {len(to_emails)} recipients!")


# ================= SCHEDULER CONFIG =================
# Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4
SCHEDULE_WEEKDAYS = {0, 2, 4}  # Monday, Wednesday, Friday
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", 12))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", 0))
SCHEDULE_TIMEZONE = os.getenv("SCHEDULE_TIMEZONE", "Asia/Karachi")


def get_next_scheduled_run(after_dt=None):
    """
    Returns the next Monday/Wednesday/Friday 8:00 AM run time
    in Asia/Karachi timezone by default.
    """
    tz = ZoneInfo(SCHEDULE_TIMEZONE)

    if after_dt is None:
        after_dt = datetime.now(tz)
    elif after_dt.tzinfo is None:
        after_dt = after_dt.replace(tzinfo=tz)
    else:
        after_dt = after_dt.astimezone(tz)

    for days_ahead in range(0, 8):
        candidate_date = (after_dt + timedelta(days=days_ahead)).date()
        candidate = datetime.combine(
            candidate_date,
            time(SCHEDULE_HOUR, SCHEDULE_MINUTE),
            tzinfo=tz
        )

        if candidate.weekday() in SCHEDULE_WEEKDAYS and candidate > after_dt:
            return candidate

    # Safety fallback, should almost never run
    return after_dt + timedelta(days=1)


def run_scheduler():
    """
    Keeps this Python script running and automatically sends the report
    every Monday, Wednesday, and Friday at 8:00 AM Pakistan time.

    Important:
    - Keep the server/laptop running.
    - For production, run this file through Task Scheduler, systemd, PM2,
      Docker, or another process manager so it restarts after reboot.
    """
    print(
        "Newsletter scheduler started. "
        f"Schedule: Monday, Wednesday, Friday at "
        f"{SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} ({SCHEDULE_TIMEZONE})"
    )

    while True:
        now = datetime.now(ZoneInfo(SCHEDULE_TIMEZONE))
        next_run = get_next_scheduled_run(now)

        print(
            f"Next scheduled report: "
            f"{next_run.strftime('%A, %Y-%m-%d %I:%M %p %Z')}"
        )

        sleep_seconds = max(1, int((next_run - now).total_seconds()))
        time_module.sleep(sleep_seconds)

        try:
            print(
                f"Running scheduled newsletter at "
                f"{datetime.now(ZoneInfo(SCHEDULE_TIMEZONE)).strftime('%Y-%m-%d %I:%M %p %Z')}"
            )
            main()
            print("Scheduled newsletter completed successfully.")

        except Exception as e:
            print(f"Scheduled newsletter failed: {e}")

        # Prevent duplicate run in the same minute
        time_module.sleep(60)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate and email the Combined Media Energy Monitor newsletter."
    )

    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Keep script running and send automatically on Monday, Wednesday, and Friday at 12:00 pM."
    )

    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Generate and send the newsletter immediately."
    )

    parser.add_argument(
        "--start-date",
        help="Optional report start date in YYYY-MM-DD format."
    )

    parser.add_argument(
        "--end-date",
        help="Optional report end date in YYYY-MM-DD format."
    )

    return parser.parse_args()


# ================= MAIN RUNNER =================
def main(start_date_str=None, end_date_str=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Setup date range
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    elif start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = start_date

    else:
        # Default: last 3 days
        # Today + yesterday + day before yesterday
        end_date = datetime.today()
        start_date = end_date - timedelta(days=2)

    print(
        f"Generating single clubbed report from "
        f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}..."
    )

    keywords_path = os.path.join(base_dir, "keywords.csv")

    if not os.path.exists(keywords_path):
        raise FileNotFoundError(f"keywords.csv not found at: {keywords_path}")

    df = pd.read_csv(keywords_path)
    df.columns = df.columns.str.strip()

    try:
        # 1. Fetch data
        theme_results = fetch_news_by_theme_range(df, start_date, end_date)

        # 2. Generate HTML
        html_content = generate_html(theme_results, start_date, end_date)

        # 3. Generate PDF
        pdf_path = generate_pdf(html_content, start_date, end_date)

        # 4. Email body
        email_body = f"""
        <p>Please find attached the <strong>newsletter</strong> dated {start_date.strftime('%d %b')} – {end_date.strftime('%d %B %Y')}.</p>
        <p>For any questions or corrections, please reach out to the Advanced Analytics department at <a href="mailto:power.post@ppmc.gov.pk">Advanced Analytics</a>.</p>
        <br><p>Best regards,<br>
        <p>Advanced Analytics Department</p>"""

        # 5. Multiple recipient emails
        # Add all people here
        recipient_emails = [
            "all@ppmc.gov.pk",
        ]

        email_subject = (
            f"Media Energy Monitor Report "
            f"({start_date.strftime('%d %b')} - {end_date.strftime('%d %B %Y')})"
        )

        # 6. Send email
        # use_bcc=True means recipients cannot see each other's emails
        email_report(
            to_emails=recipient_emails,
            subject=email_subject,
            body=email_body,
            pdf_path=pdf_path,
            use_bcc=True
        )

    except Exception as e:
        print(f"❌ Failed to complete clubbed report processing execution: {e}")


if __name__ == "__main__":
    args = parse_args()

    if args.schedule:
        run_scheduler()

    elif args.run_now or args.start_date or args.end_date:
        main(
            start_date_str=args.start_date,
            end_date_str=args.end_date
        )

    else:
        # Default behavior stays the same as before:
        # running the file directly will generate and email the last 3 days report once.
        main()