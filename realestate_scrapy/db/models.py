from sqlalchemy.orm import declarative_base, relationship
from realestate_scrapy.db import engine
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.dialects.mysql import LONGTEXT, JSON

Base = declarative_base()


class Agent(Base):
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(255), nullable=False, comment="代理人姓名")
    agency = Column(String(255), nullable=True, comment="所属机构名称")
    phone = Column(String(50), nullable=True, comment="联系电话")
    email = Column(String(100), nullable=True, comment="电子邮件")
    profile_url = Column(String(255), nullable=True, comment="代理人个人页面URL")
    bio = Column(Text, nullable=True, comment="代理人个人简介")
    profile_image = Column(String(255), nullable=True, comment="代理人头像URL")
    social_media = Column(JSON, nullable=True, comment="社交媒体账号信息")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                        comment="更新时间")

    # 建立与 HomeListing 的一对多关系，但不设置级联删除
    listings = relationship("HomeListing", back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', agency='{self.agency}')>"


class HomeListing(Base):
    __tablename__ = 'home_listings'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    url = Column(String(255), unique=True, nullable=False, comment="页面 URL")
    external_id = Column(String(50), unique=True, nullable=False, comment="网站房屋ID")
    title = Column(String(255), nullable=True, comment="房源标题/名称")
    address = Column(String(255), nullable=True, comment="完整地址")
    suburb = Column(String(255), nullable=True, comment="所属郊区")
    state = Column(String(50), nullable=True, comment="州/地区")
    postcode = Column(String(10), nullable=True, comment="邮政编码")

    # 价格
    price_text = Column(String(50), nullable=True, comment="价格文本信息")
    lower_price = Column(Integer, nullable=True, comment="最低价格")
    upper_price = Column(Integer, nullable=True, comment="最高价格")

    property_type = Column(String(50), nullable=True, comment="房产类型")
    bedrooms = Column(Integer, nullable=True, comment="卧室数量")
    bathrooms = Column(Integer, nullable=True, comment="浴室数量")
    car_spaces = Column(Integer, nullable=True, comment="车位数量")
    land_area = Column(Integer, nullable=True, comment="土地/建筑面积")
    description = Column(Text, nullable=True, comment="房产描述")
    council_rates = Column(String(50), nullable=True, comment="市政费")
    features = Column(Text, nullable=True, comment="其他特性或配置")
    images = Column(JSON, nullable=True, comment="房屋图片URL列表")
    origin_images = Column(JSON, nullable=True, comment="原房屋图片URL列表")
    floor_plan = Column(JSON, nullable=True, comment="楼层平面图图片URL列表")
    origin_floor_plan = Column(JSON, nullable=True, comment="原楼层平面图图片URL列表")
    pdf_document = Column(JSON, nullable=True, comment="房屋PDF文档URL")
    origin_pdf_document = Column(JSON, nullable=True, comment="原房屋PDF文档URL")
    latitude = Column(Numeric(11, 7), nullable=True, comment="纬度")
    longitude = Column(Numeric(11, 7), nullable=True, comment="经度")
    publish_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, comment="房源发布时间")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow,
                        comment="更新时间")

    # 添加与 Agent 关联的字段，建立外键关联
    agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True, comment="关联的代理人ID")
    # 建立与 Agent 的关系字段，方便通过 listing 获取对应代理信息
    agent = relationship("Agent", back_populates="listings")

    def __repr__(self):
        return (f"<HomeListing(id={self.id}, external_id='{self.external_id}', "
                f"address='{self.address}', price='{self.price}')>")


# 创建所有表
Base.metadata.create_all(engine)

# from sqlalchemy.orm import declarative_base
#
# from realestate_scrapy.db import engine
#
# # !/usr/bin/env python
# # -*- coding: utf-8 -*-
# import datetime
# from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.dialects.mysql import LONGTEXT, JSON
#
# Base = declarative_base()
#
#
# class HomeListing(Base):
#     __tablename__ = 'home_listings'
#
#     id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
#     url = Column(String(255), unique=True, nullable=False, comment="页面 URL")
#     external_id = Column(String(50), unique=True, nullable=False, comment="网站房屋ID")
#     title = Column(String(255), nullable=True, comment="房源标题/名称")
#     address = Column(String(255), nullable=True, comment="完整地址")
#     suburb = Column(String(255), nullable=True, comment="所属郊区")
#     state = Column(String(50), nullable=True, comment="州/地区")
#     postcode = Column(String(10), nullable=True, comment="邮政编码")
#     price = Column(String(50), nullable=True, comment="价格信息")
#     property_type = Column(String(50), nullable=True, comment="房产类型")
#     bedrooms = Column(Integer, nullable=True, comment="卧室数量")
#     bathrooms = Column(Integer, nullable=True, comment="浴室数量")
#     car_spaces = Column(Integer, nullable=True, comment="车位数量")
#     land_area = Column(String(50), nullable=True, comment="土地/建筑面积")
#     description = Column(Text, nullable=True, comment="房产描述")
#     features = Column(Text, nullable=True, comment="其他特性或配置")
#
#     # 新增图片相关字段
#     images = Column(JSON, nullable=True, comment="房屋图片URL列表")
#     origin_images = Column(JSON, nullable=True, comment="原房屋图片URL列表")
#     floor_plan = Column(JSON, nullable=True, comment="楼层平面图图片URL列表")
#     origin_floor_plan = Column(JSON, nullable=True, comment="原楼层平面图图片URL列表")
#     pdf_document = Column(JSON, nullable=True, comment="房屋PDF文档URL")
#     origin_pdf_document = Column(JSON, nullable=True, comment="原房屋PDF文档URL")
#
#     # 地理位置信息
#     latitude = Column(Numeric(11, 7), nullable=True, comment="纬度")
#     longitude = Column(Numeric(11, 7), nullable=True, comment="经度")
#
#     publish_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, comment="房源发布时间")
#     created_at = Column(DateTime, default=datetime.datetime.utcnow, comment="创建时间")
#     updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, comment="更新时间")
#
#     def __repr__(self):
#         return (f"<HomeListing(id={self.id}, external_id='{self.external_id}', "
#                 f"address='{self.address}', price='{self.price}')>")
#
# Base.metadata.create_all(engine)
#
