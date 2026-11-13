"""
Рисование графиков Matplotlib (без Kivy — можно проверить отдельно).
Рисуем два графика: расходы по категориям (круговая) и доходы/расходы/баланс (столбики).
"""
from models.transaction import KIND_EXPENSE, calc_totals, sum_by_category


def draw_charts(figure, transactions):
    """Очищает фигуру и рисует на ней графики по списку операций."""
    figure.clf()

    ax_pie = figure.add_subplot(211)
    ax_bar = figure.add_subplot(212)

    # --- Круговая диаграмма: расходы по категориям ---
    by_category = sum_by_category(transactions, KIND_EXPENSE)
    if by_category:
        ax_pie.pie(list(by_category.values()), labels=list(by_category.keys()),
                   autopct='%1.0f%%')
        ax_pie.set_title('Расходы по категориям')
    else:
        ax_pie.text(0.5, 0.5, 'Расходов пока нет', ha='center', va='center')
        ax_pie.axis('off')

    # --- Столбики: доходы, расходы, баланс ---
    income, expenses, balance = calc_totals(transactions)
    ax_bar.bar(['Доходы', 'Расходы', 'Баланс'], [income, expenses, balance],
               color=['green', 'red', 'steelblue'])
    ax_bar.axhline(0, color='black', linewidth=0.8)
    ax_bar.set_ylabel('руб.')
    ax_bar.set_title('Доходы и расходы')

    figure.tight_layout()
