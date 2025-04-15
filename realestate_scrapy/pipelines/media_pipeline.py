import logging
import os
from scrapy import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.project import get_project_settings

logger = logging.getLogger('media')

SETTING = get_project_settings()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=SETTING["GOOGLE_APPLICATION_CREDENTIALS"]

class RealEstateMediaPipeline(FilesPipeline):
    """
    该 pipeline 下载 item 中的图片和文件，并重命名为:
      realestate/hl/{external_id}/{category}-{index}.{ext}

    - 对于 images 字段，category 为 gallery，扩展名为 jpg；
    - 对于 floor_plan 字段，category 为 floorplan，扩展名为 jpg；
    - 对于 pdf_document 字段，category 为 pdf，扩展名为 pdf。

    下载结束后，将原始 URL 与目标保存路径构造映射，并直接替换原有的 images、floor_plan 和 pdf_document 字段，
    以便数据库中直接以 JSON 格式存储。
    """

    def get_media_requests(self, item, info):
        external_id = item.get("external_id")
        # 处理 images 字段（列表）：类别为 gallery
        if item.get("images"):
            for index, img_url in enumerate(item["images"], start=1):
                yield Request(
                    url=img_url,
                    meta={
                        "external_id": external_id,
                        "category": "gallery",
                        "index": index,
                        "original_url": img_url
                    }
                )
        # 处理 floor_plan 字段（列表）：类别为 floorplan
        if item.get("floor_plan"):
            for index, img_url in enumerate(item["floor_plan"], start=1):
                yield Request(
                    url=img_url,
                    meta={
                        "external_id": external_id,
                        "category": "floorplan",
                        "index": index,
                        "original_url": img_url
                    }
                )
        # 处理 pdf_document 字段（单个 URL）：类别为 pdf
        if item.get("pdf_document"):
            yield Request(
                url=item["pdf_document"],
                meta={
                    "external_id": external_id,
                    "category": "pdf",
                    "index": 1,
                    "original_url": item["pdf_document"]
                }
            )

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        根据传入的 meta 信息构造文件保存路径：
          realestate/hl/{external_id}/{category}-{index}.{ext}
        如果 category 为 "pdf"，扩展名为 pdf，其它情况一律为 jpg。
        """
        external_id = request.meta.get("external_id", "unknown")
        category = request.meta.get("category", "file")
        index = request.meta.get("index", 1)
        ext = "pdf" if category == "pdf" else "jpg"
        filename = f"{category}-{index}.{ext}"
        p = os.path.join("realestate", "hl", str(external_id), filename)
        logger.info(f'return bucket filename:{p}')

    def file_downloaded(self, response, request, info, *, item=None):
        path = self.file_path(request, response=response, info=info, item=item)
        return {
            "original": request.meta.get("original_url", request.url),
            "target": path,
            "category": request.meta.get("category"),
            "index": request.meta.get("index")
        }

    def item_completed(self, results, item, info):
        """
        遍历所有下载结果，将每个成功下载的文件构造为包含原始 URL 与目标路径的映射，
        然后直接更新 item 中的 images、floor_plan、pdf_document 字段为 JSON 格式数据。
        """
        mappings = {
            "images": [],
            "floor_plan": [],
            "pdf_document": []
        }
        for success, file_info in results:
            if success:
                cat = file_info.get("category")
                mapping = {
                    "original": file_info.get("original"),
                    "target": file_info.get("target")
                }
                if cat == "gallery":
                    mappings["images"].append(mapping)
                elif cat == "floorplan":
                    mappings["floor_plan"].append(mapping)
                elif cat == "pdf":
                    mappings["pdf_document"].append(mapping)
        # 直接更新 item 中对应字段：如果没有下载成功的内容，可按需求保留原始值或设为 None
        if mappings["images"]:
            item["images"] = mappings["images"]
        if mappings["floor_plan"]:
            item["floor_plan"] = mappings["floor_plan"]
        if mappings["pdf_document"]:
            item["pdf_document"] = mappings["pdf_document"]
        return item

