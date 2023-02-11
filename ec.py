__author__ = 'norsulfazol'
__version__ = '1.1.0'

from selenium.webdriver.support.expected_conditions import *
from selenium.common.exceptions import InvalidSelectorException


def title_contains_lower(title):
    """
    An expectation for checking that the title contains a case-insensitive (lower) substring.
    """

    def _predicate(driver):
        return title.lower() in driver.title.lower()

    return _predicate


def displayed_of_element(locator):
    """
    An expectation for checking that the element is present in the DOM of the page
    and visible or the css property "display" is not equal to "none".
    """

    def _predicate(driver):
        try:
            element = driver.find_element(*locator)
            return element if element.is_displayed() or element.value_of_css_property('display') != 'none' else False
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate


def not_displayed_of_element(locator):
    """
    An expectation for checking that the element is not present in the DOM of the page
    or invisible or the css property "display" is equal to "none".
    """

    def _predicate(driver):
        try:
            element = driver.find_element(*locator)
            return element if not element.is_displayed() or element.value_of_css_property(
                'display') == 'none' else False
        except InvalidSelectorException as e:
            raise e
        except (NoSuchElementException, StaleElementReferenceException):
            return True

    return _predicate


def value_to_be_equal_to_css_property_value_of_element(locator, css_property, value):
    """
    An expectation for checking if the passed value is equal to the css property value of the specified element.
    """

    def _predicate(driver):
        try:
            element_value = driver.find_element(*locator).value_of_css_property(css_property)
            return value == element_value
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate


def element_attribute_to_include(locator, attribute_):
    """
    An expectation for checking if the given attribute is included in the specified element.
    """

    def _predicate(driver):
        try:
            element_attribute = driver.find_element(*locator).get_attribute(attribute_)
            return element_attribute is not None
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate


def text_to_be_present_in_element_attribute(locator, attribute_, text_):
    """
    An expectation for checking if the given text is present in the element's attribute.
    """

    def _predicate(driver):
        try:
            if not element_attribute_to_include(locator, attribute_)(driver):
                return False
            element_text = driver.find_element(*locator).get_attribute(attribute_)
            return text_ in element_text
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate


def value_to_be_equal_to_attribute_value_of_element(locator, attribute_, value):
    """
    An expectation for checking if the passed value is equal to the attribute value of the specified element.
    """

    def _predicate(driver):
        try:
            if not element_attribute_to_include(locator, attribute_)(driver):
                return False
            element_value = driver.find_element(*locator).get_attribute(attribute_)
            return value == element_value
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate


def element_property_to_include(locator, property_):
    """
    An expectation for checking if the given property is included in the specified element.
    """

    def _predicate(driver):
        try:
            element_property = driver.find_element(*locator).get_property(property_)
            return element_property is not None
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate


def text_to_be_present_in_element_property(locator, property_, text_):
    """
    An expectation for checking if the given text is present in the element's property.
    """

    def _predicate(driver):
        try:
            if not element_property_to_include(locator, property_)(driver):
                return False
            element_text = driver.find_element(*locator).get_property(property_)
            return text_ in element_text
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate


def value_to_be_equal_to_property_value_of_element(locator, property_, value):
    """
    An expectation for checking if the passed value is equal to the property value of the specified element.
    """

    def _predicate(driver):
        try:
            if not element_property_to_include(locator, property_)(driver):
                return False
            element_value = driver.find_element(*locator).get_property(property_)
            return value == element_value
        except InvalidSelectorException as e:
            raise e
        except StaleElementReferenceException:
            return False

    return _predicate
