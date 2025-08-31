from datetime import datetime
from typing import Any, Literal

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Locator, Page, sync_playwright

from . import constants  # noqa: WPS300


class YandexMapParser:
    def _click_on_element(
        self,
        element: Locator,
        button: Literal['left', 'middle', 'right'] = 'left',
        timeout: int = constants.VERY_SMALL_TIMEOUT,
    ) -> bool:
        """
        Safely click on a Playwright element with error handling.

        Args:
            element: Playwright Locator object.
            button: Mouse button to use for click.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if click succeeded, False if failed.
        """
        try:
            element.click(button=button, timeout=timeout)
        except Exception:
            return False
        else:
            return True


class YandexMapProductsAndServicesHtmlCodeParser:
    """
    Parser for extracting products and services data from Yandex Maps.
    """

    def parse_yandex_products_and_services(
        self,
        html_content: str = '',
    ) -> list[dict[str, Any]]:
        """
        Parse HTML content containing Yandex Maps products and services.
        """

        soup = BeautifulSoup(html_content, 'html.parser')
        products_and_services = []
        category_groups = soup.find_all(
            constants.DIV,
            class_=constants.CATEGORY_GROUP,
        )
        for category_group in category_groups:
            if isinstance(category_group, Tag):
                products_and_services.extend(
                    self._parse_category_group(category_group),
                )
        return products_and_services

    def _parse_category_group(
        self,
        category_group: Tag,
    ) -> list[dict[str, Any]]:
        category_products_and_services = []
        category_title = category_group.find(
            constants.DIV,
            class_=constants.CATEGORY_TITLE,
        )
        group_name = (
            category_title.get_text(strip=True)
            if category_title
            else 'Без категории'
        )
        category_group_items = category_group.find_all(
            constants.DIV,
            class_=constants.CATEGORY_GROUP_ITEM,
        )
        for category_group_item in category_group_items:
            if isinstance(category_group_item, Tag):
                category_products_and_services.append(
                    {
                        'group_name': group_name,
                        'title': self._parse_product_or_service_title(
                            product_or_service=category_group_item,
                        ),
                        'description':
                        self._parse_product_or_service_description(
                            product_or_service=category_group_item,
                        ),
                        'price': self._parse_product_or_service_price(
                            product_or_service=category_group_item,
                        ),
                        'image_url': self._parse_product_or_service_image(
                            product_or_service=category_group_item,
                        ),
                    }
                )
        return category_products_and_services

    def _parse_product_or_service_title(
        self,
        product_or_service: Tag,
    ) -> str | None:
        if isinstance(product_or_service, Tag):
            title_elem = product_or_service.find(
                constants.DIV,
                class_=constants.PRODUCT_TITLE_CLASS,
            )
            if title_elem:
                return title_elem.get_text(strip=True)
        return None

    def _parse_product_or_service_description(
        self,
        product_or_service: Tag,
    ) -> str | None:
        desc_elem = product_or_service.find(
            constants.DIV,
            class_=constants.PRODUCT_DESCRIPTION_CLASS,
        )
        if desc_elem:
            return desc_elem.get_text(strip=True)
        return None

    def _parse_product_or_service_price(
        self,
        product_or_service: Tag,
    ) -> str | None:
        price_elem = product_or_service.find(
            constants.SPAN,
            class_=constants.PRODUCT_PRICE_CLASS,
        )
        if price_elem:
            return price_elem.get_text(strip=True)
        return None

    def _parse_product_or_service_image(
        self,
        product_or_service: Tag,
    ) -> Any:
        img_elem = product_or_service.find(
            'img',
            class_=constants.PRODUCT_IMAGE_CLASS,
        )
        if isinstance(img_elem, Tag):
            if img_elem and img_elem.get('src'):
                return img_elem['src']
        return None


