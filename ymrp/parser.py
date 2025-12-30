from typing import Any

from .parsers import reviews, products_and_services as ps  # noqa: WPS300


class Parser:
    """Main parser class combining HTML scraping and parsing functionality."""

    def __init__(self) -> None:
        """
        Initialize parser with required components.

        Creates instances of all necessary parser and scraper classes.
        """
        self.ymrhcp = reviews.YandexMapReviewsHtmlCodeParser()
        self.ymrp = reviews.YandexMapReviewsParser()
        self.ympashcp = ps.YandexMapProductsAndServicesHtmlCodeParser()
        self.ympasp = ps.YandexMapProductsAndServicesParser()

    def get_yandex_reviews(self, url: str) -> list[dict[str, Any]]:
        """
        Get parsed reviews from Yandex Maps URL.

        Args:
            url: URL of the Yandex Maps business page.

        Returns:
            List of dictionaries containing parsed review data.

        Example:
            >>> url = 'https://yandex.ru/maps/org/...'
            >>> parser = Parser()
            >>> reviews = parser.get_yandex_reviews(url)
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

        Example:
            >>> url = 'https://yandex.ru/maps/org/...'
            >>> parser = Parser()
            >>> products = parser.get_yandex_products_and_services(url)
        """
        html_content = self.ympasp.get_products_and_services_html_content(url)
        return self.ympashcp.parse_yandex_products_and_services(html_content)
