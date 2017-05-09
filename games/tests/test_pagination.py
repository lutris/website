from django.test import TestCase
from ..util.pagination import get_page_range


class TestPageRange(TestCase):
    def test_single_page_should_return_single_entry(self):
        self.assertEqual(get_page_range(1, 1), range(1, 2))

    def test_num_page_less_than_max_returns_all(self):
        self.assertEqual(get_page_range(7, 1), range(1, 8))

    def test_adds_end_ellipsis(self):
        self.assertEqual(get_page_range(9, 1), [1, 2, 3, None, 9])
        self.assertEqual(get_page_range(9, 3), [1, 2, 3, 4, 5, None, 9])

    def test_adds_start_ellipsis(self):
        self.assertEqual(get_page_range(9, 9), [1, None, 7, 8, 9])

    def test_add_both_ellipsis(self):
        self.assertEqual(get_page_range(9, 5),
                         [1, None, 3, 4, 5, 6, 7, None, 9])
