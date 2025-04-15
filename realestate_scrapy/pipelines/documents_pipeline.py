import os
import logging
import hashlib
from scrapy.pipelines.images import FilesPipeline
from scrapy.utils.project import get_project_settings
from google.cloud import storage

logger = logging.getLogger('document')

SETTINGS = get_project_settings()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SETTINGS["GOOGLE_APPLICATION_CREDENTIALS"]


class HlDocumentsPipeline(FilesPipeline):

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        通过 MD5 生成8位哈希作为文件名，文件将存放于 realestate/hl 目录下
        """

        if item is not None and item.get("external_id"):
            external_id = item["external_id"]
        else:
            pdf_url_hash = hashlib.shake_256(request.url.encode()).hexdigest(5)
            external_id = pdf_url_hash[:5]

        # 尝试获取 request.url 在 item["origin_images"] 列表中的下标，如果找不到则默认使用 0
        try:
            index = item.get("origin_pdf_document", []).index(request.url)
        except ValueError:
            index = 0

        path = os.path.join("realestate", "hl", external_id, f"doc-{index}.jpg")
        logger.info("Generated pdf file path: %s", path)
        return path

    def item_completed(self, results, item, info):
        """
        在 item_completed 阶段对已上传的 PDF 文件进行后处理：
        1. 通过 Google Cloud Storage API 打开已上传文件的 blob 对象，
           修改其元数据，将 Content-Disposition 设置为 inline，并附加文件名，
           使得文档在浏览器中直接打开而不是下载。
           通过设置 blob.content_type = "application/pdf" 来确保文件的 Content-Type 在 GCS 中被更新为 application/pdf。
        2. 构造最终的 CDN URL（基于 NEWS_ACCOUNTS 配置）写入 item 的 pdf_document_cdn 字段。
        """
        # 确保 pdf_document_cdn 字段存在
        if "pdf_document" not in item:
            item["pdf_document"] = []

        # 初始化 GCS 客户端和 bucket（需要在 settings 中配置 GCS_BUCKET_NAME）
        client = storage.Client()
        bucket_name = SETTINGS.get("GCS_BUCKET_NAME")
        if not bucket_name:
            logger.error("GCS_BUCKET_NAME is not configured in settings.")
            return item
        bucket = client.bucket(bucket_name)

        if "origin_pdf_document" in item:
            for ok, value in results:
                if ok and isinstance(value, dict) and "path" in value:
                    file_path_value = value["path"]
                    # 获取 GCS 中该文件对应的 blob 对象
                    blob = bucket.blob(file_path_value)
                    # 从 file_path 中提取文件名
                    filename = os.path.basename(file_path_value)
                    # 设置 Content-Disposition 为 inline，并附加文件名
                    blob.content_disposition = f'inline; filename="{filename}"'
                    # 设置 Content-Type 为 application/pdf
                    blob.content_type = "application/pdf"
                    try:
                        blob.patch()  # 更新 blob 元数据
                        logger.info(f"Updated metadata for {file_path_value} to inline with filename {filename}")
                    except Exception as e:
                        logger.error(f"Error updating metadata for {file_path_value}: {e}")
                    # 构造最终 CDN URL，依赖 NEWS_ACCOUNTS 与 item["name"] 的配置
                    try:
                        cdn_domain = SETTINGS["NEWS_ACCOUNTS"][item["name"]]["image_cdn_domain"]
                        cdn_url = f"{cdn_domain}{file_path_value}"
                        item["pdf_document"].append(cdn_url)
                    except Exception as e:
                        logger.error(f"Error constructing CDN URL for item {item}: {e}")

        logger.info(f"Final PDF CDN URLs: {item['pdf_document']}")
        return item
