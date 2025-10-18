# اجرای خودکار بک‌تست با GitHub Actions

این فولدر شامل اسکریپت و راهنمای اجرای چرخه‌ی کامل جمع‌آوری داده و بک‌تست در محیط‌های خودکار (مثل GitHub Actions یا کرون‌جاب) است.

## اجزای اصلی

| فایل | توضیح |
| --- | --- |
| `run_full_cycle.py` | اسکریپت اصلی که تمام نمادهای تعریف‌شده در `prover.py` را پردازش می‌کند: جمع‌آوری داده، تولید سیگنال، ثبت لاگ‌ها و اجرای بک‌تست. |
| `.github/workflows/collect-backtest.yml` | ورک‌فلو پیشنهادی برای GitHub Actions (در ریشه‌ی مخزن) که این اسکریپت را به‌صورت زمان‌بندی‌شده اجرا می‌کند. |

## پیش‌نیازها

- Python 3.10 یا بالاتر  
- کتابخانه‌های موردنیاز:  
```
pip install \
  pandas==2.3.3 \
  pandas-ta==0.3.14b0 \
  numpy==2.1.3 \
  requests==2.32.3 \
  orjson==3.10.7 \
  PyQt5==5.15.11 \
  matplotlib==3.9.2
```

## اجرای دستی روی سیستم‌تان

```bash
python گیتهاب اکشن/run_full_cycle.py \
  --root data \
  --horizon 5 \
  --calibration-output data/analytics/threshold_suggestions.json \
  --summary-output data/analytics/backtest_summary.txt
```

پس از اجرا، خروجی‌های زیر تولید می‌شود:

- `data/analytics/decision_profile.csv` و `data/analytics/entry_gap.csv`
- `data/analytics/backtest_summary.txt`
- `data/analytics/threshold_suggestions.json`

## استفاده روی GitHub

1. این مخزن را به GitHub منتقل و فولدر `.github/workflows` را نیز کامیت کنید.  
2. فایل `collect-backtest.yml` یک ورک‌فلو زمان‌بندی‌شده‌ی روزانه ایجاد می‌کند؛ در صورت نیاز، کران را تغییر دهید.  
3. لزومی به تنظیم توکن نیست مگر این‌که به API یا سرویس خصوصی دیگری متصل شوید.  
4. خروجی هر اجرای موفق به‌صورت Artifact در صفحه‌ی Action ذخیره می‌شود و می‌توانید آن را دانلود یا به برنامه‌ی دسکتاپ منتقل کنید.

## سفارشی‌سازی

- پارامترهای اسکریپت (`--symbols`، `--timeframes`، `--bars-per-tf`) قابل تنظیم هستند.  
- می‌توانید مسیر خروجی‌ها را متناسب با نیاز خود تغییر دهید یا پس از اتمام، فایل‌ها را به S3/FTP انتقال دهید.  
- در صورت نیاز به وابستگی‌های بیشتر، بخش نصب کتابخانه‌ها در فایل ورک‌فلو را به‌روزرسانی کنید.
