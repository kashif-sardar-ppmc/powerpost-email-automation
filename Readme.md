# Email Newsletter Scheduler

## Installation

Install all required dependencies:

```bash
pip install -r req.txt
```

## Run Scheduler

Start the newsletter scheduler:

```bash
python .\email_newsletter.py --schedule
```

The scheduler will automatically generate and send the newsletter on:

* Monday
* Wednesday
* Friday

at **12:00 PM (Asia/Karachi Time Zone)**.

## Run Immediately

To generate and send the newsletter immediately:

```bash
python .\email_newsletter.py --run-now
```

## Notes

* Ensure all environment variables are configured correctly.
* Ensure the database is accessible.
* Ensure SMTP credentials are valid.
* Keep the application running when using `--schedule` mode.