class YandexMapProductsAndServicesParser(YandexMapParser):
    """
    Scraper for retrieving Yandex Maps products and services using Playwright.
    """

    def get_products_and_services_html_content(self, url: str) -> str:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector(
                constants.CATEGORIES_CONTAINER,
                timeout=constants.BIG_TIMEOUT,
                state='visible',
            )
            page.wait_for_timeout(constants.SMALL_TIMEOUT)
            self._view_all_categories(page)
            page.wait_for_timeout(constants.SMALL_TIMEOUT)
            reviews_container = page.locator(constants.CATEGORIES_CONTAINER)
            return reviews_container.inner_html()

    def _view_all_categories(self, page: Page) -> None:
        last_category = None
        prev_category_count, category_count = 0, 0
        while True:
            page.wait_for_timeout(constants.MEDIUM_TIMEOUT)
            last_category = page.locator(constants.CATEGORY)
            category_count = last_category.count()
            last_category = last_category.last
            self._click_on_element(last_category)
            if prev_category_count == category_count:
                break
            prev_category_count = category_count
        page.wait_for_timeout(constants.MEDIUM_TIMEOUT)
        categories = page.locator(constants.CATEGORY)
        for index in range(categories.count()):
            try:
                categories.nth(index).scroll_into_view_if_needed()
            except Exception:
                ...
            finally:
                page.wait_for_timeout(constants.SMALL_TIMEOUT)


