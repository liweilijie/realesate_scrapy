# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import json

class CombinedRealEstateItem(scrapy.Item):
    # 房源基本信息
    name = scrapy.Field()           # 页面标识/名称（可选）
    url = scrapy.Field()            # 页面 URL
    title = scrapy.Field()          # 房源标题/名称
    external_id = scrapy.Field()    # 房屋外部唯一ID
    address = scrapy.Field()        # 完整地址
    suburb = scrapy.Field()         # 所属郊区
    state = scrapy.Field()          # 州/地区
    postcode = scrapy.Field()       # 邮政编码

    # 房屋属性
    price = scrapy.Field()          # 价格信息（字符串格式）
    property_type = scrapy.Field()  # 房产类型，如公寓、别墅等
    bedrooms = scrapy.Field()       # 卧室数量
    bathrooms = scrapy.Field()      # 浴室数量
    car_spaces = scrapy.Field()     # 车位数量
    land_area = scrapy.Field()      # 土地/建筑面积

    # 房屋描述与特性
    description = scrapy.Field()    # 房产详细描述
    council_rates = scrapy.Field() # 市政费
    features = scrapy.Field()       # 其他特性或配置

    # 媒体相关字段
    images = scrapy.Field()         # 房屋图片 URL 列表（预期为 Python 列表）
    origin_images = scrapy.Field()  # 原始图片 URL 列表
    floor_plan = scrapy.Field()     # 楼层平面图图片 URL 列表（预期为 Python 列表）
    origin_floor_plan = scrapy.Field()   # 原楼层平面图图片 URL 列表（预期为 Python 列表）
    pdf_document = scrapy.Field()   # 房屋相关 PDF 文档 URL
    origin_pdf_document = scrapy.Field()  # 原始 PDF 文档 URL

    # 地理位置信息
    latitude = scrapy.Field()       # 纬度
    longitude = scrapy.Field()      # 经度

    # 发布时间字段
    publish_date = scrapy.Field()   # 房源发布时间

    # 代理人信息
    agent_name = scrapy.Field()          # 代理人姓名（必填）
    agent_phone = scrapy.Field()         # 代理人电话号码（必填）
    agent_email = scrapy.Field()         # 代理人电子邮件（可选）
    agent_agency = scrapy.Field()        # 代理人所属机构
    agent_profile_url = scrapy.Field()   # 代理人个人页面 URL
    agent_bio = scrapy.Field()           # 代理人个人简介
    agent_profile_image = scrapy.Field() # 代理人头像 URL
    agent_social_media = scrapy.Field()  # 代理人社交媒体账号信息

    @classmethod
    def convert_images_to_json(cls, images):
        """
        将 images 字段（列表）转换为 JSON 格式字符串，
        方便在存储到数据库时直接作为 JSON 类型的数据使用。
        """
        try:
            return json.dumps(images)
        except Exception:
            return '[]'