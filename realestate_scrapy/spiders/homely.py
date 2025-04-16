import logging
import time
import re
from datetime import datetime

import scrapy
from scrapy.selector import Selector
from scrapy_redis.spiders import RedisSpider

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC
import undetected_chromedriver as uc

from realestate_scrapy.cache import url_queue
from realestate_scrapy.settings import REDIS_URL

logger = logging.getLogger('homely')


class HomelySpider(RedisSpider):
    name = "homely"
    allowed_domains = ["homely.com.au"]
    start_urls = ["https://www.homely.com.au/for-sale/melbourne-vic-3000/real-estate"]
    redis_key = "homelyspider:start_urls"
    redis_batch_size = 1

    custom_settings = {
        'COOKIES_ENABLED': True,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/132.0.0.0 Safari/537.36',
    }

    def __init__(self, *args, **kwargs):
        super(HomelySpider, self).__init__(*args, **kwargs)
        # 配置 Chrome 和 Chromedriver 的路径（根据具体平台修改）
        #chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        #chromedriver_path = "/usr/local/bin/chromedriver"

        chrome_path = "/usr/bin/google-chrome"
        chromedriver_path = "/usr/local/bin/chromedriver"
        options = Options()
        options.headless = True # 调试时可设置为 False，正式运行时可考虑 headless 模式
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        self.driver = uc.Chrome(
            options=options,
            driver_executable_path=chromedriver_path,
            browser_executable_path=chrome_path,
            use_subprocess=False
        )
        self.wait = WebDriverWait(self.driver, 20)
        # 定义页面滚动的 JavaScript 代码
        self.js_scroll = "window.scrollTo(0, document.body.scrollHeight)"
        self.headers = {
            'Referer': 'https://www.homely.com.au/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/133.0.0.0 Safari/537.36'
        }
        self.url_queue = url_queue.RedisUrlQueue(self.name, REDIS_URL)

    def __del__(self):
        # 保证退出时关闭浏览器
        self.driver.quit()

    def parse(self, response):
        """
        加载列表页，提取每个房源详情链接。
        """
        # if property call parse_property
        if "/homes/" in response.url:
            yield scrapy.Request(response.url, callback=self.parse_property)
        else:
            logger.info("Parse listing page: %s", response.url)
            self.driver.get(response.url)
            time.sleep(5)  # 等待页面加载（也可以改用更精准的显式等待）
            self.driver.execute_script(self.js_scroll)
            time.sleep(2)

            page_source = self.driver.page_source
            sel = Selector(text=page_source)
            # 定位所有房产列表条目的链接
            property_links = sel.css('article[aria-label="Property Listing"] a::attr(href)').getall()
            logger.info("Found %d property links", len(property_links))
            # 对每个链接发起新的请求，交由 parse_property 方法处理
            for link in property_links:
                yield response.follow(link, self.parse_property)

    def parse_property(self, response):
        """
        解析房产详情页，提取基本信息和描述，接着模拟点击 gallery 按钮获取图片 URL。
        """
        logger.info("Parse property detail page: %s", response.url)
        self.driver.get(response.url)
        time.sleep(5)
        try:
            # 等待房产描述部分加载出来
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'section[aria-label="Property description"]')
                )
            )
        except Exception as e:
            logger.error("Property description not found: %s", e)
        self.driver.execute_script(self.js_scroll)
        time.sleep(2)

        page_source = self.driver.page_source

        # debug
        with open("p2.html", "w", encoding="utf-8") as f:
            f.write(page_source)

        sel = Selector(text=page_source)
        header_sel = sel.xpath("//header")

        # 提取地址、城市、价格等基本信息
        address = header_sel.xpath('.//h1/text()').get()
        city = header_sel.xpath('.//span[@class="inline"]/text()').get()
        full_address = f"{address.strip()} {city.strip()}" if address and city else None
        postcode = self.parse_postcode(city)

        # 提取价格字符串
        price_text = header_sel.xpath('.//section[@aria-label="Summary"]//h2/text()').get()
        lower_price, upper_price = self.parse_price(price_text)

        # 提取卧室、浴室、车位信息，先获取对应的文本，再转为整数
        bedrooms_str = header_sel.xpath('//li[span[@aria-label="Bed"]]/text()[normalize-space()]').get()
        bathrooms_str = header_sel.xpath('//li[span[@aria-label="Bath"]]/text()[normalize-space()]').get()
        cars_str = header_sel.xpath('//li[span[@aria-label="Car"]]/text()[normalize-space()]').get()
        area = header_sel.xpath('//li[span[@aria-label="Area"]]/text()[normalize-space()]').get(default='')
        try:
            bedrooms = int(bedrooms_str) if bedrooms_str else None
        except Exception:
            bedrooms = None
        try:
            bathrooms = int(bathrooms_str) if bathrooms_str else None
        except Exception:
            bathrooms = None
        try:
            car_spaces = int(cars_str) if cars_str else None
        except Exception:
            car_spaces = None

        # try:
        #     area = int(area_str) if area_str else None
        # except Exception:
        #     area = None

        # 解释：
        #
        #     (//section[@aria-label="Summary"]//h3/span[contains(text(),"for sale")])[1]
        #     这部分先查找 <section aria-label="Summary"> 下的所有 <h3> 内的 <span> 元素，且其文本包含 “for sale”，用 [1] 取第一个匹配项。
        #
        #     substring-before(..., " for sale")
        #     这个函数会返回第一个参数文本中，在遇到 " for sale"（注意前面有一个空格）之前的部分，从而提取出 “Apartment” 或 “House”。
        #
        #     .get(default='house')
        #     若没有匹配到任何结果，就返回默认值 'house'。
        property_type = header_sel.xpath(
            'substring-before((//section[@aria-label="Summary"]//h3/span[contains(text(),"for sale")])[1]/text(), " for sale")'
        ).get(default='House')


        # 提取详细描述
        desc_sel = sel.xpath('//section[@aria-label="Property description"]')
        # description = desc_sel.xpath('.//p//text()').getall()
        description = desc_sel.xpath('.//p//text()').get(default='')

        council_rates = response.xpath(
            '//section[@aria-label="Property description"]//div[h3[contains(text(),"Council rates")]]/span/text()'
        ).get(default='').strip()

        # description = ' '.join([p.strip() for p in description_paragraphs if p.strip()])

        # 使用 XPath 表达式定位并提取 Area 的值
        # 这段代码的工作原理如下：
        # Scrapy Cookbook
        #
        # //section[@aria-label="Property description"]：定位到具有aria-label属性为“Property description”的section元素。
        # //div[h3[contains(text(), "Land details")]]：在上述section元素内，查找包含h3标题且其文本包含“Land details”的div元素。
        # //div[contains(text(), "Area:")]/span/text()：在上述div元素内，查找包含文本“Area:”的div元素，并提取其子span元素的文本内容。
        if area is None or area == '':
            area = sel.xpath(
                '//section[@aria-label="Property description"]'
                # '//div[h3[contains(text(), "Land details")]]'
                '//div[contains(text(), "Area:")]/span/text()'
            ).get()

        logger.info(f"Area: {area}")

        if area is not None:
            area_number = re.findall(r'\d+', area)
            area_number = int(area_number[0]) if area_number else 0
        else:
            area_number = 0
        # 提取数字部分
        # area_value = int(re.search(r'\d+', area).group()) if area else None
        # print(f"Area (numeric): {area_value}")

        # 提取 Documents 链接
        document_link = sel.xpath(
            '//section[@aria-label="Property description"]'
            '//h3[text()="Documents"]/following-sibling::div[1]//a/@href'
        ).get()

        document_link = document_link.strip() if document_link else None
        document_links = [document_link]

        # //section[@aria-label="Property map"]//div[contains(@style, "background-image")]/@style
        # 定位到包含背景图片 URL 的 div 的 style 属性。
        #
        # substring-after(..., "center=")
        # 从 style 属性值中截取 "center=" 后的字符串。
        #
        # substring-before(..., "&")
        # 从上一步的结果中截取第一个 & 前的部分，从而得到类似 "-37.7334201,144.7981836" 的字符串。
        # 使用 XPath 提取包含背景图片 URL 的 style 属性值，并截取出 center 参数的内容
        center_coordinates = sel.xpath(
            'substring-before(substring-after(//section[@aria-label="Property map"]//div[contains(@style, "background-image")]/@style, "center="), "&")'
        ).get()

        # 如果成功提取到了坐标字符串，拆分为纬度和经度
        if center_coordinates:
            latitude, longitude = center_coordinates.split(",")
            print("纬度:", latitude)  # 输出 -37.7334201
            print("经度:", longitude)  # 输出 144.7981836
        else:
            print("未能提取坐标信息")

        # Agent information
        # 提取 Agent 的姓名（h3 标签内的文字）
        agent_name = sel.xpath('//section[@aria-label="Contact the real estate agent"]//article//h3/text()').get()
        agent_name = agent_name.strip() if agent_name else None

        # 提取 Agent 的所属机构（h4 标签内的文字）
        agent_office = sel.xpath('//section[@aria-label="Contact the real estate agent"]//article//h4/text()').get()
        agent_office = agent_office.strip() if agent_office else None

        # 提取 Agent 的个人主页链接（profile），从 <a> 标签的 href 属性中提取
        agent_profile = sel.xpath(
            '//section[@aria-label="Contact the real estate agent"]//article//a[@aria-label][1]/@href').get()
        agent_profile = agent_profile.strip() if agent_profile else None

        # 修改电话号码提取方式：选择所有带有 href 且 href 属性以 "tel:" 开头的元素（不局限于 a 标签）
        agent_phone_href = sel.xpath(
            '//section[@aria-label="Contact the real estate agent"]//*[@href][starts-with(@href, "tel:")]/@href').get()
        agent_phone = agent_phone_href.replace("tel:", "").strip() if agent_phone_href else None

        # 输出结果
        print("Agent Name:", agent_name)
        print("Agent Office:", agent_office)
        print("Agent Profile URL:", agent_profile)
        print("Agent Phone:", agent_phone)

        # 构造初始 item，对应数据库模型中的各字段
        item = {
            "name": self.name,
            "url": response.url,
            "external_id": self.extract_external_id(response.url),
            "address": full_address,
            "title": full_address,
            "suburb": city,
            "state": city, # TODO:
            "postcode": postcode,
            "price_text": price_text,
            "lower_price": lower_price if lower_price else 0,
            "upper_price": upper_price if upper_price else 0,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "car_spaces": car_spaces,
            "property_type": property_type,
            "description": description,
            "council_rates": council_rates,
            "land_area": area_number,
            "pdf_document": [],
            "origin_pdf_document": document_links,
            "latitude": latitude if latitude else 0,
            "longitude": longitude if longitude else 0,
            # 后续将 gallery 中获取的图片 URL 列表填入此字段，Pipeline 负责下载及映射构造
            "images": [],
            "origin_images": [],
            "floor_plan": [],
            "origin_floor_plan": [],
            "publish_date": datetime.utcnow(),

            # agent
            "agent_name": agent_name,
            "agent_phone": agent_phone,
            "agent_agency": agent_office,
            "agent_profile_url": agent_profile,
        }

        # 调用 parse_gallery 模拟点击 gallery 按钮并获取图片 URL
        result = self.parse_gallery()

        if result and len(result) == 2:
            # item["images"], item["floor_plan"] = result
            a, b = result
            # 合并两个数组给到front_image_url
            item["origin_images"] = a + b
        else:
            item["origin_images"] = []
            # item["images"], item["floor_plan"] = [], []

        if item["external_id"] is not None:
            yield item
        else:
            logger.error(f"No external id found: {response.url}")

    def parse_gallery(self):
        """
        模拟点击 Gallery 按钮，等待 AJAX 加载出图片数据，然后返回图片 URL 列表。
        """
        try:
            # 定位 Gallery 按钮（假设选择第一个按钮即可）
            gallery_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div[aria-label='Gallery button bar'] button:first-of-type")
                )
            )
            # 滚动使按钮可见后点击（先尝试常规点击，失败后使用 JavaScript 点击）
            self.driver.execute_script("arguments[0].scrollIntoView(true);", gallery_button)
            time.sleep(5)
            try:
                gallery_button.click()
                logger.info("Clicked Gallery button successfully.")
            except Exception as click_exception:
                logger.warning("Standard click failed, using JavaScript click. Error: %s", click_exception)
                self.driver.execute_script("arguments[0].click();", gallery_button)
                logger.info("JavaScript click on Gallery button succeeded.")
            # 等待页面 AJAX 加载出图片展示区域
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[aria-label='Vertical image gallery']")
                )
            )
            time.sleep(2)  # 保证数据加载完全
        except Exception as e:
            logger.error("Error clicking or loading gallery: %s", e)
            return [],[]

        # 滚动到页面底部确保图片全部加载
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

        # 利用 Selector 解析加载后的页面
        page_source = self.driver.page_source

        # debug
        with open("p3.html", "w", encoding="utf-8") as f:
            f.write(page_source)

        sel = Selector(text=page_source)

        # 限定在垂直图库区域中查找
        gallery = sel.xpath('//div[@aria-label="Vertical image gallery"]')

        images = []
        floorplan = []

        for img in gallery.xpath('.//img'):
            src = img.xpath('./@src').get()
            if not src:
                continue
            # 获取当前 img 元素之前的所有 h2 元素
            preceding_h2s = img.xpath('preceding::h2')
            if preceding_h2s:
                # 获取最近的一个 h2 元素的文本
                last_h2_text = preceding_h2s[-1].xpath('normalize-space()').get()
                if last_h2_text:
                    if "Floor plan" in last_h2_text:
                        floorplan.append(src)
                    elif "Photo" in last_h2_text or "Photos" in last_h2_text:
                        images.append(src)

        return images, floorplan

    def extract_external_id(self, url):
        """
        从 URL 中提取房产的唯一标识 external_id，例如：
          https://www.homely.com.au/homes/105-conrad-street-st-albans-vic-3021/11105399
        返回 '11105399'
        """
        pattern = re.compile(r'/(\d+)/?$')
        match = pattern.search(url)
        if match:
            return match.group(1)
        return None

    def parse_price(self, price_text):
        """
        解析价格字符串，返回 (price_low, price_high) 元组。

        支持的价格样式包括：
          1. 区间价格，使用“-”作为分隔符：
             "$1,460,000 - $1,600,000"
          2. 区间价格，使用 "to" 作为分隔符：
             "$770,000 to $820,000"
          3. 单一价格（只有一个数值）：
             "$249,500"
          4. 带有状态前缀（例如“For Sale - $1,799,000”）：
             "For Sale - $1,799,000"
          5. 带有状态前缀，但无连接符：
             "For Sale $1,800,000"
          6. 带有额外描述和区间的：
             "Expressions of Interest | $3,900,000 - $4,290,000"

        对于单一价格，将 lower 与 upper 都设为相同数值；对于区间价格，
        将两个数字分别赋值给 price_low 和 price_high。

        测试：
            # 示例测试各个价格样式
            examples = [
                "$1,460,000 - $1,600,000",  # 区间价格，用 - 分隔
                "$770,000 to $820,000",  # 区间价格，用 "to" 分隔
                "$249,500",  # 单一价格
                "For Sale - $1,799,000",  # 带状态前缀和 - 的单一价格
                "For Sale $1,800,000",  # 带状态前缀（无连接符）的单一价格
                "Expressions of Interest | $3,900,000 - $4,290,000"  # 带描述和区间价格
            ]

            for example in examples:
                low, high = parse_price(example)
                print(f"原始字符串: {example}\n解析结果: price_low={low}, price_high={high}\n")
        """


        if not price_text:
            return None, None

        # 去除首尾空格
        price_text = price_text.strip()

        # 如果有额外的描述信息，例如：
        #   "For Sale - $1,799,000" 或 "Expressions of Interest | $3,900,000 - $4,290,000"
        # 则去除描述，保留美元符号开始的部分
        # 这里查找第一个 "$" 出现的位置，从该位置截取子串
        dollar_index = price_text.find('$')
        if dollar_index != -1:
            price_text = price_text[dollar_index:]

        # 注：此时 price_text 可能是以下格式之一：
        #   "$1,460,000 - $1,600,000"
        #   "$770,000 to $820,000"
        #   "$249,500"
        #   "$1,799,000"
        #   "$1,800,000"
        #   "$3,900,000 - $4,290,000"

        # 优先尝试匹配价格区间，支持 "-" 或 "to" 作为分隔符
        range_pattern = re.compile(r'\$?([\d,]+)\s*(?:-|to)\s*\$?([\d,]+)', re.IGNORECASE)
        range_match = range_pattern.search(price_text)
        if range_match:
            try:
                lower_price = int(range_match.group(1).replace(',', '').strip())
                upper_price = int(range_match.group(2).replace(',', '').strip())
                return lower_price, upper_price
            except ValueError as e:
                print("价格转换错误:", e)
                return None, None

        # 如果未匹配到区间格式，则尝试匹配单一价格格式
        single_pattern = re.compile(r'\$([\d,]+)')
        single_match = single_pattern.search(price_text)
        if single_match:
            try:
                price = int(single_match.group(1).replace(',', '').strip())
                # 单一价格，下限和上限均为相同数值
                return price, price
            except ValueError as e:
                print("价格转换错误:", e)
                return None, None

        # 若上述均不匹配，则返回 (None, None)
        return None, None

    def parse_postcode(self, address_text):
        """
        解析地址中的 postcode（邮政编码）。

        支持格式包括：
          1. 地址文本中可能包含城市、州以及邮政编码，例如 "Abbotsford VIC 3067"
          2. 邮政编码通常为 4 位数字（如 3067）

        参数:
          address_text (str): 从网页中提取的地址详情，例如 "Abbotsford VIC 3067"

        返回:
          str 或 None: 如果能匹配到 4 位数字，则返回该邮政编码；否则返回 None。
        """
        if not address_text:
            return None

        # 使用正则表达式匹配 4 位数字，\b 用于确保匹配边界
        match = re.search(r'\b\d{4}\b', address_text)
        if match:
            return match.group()
        return None