from datetime import datetime

from playwright.sync_api import sync_playwright

MONTHS = {
    'января': '01',
    'февраля': '02',
    'марта': '03',
    'апреля': '04',
    'мая': '05',
    'июня': '06',
    'июля': '07',
    'августа': '08',
    'сентября': '09',
    'октября': '10',
    'ноября': '11',
    'декабря': '12',
}


class Parser:
    def get_reviews_html_content(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)

            page.wait_for_timeout(15000)

            reviews_container = page.locator(
                '.business-reviews-card-view__reviews-container'
            )
            reviews_container.click(button='left')

            last_review = None
            prev_review_count, review_count = 0, 0

            while True:
                page.wait_for_timeout(10000)

                last_review = page.locator(
                    '.business-reviews-card-view__review'
                )
                review_count = last_review.count()
                last_review = last_review.last

                last_review.click(button='left')

                if prev_review_count == review_count:
                    break

                prev_review_count = review_count

            more_buttons = page.locator(
                '.business-review-view__expand[aria-hidden="false"]'
            ).all()
            iterations = 0
            while iterations < 10 or len(more_buttons) != 0:
                more_buttons = page.locator(
                    '.business-review-view__expand[aria-hidden="false"]'
                ).all()
                for button in more_buttons:
                    try:
                        page.wait_for_timeout(2000)
                        button.click(button='left', timeout=2000)
                    except Exception:
                        pass
                iterations += 1

            page.wait_for_timeout(2000)

            reviews_container = page.locator(
                '.business-reviews-card-view__reviews-container'
            )
            return reviews_container.inner_html()

    def convert_date(self, date_str: str) -> str:
        parts = date_str.split()
        if len(parts) == 3:
            day, month_name, year = parts
        else:
            day, month_name = parts
            year = str(datetime.now().year)
        month = MONTHS.get(month_name, '01')
        return f'{year}-{month}-{day.zfill(2)}'