class YandexMapReviewsHtmlCodeParser:
    """Parser for extracting review data from Yandex Maps HTML content."""

    def parse_yandex_reviews(
        self,
        html_content: str = '',
    ) -> list[dict[str, Any]]:
        """
        Parse HTML content containing Yandex Maps reviews into structured data.

        Args:
            html_content: String containing HTML of reviews section.

        Returns:
            List of dicts with parsed review data, each containing:
            - name: Reviewer's name
            - rating: Numerical rating (1-5)
            - text: Full review text
            - date: Formatted date string (YYYY-MM-DD)

        Note:
            Silently skips any reviews that fail to parse.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        review_cards = soup.find_all(
            constants.DIV,
            class_=constants.REVIEW_CLASS,
        )
        reviews: list[dict[str, Any]] = []
        for review in review_cards:
            try:
                if isinstance(review, Tag):
                    reviews.append(self.parse_yandex_review(review))
            except Exception:
                ...
        return reviews

    def parse_yandex_review(self, review: Tag) -> dict[str, Any]:
        """Parse an individual review Tag into structured data.

        Args:
            review: BeautifulSoup Tag object representing a single review card.

        Returns:
            Dictionary containing parsed review data with keys:
            - name: Reviewer's name
            - rating: Numerical rating (1-5)
            - text: Full review text
            - date: Formatted date string (YYYY-MM-DD)

        Raises:
            Exception: If any required review field cannot be parsed.
        """
        return {
            'name': self._parse_review_name(review),
            'rating': self._parse_review_rating(review),
            'text': self._parse_review_text(review),
            'date': self._parse_review_date(review),
        }

    def _parse_review_name(self, review: Tag) -> str | None:
        """Extract reviewer name from review Tag.

        Args:
            review: BeautifulSoup Tag object of a review.

        Returns:
            Reviewer's name as string.

        Raises:
            Exception: If name element cannot be found.
        """
        name = review.find(constants.SPAN, itemprop='name')
        if name:
            return str(name.text.strip())
        return None

    def _parse_review_rating(self, review: Tag) -> int:
        """Extract numerical rating from review Tag.

        Args:
            review: BeautifulSoup Tag object of a review.

        Returns:
            Integer rating value (1-5).

        Note:
            Converts the rating from string to integer.
        """
        rating = review.find(
            'meta',
            itemprop='ratingValue',
        )[
            'content'
        ]  # type: ignore
        return int(float(rating))

    def _parse_review_text(self, review: Tag) -> str | None:
        """Extract review text content from review Tag.

        Args:
            review: BeautifulSoup Tag object of a review.

        Returns:
            Full text content of the review.

        Raises:
            Exception: If review text element cannot be found.
        """
        review_text = review.find(
            constants.SPAN,
            class_=constants.REVIEW_TEXT_CLASS,
        )
        if review_text:
            return str(review_text.text.strip())
        return None

    def _parse_review_date(self, review: Tag) -> str | None:
        """Extract and format review date from review Tag.

        Args:
            review: BeautifulSoup Tag object of a review.

        Returns:
            Date string formatted as YYYY-MM-DD.

        Raises:
            Exception: If date element cannot be found.
        """
        date = review.find(
            constants.SPAN,
            class_=constants.REVIEW_DATE_CLASS,
        )
        if date:
            return self._convert_date(date.text.strip())
        return None

    def _convert_date(self, date_str: str) -> str:
        """Convert Russian date string to ISO format (YYYY-MM-DD).

        Args:
            date_str: Date string in Russian format (e.g., "12 мая 2023").

        Returns:
            Date string in ISO format (YYYY-MM-DD).

        Note:
            Uses current year if year is not specified in input string.
        """
        parts = date_str.split()
        if len(parts) == 3:
            day, month_name, year = parts
        else:
            day, month_name = parts
            year = str(datetime.now().year)
        month = constants.months.get(month_name, '01')
        return f'{year}-{month}-{day.zfill(2)}'


class YandexMapReviewsParser(YandexMapParser):
    """Scraper for retrieving Yandex Maps reviews using Playwright."""

    def get_reviews_html_content(self, url: str) -> str:
        """
        Retrieve HTML content of reviews from Yandex Maps page.

        Args:
            url: URL of the Yandex Maps business page.

        Returns:
            HTML content string of the reviews section.

        Note:
            Performs browser automation to:
            1. Load all available reviews
            2. Expand all review texts
            3. Return the complete HTML
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(url)

            reviews_container = page.locator(constants.REVIEWS_CONTAINER)
            page.wait_for_selector(
                constants.REVIEWS_CONTAINER,
                timeout=constants.BIG_TIMEOUT,
                state='visible',
            )

            self._click_on_element(reviews_container)
            self._view_all_reviews(page)
            self._expand_all_reviews(page)

            page.wait_for_timeout(constants.SMALL_TIMEOUT)

            reviews_container = page.locator(constants.REVIEWS_CONTAINER)
            return reviews_container.inner_html()

    def _view_all_reviews(self, page: Page) -> None:
        """
        Scroll through and load all available reviews.

        Args:
            page: Playwright Page object.
        """
        last_review = None
        prev_review_count, review_count = 0, 0

        while True:
            page.wait_for_timeout(constants.MEDIUM_TIMEOUT)

            last_review = page.locator(constants.REVIEW)
            review_count = last_review.count()
            last_review = last_review.last

            self._click_on_element(last_review)

            if prev_review_count == review_count:
                break

            prev_review_count = review_count

    def _expand_all_reviews(self, page: Page) -> None:
        """
        Expand all review texts by clicking "Read more" buttons.

        Args:
            page: Playwright Page object.

        Note:
            Makes multiple attempts to ensure all expand buttons are clicked.
        """
        more_buttons = page.locator(constants.REVIEW_VIEW_EXPAND).all()
        iterations = 0
        while iterations < 10 or len(more_buttons) != 0:
            more_buttons = page.locator(constants.REVIEW_VIEW_EXPAND).all()
            for button in more_buttons:
                self._click_on_element(button)
            iterations += 1


class Parser:
    """Main parser class combining HTML scraping and parsing functionality."""

    def __init__(self) -> None:
        """Initialize parser with required components."""
        self.ymrhcp = YandexMapReviewsHtmlCodeParser()
        self.ymrp = YandexMapReviewsParser()
        self.ympashcp = YandexMapProductsAndServicesHtmlCodeParser()
        self.ympasp = YandexMapProductsAndServicesParser()

    def get_yandex_reviews(self, url: str) -> list[dict[str, Any]]:
        """
        Get parsed reviews from Yandex Maps URL.

        Args:
            url: URL of the Yandex Maps business page.

        Returns:
            List of dictionaries containing parsed review data.
        """
        return self.ymrhcp.parse_yandex_reviews(
            html_content=self.ymrp.get_reviews_html_content(url)
        )

    def get_yandex_products_and_services(self, url: str) -> Any:
        """
        Get parsed products and services from Yandex Maps URL.

        Args:
            url: URL of the Yandex Maps business page.

        Returns:
            List of dictionaries containing parsed products and services data.
        """
        html_content = self.ympasp.get_products_and_services_html_content(url)
        return self.ympashcp.parse_yandex_products_and_services(html_content)
