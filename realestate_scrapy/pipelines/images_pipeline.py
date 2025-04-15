import logging
import hashlib
import os
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.project import get_project_settings

logger = logging.getLogger('media')
# 通过 settings 获取配置信息，并设置 GOOGLE_APPLICATION_CREDENTIALS 环境变量
SETTING = get_project_settings()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SETTING["GOOGLE_APPLICATION_CREDENTIALS"]

class HlImagesPipeline(ImagesPipeline):

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        根据图片 URL 生成图片存储路径：
        若 item 中包含 external_id，则使用该值，
        否则使用 SHAKE_256 生成前 5 个字符作为 external_id，
        同时利用 request.url 在 item["origin_images"] 中的下标构造图片路径，
        路径格式： realestate/hl/external_id/gallery-index.jpg
        """
        # 判断 item 是否包含 external_id，有则使用；否则生成前 5 个字符的哈希
        if item is not None and item.get("external_id"):
            external_id = item["external_id"]
        else:
            image_url_hash = hashlib.shake_256(request.url.encode()).hexdigest(5)
            external_id = image_url_hash[:5]

        # 尝试获取 request.url 在 item["origin_images"] 列表中的下标，如果找不到则默认使用 0
        try:
            index = item.get("origin_images", []).index(request.url)
        except ValueError:
            index = 0

        path = os.path.join("realestate", "hl", external_id, f"gallery-{index}.jpg")
        logger.info("Generated image file path: %s", path)
        return path

    # def file_path(self, request, response=None, info=None, *, item=None):
    #     """
    #     根据图片 URL 生成图片存储路径：
    #     使用 SHAKE_256 生成 5 个字符的哈希，保证文件名唯一，
    #     并存放在 realestate/hl 目录下，扩展名为 .jpg
    #     """
    #     image_url_hash = hashlib.shake_256(request.url.encode()).hexdigest(5)
    #     path = os.path.join("realestate", "hl", f"{image_url_hash[:5]}.jpg")
    #     logger.info("Generated image file path: %s", path)
    #     return path

    def item_completed(self, results, item, info):
        """
        图片上传完成后：
        1. 遍历 results 数组，构造图片的 CDN URL
        2. 将 CDN URL 存入 item 的 front_image_path 数组中
        """
        # 确保 front_image_path 字段存在
        item.setdefault("images", [])
        if "origin_images" in item:
            for ok, value in results:
                if ok and isinstance(value, dict) and 'path' in value:
                    try:
                        # 从 settings 中根据 item["name"] 获取 CDN 域名
                        cdn_domain = SETTING["NEWS_ACCOUNTS"][item["name"]]["image_cdn_domain"]
                        cdn_url = f"{cdn_domain}{value['path']}"
                        item["images"].append(cdn_url)
                    except KeyError as e:
                        logger.error("Missing configuration key: %s", e)
                    except Exception as ex:
                        logger.error("Error constructing CDN URL: %s", ex)

        logger.info("Final images: %s", item["images"])
        return item
