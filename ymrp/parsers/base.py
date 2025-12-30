from typing import Literal

from playwright.sync_api import Locator

from .. import constants  # noqa: WPS300


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
