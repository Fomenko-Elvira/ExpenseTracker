import unittest

from models.transaction import (
    KIND_EXPENSE, KIND_INCOME, calc_totals, create_transaction,
    make_key, normalize, sorted_newest_first, sum_by_category,
)


class TestCreateTransaction(unittest.TestCase):
    def test_expense_ok(self):
        key, rec = create_transaction(KIND_EXPENSE, 'Офис', ' Бумага ', '1500,50')
        self.assertEqual(rec['amount'], 1500.5)
        self.assertEqual(rec['description'], 'Бумага')
        self.assertEqual(rec['kind'], KIND_EXPENSE)
        self.assertTrue(key.startswith('t_'))

    def test_income_ok(self):
        _, rec = create_transaction(KIND_INCOME, 'Продажи', 'Заказ', '10000')
        self.assertEqual(rec['kind'], KIND_INCOME)

    def test_income_category_not_allowed_for_expense(self):
        with self.assertRaises(ValueError):
            create_transaction(KIND_EXPENSE, 'Продажи', 'Что-то', '100')

    def test_bad_amounts(self):
        for bad in ('', 'abc', '0', '-5', 'nan', 'inf'):
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    create_transaction(KIND_EXPENSE, 'Офис', 'Тест', bad)

    def test_category_not_chosen(self):
        with self.assertRaises(ValueError):
            create_transaction(KIND_EXPENSE, 'Выберите категорию', 'Тест', '100')

    def test_empty_description(self):
        with self.assertRaises(ValueError):
            create_transaction(KIND_EXPENSE, 'Офис', '   ', '100')

    def test_key_has_no_dot_for_firebase(self):
        self.assertNotIn('.', make_key())
        self.assertNotEqual(make_key(), make_key())


class TestTotals(unittest.TestCase):
    def setUp(self):
        self.items = [
            normalize({'kind': 'income', 'category': 'Продажи', 'amount': 10000, 'date': '2026-01-02'}),
            normalize({'kind': 'expense', 'category': 'Офис', 'amount': 1500.5, 'date': '2026-01-03'}),
            normalize({'kind': 'expense', 'category': 'Офис', 'amount': 500, 'date': '2026-01-01'}),
            normalize({'kind': 'expense', 'category': 'Налоги', 'amount': 1000, 'date': '2026-01-04'}),
        ]

    def test_balance(self):
        self.assertEqual(calc_totals(self.items), (10000.0, 3000.5, 6999.5))

    def test_empty(self):
        self.assertEqual(calc_totals([]), (0, 0, 0))

    def test_by_category(self):
        self.assertEqual(sum_by_category(self.items, KIND_EXPENSE), {'Офис': 2000.5, 'Налоги': 1000.0})
        self.assertEqual(sum_by_category(self.items, KIND_INCOME), {'Продажи': 10000.0})

    def test_sorted_newest_first(self):
        dates = [t['date'] for t in sorted_newest_first(dict(enumerate(self.items)))]
        self.assertEqual(dates, sorted(dates, reverse=True))


class TestNormalize(unittest.TestCase):
    def test_old_lecture_record_is_expense(self):
        rec = normalize({'category': 'Офис', 'description': 'x', 'amount': 100, 'date': 'd'})
        self.assertEqual(rec['kind'], KIND_EXPENSE)

    def test_garbage_is_safe(self):
        rec = normalize({'kind': 'strange', 'amount': 'oops'})
        self.assertEqual((rec['kind'], rec['amount']), (KIND_EXPENSE, 0.0))


if __name__ == '__main__':
    unittest.main()
