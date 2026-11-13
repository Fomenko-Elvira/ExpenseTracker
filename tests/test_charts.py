import os
import tempfile
import unittest

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from charts.drawing import draw_charts
from models.transaction import normalize


def _render(transactions):
    figure = Figure(figsize=(5, 7))
    draw_charts(figure, transactions)
    path = os.path.join(tempfile.mkdtemp(), 'chart.png')
    FigureCanvasAgg(figure).print_png(path)
    return path


class TestDrawing(unittest.TestCase):
    def test_draws_with_data(self):
        data = [
            normalize({'kind': 'income', 'category': 'Продажи', 'amount': 10000}),
            normalize({'kind': 'expense', 'category': 'Офис', 'amount': 1500}),
            normalize({'kind': 'expense', 'category': 'Налоги', 'amount': 1000}),
        ]
        self.assertGreater(os.path.getsize(_render(data)), 1000)

    def test_draws_when_empty(self):
        self.assertGreater(os.path.getsize(_render([])), 1000)

    def test_redraw_twice_keeps_two_axes(self):
        figure = Figure()
        draw_charts(figure, [])
        draw_charts(figure, [normalize({'kind': 'expense', 'category': 'Офис', 'amount': 5})])
        self.assertEqual(len(figure.axes), 2)       # clf() очищает старые оси


if __name__ == '__main__':
    unittest.main()
