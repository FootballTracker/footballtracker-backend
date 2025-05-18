# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

# TODO: use the pipeline to parse the data of matches for how many pages will be needed
class FlamengoScraperPipeline:
    def process_item(self, item, spider):
        return item
