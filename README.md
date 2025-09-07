# ymrp

## Requirements

YMRP stands on the shoulders of:
 - python 3.13
 - playwright
 - beautifulsoup4

## Installation

Create and activate a virtual environment and then install YMRP:

```sh
pip install ymrp
```

Install playwright dependencies

```sh
playwright install chromium
playwright install-deps
```

## Example

Get business reviews from yandex map

```python
from ymrp.parser import Parser

url = 'https://yandex.ru/maps/10875/lomonosov/?from=mapframe&ll=29.770779%2C59.913080&mode=poi&poi%5Bpoint%5D=29.770747%2C59.913078&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D1245233699&tab=reviews&z=20.34'

parser = Parser()
reviews = parser.get_yandex_reviews(url)

for review in reviews:
    print(review)

```

Get business products and services from yandex map

```python
from ymrp.parser import Parser

url = 'https://yandex.ru/maps/10875/lomonosov/?from=mapframe&ll=29.770779%2C59.913080&mode=poi&poi%5Bpoint%5D=29.770747%2C59.913078&poi%5Buri%5D=ymapsbm1%3A%2F%2Forg%3Foid%3D1245233699&tab=prices&z=20.34'

parser = Parser()
products_and_services = parser.get_yandex_products_and_services(url)

for product_or_service in products_and_services:
    print(product_or_service)

```

Note: images size can be S, M, L, XL and XXL.
