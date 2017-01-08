from operator import contains, eq

from selene.common.none_object import NoneObject
from selene.exceptions import ConditionNotSatisfiedException

or_not_to_be = lambda: True


class Condition(object):
    def __init__(self):
        self.found = NoneObject('Condition#found')

    def __call__(self, entity):
        self.entity = entity
        self.found = self.entity()  # todo: do we actually need it?
        # while we have self.found = wait_for(...
        if self.apply():
            return self.found
        else:
            raise ConditionNotSatisfiedException

        return self.found if self.apply() else None

    # todo: change this method to only stringify condition name and parameters,
    # todo:  and everything else should be provided in some describe method...
    def __str__(self):
        expected_string = str(self.expected()) if (self.expected() is not None) else ""
        actual_string = str(self.actual()) if (self.actual() is not None) else ""
        return """
            for {element} located by: {locator}
            \texpected: {expected}
            \t  actual: {actual}
        """.format(element=self.identity(),
                   locator=self._get_entity_locator(self.entity),
                   expected=expected_string,
                   actual=actual_string)

    def _get_entity_locator(self, entity):
        locator = entity._locator
        if self._is_chained_locator(locator):
            parent_locator = self._get_entity_locator(locator._element)
            return "{} > {}".format(parent_locator, locator._by)
        return locator._by

    def _is_chained_locator(self, locator):
        try:
            return locator._element
        except AttributeError:
            return False

    def description(self):
        return "%s expecting: %s" % (self.__class__.__name__, self.expected())

    def identity(self):
        return "element"

    def expected(self):
        return ''

    def actual(self):
        return ''

    def apply(self):
        return False

    def matches_webelement(self, webelement):
        self.found = webelement
        try:
            return self.apply()
        except Exception:
            return False

    def matches(self, entity):
        try:
            return self(entity)
        except Exception:
            return False


class CollectionCondition(Condition):
    def identity(self):
        return "elements"


class text(Condition):
    def __init__(self, expected_text):
        self.expected_text = expected_text
        self.actual_text = None

    def compare_fn(self):
        return contains

    def apply(self):
        self.actual_text = self.found.text.encode('utf-8')
        return self.compare_fn()(self.actual_text, self.expected_text)

    def expected(self):
        return self.expected_text

    def actual(self):
        return self.actual_text


class exact_text(text):
    def compare_fn(self):
        return eq


class Visible(Condition):
    def apply(self):
        return self.found.is_displayed()


visible = Visible()


class Clickable(Condition):
    def apply(self):
        return self.found.is_displayed and self.found.is_enabled()


clickable = Clickable()


class Enabled(Condition):
    def apply(self):
        return self.found.is_enabled()


enabled = Enabled()


# todo: consider renaming it to something else, because in jSelenide exist = visible
class Exist(Condition):
    """
    checks if element exist in DOM
    """

    def apply(self):
        return True


exist = Exist()
in_dom = exist


class Hidden(Condition):
    def apply(self):
        return not self.found.is_displayed()


hidden = Hidden()


class css_class(Condition):
    def __init__(self, class_attribute_value):
        # type: (str) -> None
        self.expected_containable_class = class_attribute_value
        self.actual_class = ''  # type: str

    def apply(self):
        self.actual_class = self.found.get_attribute("class")
        return self.expected_containable_class in self.actual_class.split()

    def expected(self):
        return self.expected_containable_class

    def actual(self):
        return self.actual_class


class attribute(Condition):
    def __init__(self, name, value):
        # type: (str, str) -> None
        self.name = name
        self.expected_value = value
        self.actual_value = ''  # type: str

    def apply(self):
        self.actual_value = self.found.get_attribute(self.name)
        return self.actual_value == self.expected_value

    def expected(self):
        return self.expected_value

    def actual(self):
        return self.actual_value


blank = attribute('value', '')


#########################
# COLLECTION CONDITIONS #
#########################


class texts(CollectionCondition):
    def __init__(self, *expected_texts):
        self.expected_texts = expected_texts
        self.actual_texts = None

    def compare_fn(self):
        return contains

    def apply(self):
        self.actual_texts = [item.text.encode('utf-8') for item in self.found]
        return len(self.actual_texts) == len(self.expected_texts) and \
               all(map(self.compare_fn(), self.actual_texts, self.expected_texts))

    def expected(self):
        return self.expected_texts

    def actual(self):
        return self.actual_texts


class exact_texts(texts):
    def compare_fn(self):
        return eq


class size(CollectionCondition):
    def __init__(self, expected_size):
        self.expected_size = expected_size
        self.actual_size = None

    def apply(self):
        self.actual_size = len(self.found)
        return self.actual_size == self.expected_size

    def expected(self):
        return self.expected_size

    def actual(self):
        return self.actual_size


empty = size(0)


class size_at_least(CollectionCondition):
    def __init__(self, minimum_size):
        self.minimum_size = minimum_size
        self.actual_size = None

    def apply(self):
        self.actual_size = len(self.found)
        return self.actual_size >= self.minimum_size

    def expected(self):
        return self.minimum_size

    def actual(self):
        return self.actual_size
