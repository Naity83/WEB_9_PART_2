import json
import scrapy
from itemadapter import ItemAdapter
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field

# Оголошення класу для елементів з цитатами
class QuoteItem(Item):
    tags = Field()
    author = Field()
    quote = Field()

# Оголошення класу для елементів з авторами
class AuthorItem(Item):
    fullname = Field()
    date_born = Field()
    location_born = Field()
    description = Field()

# Пайплайн для обробки та збереження даних
class QuotesPipline:
    quotes = []  # Список цитат
    authors = []  # Список авторів

    # Метод для обробки елементів
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        # Якщо елемент містить інформацію про автора, додати його в список авторів
        if 'fullname' in adapter.keys():
            self.authors.append({
                "fullname": adapter["fullname"],
                "date_born": adapter["date_born"],
                "location_born": adapter["location_born"],
                "description": adapter["description"],
            })
        # Якщо елемент містить цитату, додати її в список цитат
        if 'quote' in adapter.keys():
            self.quotes.append({
                "tags": adapter["tags"],
                "author": adapter["author"],
                "quote": adapter["quote"],
            })
        return

    # Метод для збереження даних у JSON-файли
    def close_spider(self, spider):
        with open('quotes.json', 'w', encoding='utf-8') as fd:
            json.dump(self.quotes, fd, ensure_ascii=False, indent=4)
        with open('authors.json', 'w', encoding='utf-8') as fd:
            json.dump(self.authors, fd, ensure_ascii=False, indent=4)

# Павук для збору даних
class QuotesSpider(scrapy.Spider):
    name = 'authors'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']
    custom_settings = {"ITEM_PIPELINES": {QuotesPipline: 300}}  # Використовувати пайплайн для обробки даних

    # Метод для обробки відповіді
    def parse(self, response, *args):
        for quote in response.xpath("/html//div[@class='quote']"):
            tags = quote.xpath("div[@class='tags']/a/text()").extract()
            author = quote.xpath("span/small/text()").get().strip()
            q = quote.xpath("span[@class='text']/text()").get().strip()
            # Повернути елемент з цитатою
            yield QuoteItem(tags=tags, author=author, quote=q)
            # Посилання на сторінку автора
            yield response.follow(url=self.start_urls[0] + quote.xpath('span/a/@href').get(),
                                  callback=self.nested_parse_author)
        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            # Перейти на наступну сторінку
            yield scrapy.Request(url=self.start_urls[0] + next_link)

    # Метод для обробки сторінки автора
    def nested_parse_author(self, response, *args):
        author = response.xpath('/html//div[@class="author-details"]')
        fullname = author.xpath('h3[@class="author-title"]/text()').get().strip()
        date_born = author.xpath('p/span[@class="author-born-date"]/text()').get().strip()
        location_born = author.xpath('p/span[@class="author-born-location"]/text()').get().strip()
        description = author.xpath('div[@class="author-description"]/text()').get().strip()
        # Повернути елемент з інформацією про автора
        yield AuthorItem(fullname=fullname, date_born=date_born, location_born=location_born, description=description)

# Початок виконання програми
if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.start()


