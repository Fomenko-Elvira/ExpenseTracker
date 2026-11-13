"""
Виджет Kivy, в который встроен график Matplotlib (Kivy Garden).
"""
from kivy.uix.boxlayout import BoxLayout
from matplotlib.figure import Figure

# Путь импорта зависит от способа установки (см. «Важные моменты» в лекции),
# поэтому пробуем несколько вариантов.
try:
    from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
except ImportError:
    try:
        from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
    except ImportError:
        from kivy_garden.matplotlib import FigureCanvasKivyAgg

from charts.drawing import draw_charts


class ChartBox(BoxLayout):
    """Контейнер с графиком. Метод update_chart перерисовывает его."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Figure() вместо plt.gcf() из лекции: так matplotlib не создаёт лишних окон
        self.figure = Figure()
        self.graph_canvas = FigureCanvasKivyAgg(self.figure)
        self.add_widget(self.graph_canvas)

    def update_chart(self, transactions):
        draw_charts(self.figure, transactions)   # аналог plt.clf() + рисование
        self.graph_canvas.draw()                 # перерисовать холст, как в лекции
