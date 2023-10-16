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

```python
from ymrp.parser import Parser

p = Parser()
reviews = p.get_yandex_reviews()

for review in reviews:
    print(review)

```
