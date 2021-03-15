import time
from selenium.webdriver.common.keys import Keys
import json
from selenium.common.exceptions import NoSuchElementException

from amazon_config import (
    get_web_driver_options,
    get_chrome_web_driver,
    set_browser_as_incognito,
    set_ignore_certificate_error,
    # set_automation_as_head_less,
    NAME,
    CURRENCY,
    FILTERS,
    BASE_URL,
    DIRECTORY
)

class GenerateReport:
    def __init__(self):
        pass


class AmazonAPI:
    def __init__(self, search_term, filters, base_url, currency):
        self.base_url = base_url
        self.search_term = search_term
        options = get_web_driver_options()
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        self.driver = get_chrome_web_driver(options)
        self.currency = currency
        self.price_filter = f"&rh=p_36%3A{filters['min']}00-{filters['max']}00"

    def run(self):
        print('Starting script...')
        print(f'looking for {self.search_term} products...')
        links = self.get_products_link()
        time.sleep(2)
        if not links:
            print('Stopped scripts. No links found.')
            return
        print(f'Got {len(links)} links to products...')
        print('Getting info about products...')
        products = self.get_products_info(links)
        

        self.driver.quit()

    def get_products_info(self, links):
        asins = self.get_asins(links)
        products = []
        for asin in asins:
            product = self.get_single_product_info(asin)
            print(json.dumps(product))

    def get_single_product_info(self, asin):
        print(f'Product ID: {asin} - Getting Data...')
        product_short_url = self.shorten_url(asin)
        self.driver.get(f'{product_short_url}?language=en_GB')
        time.sleep(2)
        title = self.get_title()
        seller = self.get_seller()
        price = self.get_price()
        if title and seller and price:
            product_info = {
                'asin': asin,
                'url': product_short_url,
                'title': title,
                'seller': seller,
                'price': price
            }
            return product_info
        return None

    def get_title(self):
        try:
            return self.driver.find_element_by_id('productTitle').text
        except Exception as e:
            print(e)
            print(f"Can't get title of a product - {self.driver.current_url}")
            return None

    def get_seller(self):
        try:
            return self.driver.find_element_by_id('bylineInfo').text
        except Exception as e:
            print(e)
            print(f"Can't get seller of a product - {self.driver.current_url}")
            return None

    def get_price(self):
        price = None
        try:
            price = self.driver.find_element_by_id('priceblock_ourprice').text
            price = self.convert_price(price)
        except NoSuchElementException:
            try:
                availability = self.driver.find_element_by_id('availability').text
                if 'Available' in availability:
                    price = self.driver.find_element_by_class_name('olp-padding-right').text
                    price = price[price.find(self.currency):]
                    price = self.convert_price(price)
            except Exception as e:
                print(e)
                print(f"Can't get price of a product - {self.driver.current_url}")
                return None
        except Exception as e:
            print(e)
            print(f"Can't get price of a product - {self.driver.current_url}")
            return None
        return price
    
    def shorten_url(self, asin):
        return self.base_url + 'dp/' + asin

    def convert_price(self, price):
        price = price.split(self.currency)[1]
        try:
            price = price.split("\n")[0] + "." + price.split("\n")[1]
        except:
            Exception()
        try:
            price = price.split(",")[0] + price.split(",")[1]
        except:
            Exception()
        return float(price)
    
    def get_asins(self, links):
        return [self.get_asin(link) for link in links]

    @staticmethod
    def get_asin(product_link):
        return product_link[product_link.find('/dp/') + 4:product_link.find('/ref')]
    


    def get_products_link(self):
        self.driver.get(self.base_url)
        #element = self.driver.find_element_by_xpath('//*[@id="twotabsearchtextbox"]')
        element = self.driver.find_element_by_id('twotabsearchtextbox')
        element.send_keys(self.search_term)
        element.send_keys(Keys.ENTER)
        time.sleep(2)
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        print(f"Our url: {self.driver.current_url}")
        result_list = self.driver.find_elements_by_class_name('s-result-list')
        links = []
        try:
            results = result_list[0].find_elements_by_xpath(
                "//div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a")
            links = [link.get_attribute('href') for link in results]
            return links
        except Exception as e:
            print("Didn't get any products...")
            print(e)
            return links



if __name__ == '__main__':
    print('hello')
    amazon = AmazonAPI(NAME, FILTERS, BASE_URL, CURRENCY)
    amazon.run()