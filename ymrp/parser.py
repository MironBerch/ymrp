from datetime import datetime
from typing import Any, Literal

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Locator, Page, sync_playwright

from .constants import (  # noqa: WPS300
    BIG_TIMEOUT,
    MEDIUM_TIMEOUT,
    REVIEW,
    REVIEW_VIEW_EXPAND,
    REVIEWS_CONTAINER,
    SMALL_TIMEOUT,
    VERY_SMALL_TIMEOUT,
    months,
)


class YandexMapReviewsHtmlCodeParser:
    def convert_date(self, date_str: str) -> str:
        parts = date_str.split()
        if len(parts) == 3:
            day, month_name, year = parts
        else:
            day, month_name = parts
            year = str(datetime.now().year)
        month = months.get(month_name, '01')
        return f'{year}-{month}-{day.zfill(2)}'

    def parse_yandex_review(
        self,
        review: Tag,
    ) -> dict[str, Any]:
        review_data = {}

        name = review.find('span', itemprop='name')
        if name:
            review_data['name'] = name.text.strip()

        rating = review.find('meta', itemprop='ratingValue')
        review_data['rating'] = int(float(rating['content']))  # type: ignore

        review_text = review.find(
            'span',
            class_='spoiler-view__text-container',
        )
        if review_text:
            review_data['text'] = review_text.text.strip()

        date = review.find(
            'span',
            class_='business-review-view__date',
        )
        if date:
            review_data['date'] = self.convert_date(date.text.strip())

        return review_data

    def parse_yandex_reviews(
        self,
        html_content: str = '',
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        review_cards = soup.find_all(
            'div',
            class_='business-reviews-card-view__review',
        )
        reviews: list[dict[str, Any]] = []
        for review in review_cards:
            try:
                if isinstance(review, Tag):
                    reviews.append(self.parse_yandex_review(review))
            except Exception:
                ...
        return reviews


class YandexMapReviewsParser:
    def get_reviews_html_content(self, url: str) -> str:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)

            reviews_container = page.locator(REVIEWS_CONTAINER)
            page.wait_for_selector(
                REVIEWS_CONTAINER,
                timeout=BIG_TIMEOUT,
                state='visible',
            )

            self._click_on_element(reviews_container)
            self._view_all_reviews(page)
            self._expand_all_reviews(page)

            page.wait_for_timeout(SMALL_TIMEOUT)

            reviews_container = page.locator(REVIEWS_CONTAINER)
            return reviews_container.inner_html()

    def _view_all_reviews(self, page: Page) -> None:
        last_review = None
        prev_review_count, review_count = 0, 0

        while True:
            page.wait_for_timeout(MEDIUM_TIMEOUT)

            last_review = page.locator(REVIEW)
            review_count = last_review.count()
            last_review = last_review.last

            self._click_on_element(last_review)

            if prev_review_count == review_count:
                break

            prev_review_count = review_count

    def _expand_all_reviews(self, page: Page) -> None:
        more_buttons = page.locator(REVIEW_VIEW_EXPAND).all()
        iterations = 0
        while iterations < 10 or len(more_buttons) != 0:
            more_buttons = page.locator(REVIEW_VIEW_EXPAND).all()
            for button in more_buttons:
                self._click_on_element(button)
            iterations += 1

    def _click_on_element(
        self,
        element: Locator,
        button: Literal['left', 'middle', 'right'] = 'left',
        timeout: int = VERY_SMALL_TIMEOUT,
    ) -> bool:
        try:
            element.click(button=button, timeout=timeout)
        except Exception:
            return False
        else:
            return True


class Parser:
    def __init__(self) -> None:
        self.ymrhcp = YandexMapReviewsHtmlCodeParser()
        self.ymrp = YandexMapReviewsParser()

    def get_yandex_reviews(self, url: str) -> list[dict[str, Any]]:
        return self.ymrhcp.parse_yandex_reviews(
            html_content=self.ymrp.get_reviews_html_content(url)
        )
