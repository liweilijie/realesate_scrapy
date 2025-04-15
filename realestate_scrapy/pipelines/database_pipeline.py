import datetime

from sqlalchemy.orm import sessionmaker

from realestate_scrapy.db import engine
from realestate_scrapy.db.models import Agent, HomeListing


class DBRealEstatePipeline:
    def __init__(self):
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def process_item(self, item, spider):
        # 1. 处理代理人信息
        # 必须字段：agent_name 和 agent_phone
        agent_name = item.get('agent_name')
        agent_phone = item.get('agent_phone')

        if not agent_name or not agent_phone:
            spider.logger.error("缺少代理人必填信息：agent_name 和 agent_phone")
            return item

        # 通过代理人姓名和电话号码判断是否存在已有记录
        # 使用 filter 显式书写查询条件
        agent = self.session.query(Agent).filter(
            Agent.name == agent_name,
                     Agent.phone == agent_phone
        ).first()


        if not agent:
            # 如果不存在，则创建新的代理人记录
            agent = Agent(
                name=agent_name,
                phone=agent_phone,
                email=item.get('agent_email'),
                agency=item.get('agent_agency'),
                profile_url=item.get('agent_profile_url'),
                bio=item.get('agent_bio'),
                profile_image=item.get('agent_profile_image'),
                social_media=item.get('agent_social_media'),
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            self.session.add(agent)
            self.session.commit()  # 提交后 agent.id 才可用于关联
        else:
            # 如果代理人记录已存在，更新非空信息（可根据需求调整更新策略）
            agent.email = item.get('agent_email') or agent.email
            agent.agency = item.get('agent_agency') or agent.agency
            agent.profile_url = item.get('agent_profile_url') or agent.profile_url
            agent.bio = item.get('agent_bio') or agent.bio
            agent.profile_image = item.get('agent_profile_image') or agent.profile_image
            agent.social_media = item.get('agent_social_media') or agent.social_media
            agent.updated_at = datetime.datetime.utcnow()
            self.session.commit()

        # 2. 处理房源信息
        external_id = item.get('external_id')
        listing = self.session.query(HomeListing).filter(HomeListing.external_id == external_id).first()


        if not listing:
            # 新增房源记录，同时将 agent_id 关联到刚刚获取的代理人记录
            listing = HomeListing(
                url=item.get('url'),
                external_id=external_id,
                title=item.get('title'),
                address=item.get('address'),
                suburb=item.get('suburb'),
                state=item.get('state'),
                postcode=item.get('postcode'),
                price=item.get('price'),
                property_type=item.get('property_type'),
                bedrooms=item.get('bedrooms'),
                bathrooms=item.get('bathrooms'),
                car_spaces=item.get('car_spaces'),
                land_area=item.get('land_area'),
                description=item.get('description'),
                council_rates=item.get('council_rates'),
                features=item.get('features'),
                images=item.get('images'),
                origin_images=item.get('origin_images'),
                floor_plan=item.get('floor_plan'),
                origin_floor_plan=item.get('origin_floor_plan'),
                pdf_document=item.get('pdf_document'),
                origin_pdf_document=item.get('origin_pdf_document'),
                latitude=item.get('latitude'),
                longitude=item.get('longitude'),
                publish_date=item.get('publish_date'),
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
                agent_id=agent.id
            )
            self.session.add(listing)
        else:
            # 更新已存在的房源记录
            listing.url = item.get('url') or listing.url
            listing.title = item.get('title') or listing.title
            listing.address = item.get('address') or listing.address
            listing.suburb = item.get('suburb') or listing.suburb
            listing.state = item.get('state') or listing.state
            listing.postcode = item.get('postcode') or listing.postcode
            listing.price = item.get('price') or listing.price
            listing.property_type = item.get('property_type') or listing.property_type
            listing.bedrooms = item.get('bedrooms') or listing.bedrooms
            listing.bathrooms = item.get('bathrooms') or listing.bathrooms
            listing.car_spaces = item.get('car_spaces') or listing.car_spaces
            listing.land_area = item.get('land_area') or listing.land_area
            listing.description = item.get('description') or listing.description
            listing.council_rates = item.get('council_rates') or listing.council_rates,
            listing.features = item.get('features') or listing.features
            listing.images = item.get('images') or listing.images
            listing.origin_images = item.get('origin_images') or listing.origin_images
            listing.floor_plan = item.get('floor_plan') or listing.floor_plan
            listing.origin_floor_plan = item.get('origin_floor_plan') or listing.origin_floor_plan
            listing.pdf_document = item.get('pdf_document') or listing.pdf_document
            listing.origin_pdf_document = item.get('origin_pdf_document') or listing.origin_pdf_document
            listing.latitude = item.get('latitude') or listing.latitude
            listing.longitude = item.get('longitude') or listing.longitude
            listing.publish_date = item.get('publish_date') or listing.publish_date
            listing.updated_at = datetime.datetime.utcnow()
            listing.agent_id = agent.id  # 确保房源记录关联到当前代理人

        self.session.commit()
        return item

    def close_spider(self, spider):
        self.session.close()
