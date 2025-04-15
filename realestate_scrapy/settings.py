# Scrapy settings for realestate_scrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "realestate_scrapy"

SPIDER_MODULES = ["realestate_scrapy.spiders"]
NEWSPIDER_MODULE = "realestate_scrapy.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "realestate_scrapy (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
LOG_LEVEL = "DEBUG"


# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "realestate_scrapy.middlewares.RealestateScrapySpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "realestate_scrapy.middlewares.RealestateScrapyDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # "realestate_scrapy.pipelines.images.ImagesPipeline": 9,
    # "realestate_scrapy.pipelines.files.FilesPipeline": 10,
    # "realestate_scrapy.pipelines.media_pipeline.RealEstateMediaPipeline": 11,
    "realestate_scrapy.pipelines.images_pipeline.HlImagesPipeline": 12,
    "realestate_scrapy.pipelines.documents_pipeline.HlDocumentsPipeline": 13,
    "realestate_scrapy.pipelines.database_pipeline.DBRealEstatePipeline": 14,
    # "realestate_scrapy.pipelines.RealestateScrapyPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "realestate_scrapy"))

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
# MEDIA_ALLOW_REDIRECTS = True
IMAGES_STORE_GCS_ACL = "publicRead"

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER_PERSIST = True

DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# which item to download image
IMAGES_URLS_FIELD = "origin_images"
FILES_URLS_FIELD = "origin_pdf_document"


# ------------------------------- emacsvi.com ---------------------------------
# emacsvi redis
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_DB = 2
REDIS_PASSWORD = ""
REDIS_URL = 'redis://127.0.0.1:6379/2'

#Database settings for emacsvi
DB_HOST = '192.168.1.253'
DB_PORT = 3306
DB_USER = 'homesteads'
DB_PASSWD = 'AEsbso129129'
DB_DB = 'homesteads'

#SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}?ssl_ca={DATABASE_CERT_FILE}"
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:{DB_PORT}/{DB_DB}"

# gcs emacsvi.com
# GOOGLE_APPLICATION_CREDENTIALS = "/Users/liwei/Desktop/py/realestate_scrapy/emacsvi.json"
GOOGLE_APPLICATION_CREDENTIALS = "/home/srv/emacsvi.json"
FILES_STORE = "gs://cdn.emacsvi.com/"
FILES_STORE_GCS_PROJECT_ID = "resounding-age-449321-k4"
IMAGES_STORE = "gs://cdn.emacsvi.com/"
GCS_PROJECT_ID = "resounding-age-449321-k4"
GCS_BUCKET_NAME= "cdn.emacsvi.com"

NEWS_ACCOUNTS = {
   "homely": {
      "image_cdn_domain": "https://cdn.emacsvi.com/",
      "count_everyday": 9
   }
}
#
# ------------------------------- end emacsvi.com ---------------------------------
