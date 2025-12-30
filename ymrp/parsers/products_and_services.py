from typing import Any

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Page, sync_playwright

from .. import constants  # noqa: WPS300


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

        Args:
            html_content: String containing HTML of products and services.

        Returns:
            List of dictionaries with parsed products and services data,
            each containing:
            - group_name: Category name
            - title: Product/service title
            - description: Product/service description
            - price: Product/service price
            - image_url: Product/service image URL
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
        """
        Parse a category group of products and services.

        Args:
            category_group: BeautifulSoup Tag object of a category group.

        Returns:
            List of dictionaries with parsed products/services in the category.
        """
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
        """
        Extract product or service title from Tag.

        Args:
            product_or_service: BeautifulSoup Tag object of a product/service.

        Returns:
            Product/service title as string or None if not found.
        """
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
        """
        Extract product or service description from Tag.

        Args:
            product_or_service: BeautifulSoup Tag object of a product/service.

        Returns:
            Product/service description as string or None if not found.
        """
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
        """
        Extract product or service price from Tag.

        Args:
            product_or_service: BeautifulSoup Tag object of a product/service.

        Returns:
            Product/service price as string or None if not found.
        """
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
        """
        Extract product or service image URL from Tag.

        Args:
            product_or_service: BeautifulSoup Tag object of a product/service.

        Returns:
            Product/service image URL as string or None if not found.
        """
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
        """
        Retrieve HTML content of products and services from Yandex Maps page.

        Args:
            url: URL of the Yandex Maps business page.

        Returns:
            HTML content string of the products and services section.

        Note:
            Performs browser automation to load all available categories
            and return the complete HTML content.
        """
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
        """
        Scroll through and load all available categories.

        Args:
            page: Playwright Page object.

        Note:
            Continuously clicks on the last category until no new categories
            are loaded to ensure all content is visible.
        """
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
