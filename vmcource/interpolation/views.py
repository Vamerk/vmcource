from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import FunctionData
import numpy as np
import json


def input_data(request):
    if request.method == 'POST':
        # Если нажата кнопка "Загрузить шаблон"
        if 'load_template' in request.POST:
            # Шаблоны данных
            templates = [
                {
                    'name': 'Кубическая',
                    'x': [3, 3.3, 3.6, 3.9, 4.2, 4.5, 4.8, 5.1, 5.4, 5.7],
                    'y': [0.88434, 0.81406, 0.73332, 0.69874, 0.68276, 0.65688, 0.62317, 0.57424, 0.5643, 0.56202],
                },
                {
                    'name': 'Степенная',
                    'x': [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
                    'y': [0.2, 0.6, 1.3, 2.4, 4.0, 6.0, 8.5, 11.5],
                },
                {
                    'name': 'Линейная',
                    'x': [1, 1.1, 1.3, 1.4, 1.7, 1.8, 1.9, 2.1, 2.3, 2.5, 2.7],
                    'y': [2, 2.1, 2.3, 2.4, 2.7, 2.8, 2.9, 3.1, 3.3, 3.5, 3.7],
                },
                {
                    'name': 'Гиперболическая',
                    'x': [-10, -5, -2, -1, 1, 2, 5, 8, 10],
                    'y': [1 / -10, 1 / -5, 1 / -2, 1 / -1, 1, 1 / 2, 1 / 5, 1 / 8, 1 / 10],
                },
                {
                    'name': 'Квадратичная',
                    'x': [2.21, 2.24, 2.25, 2.3, 2.35, 2.37, 2.4, 2.41, 2.45, 2.47],
                    'y': [5.7816, 6.15292, 6.23877, 6.81036, 6.99732, 7.3326, 7.7662, 7.4108, 8.2008, 8.0025],
                },
                # Остальные шаблоны...
            ]

            # Обработка каждого шаблона
            for template in templates:
                x = np.array(template['x'])
                y = np.array(template['y'])

                # Выбор аппроксимации
                if template['name'] == 'Кубическая':
                    coefficients = np.polyfit(x, y, 3)
                elif template['name'] == 'Степенная':
                    coefficients = np.polyfit(np.log(x), np.log(y), 1)
                    polynomial = lambda x: np.exp(coefficients[1]) * x**coefficients[0]
                elif template['name'] == 'Гиперболическая':
                    coefficients = np.polyfit(x, 1 / y, 1)
                    polynomial = lambda x: 1 / (coefficients[0] * x + coefficients[1])
                elif template['name'] == 'Квадратичная':
                    coefficients = np.polyfit(x, y, 2)
                else:  # Линейная или другие
                    coefficients = np.polyfit(x, y, 1)

                if template['name'] in ['Степенная', 'Гиперболическая']:
                    y_fit = [polynomial(val) for val in x]
                    template['y_fit'] = json.dumps(y_fit)  # Преобразуем в список, затем в JSON

                else:
                    polynomial = np.poly1d(coefficients)
                    y_fit = polynomial(x)
                    template['y_fit'] = json.dumps(y_fit.tolist())  # Преобразуем в список, затем в JSON

                # Сохраняем данные
                template['polynomial'] = str(polynomial)

            return render(request, 'interpolation/result.html', {'templates': templates})

        # Обработка пользовательского ввода
        x_values = request.POST.get('x_values')
        y_values = request.POST.get('y_values')
        error = request.POST.get('error', 0)

        if not x_values or not y_values:
            return HttpResponse("Введите данные для x и y.")

        try:
            x_values = list(map(float, x_values.split(',')))
            y_values = list(map(float, y_values.split(',')))
            error = float(error)
        except ValueError:
            return HttpResponse("Некорректный формат данных. Используйте числа, разделенные запятыми.")

        if len(x_values) != len(y_values):
            return HttpResponse("Количество x и y должно совпадать.")

        # Сохраняем данные в базу
        FunctionData.objects.create(x_values=x_values, y_values=y_values, error=error)
        return redirect('result')

    return render(request, 'interpolation/input_data.html')


def result(request):
    # Получение последней записи из базы
    data = FunctionData.objects.last()
    if not data:
        return HttpResponse("Нет доступных данных.")

    x = np.array(data.get_x_list())
    y = np.array(data.get_y_list())

    if len(x) < 2 or len(y) < 2:
        return HttpResponse("Недостаточно точек данных для аппроксимации.")

    degree = int(request.GET.get('degree', 1))
    try:
        coefficients = np.polyfit(x, y, degree)
        polynomial = np.poly1d(coefficients)
        y_fit = polynomial(x)
    except np.linalg.LinAlgError as e:
        return HttpResponse(f"Ошибка при аппроксимации: {e}")

    mse = np.mean((y - y_fit) ** 2)  # Среднеквадратичная ошибка

    context = {
        'x_values': json.dumps(x.tolist()),  # Преобразуем в JSON
        'y_values': json.dumps(y.tolist()),  # Преобразуем в JSON
        'y_fit': json.dumps(y_fit.tolist()),  # Преобразуем в JSON
        'polynomial': str(polynomial),
        'error': data.error,
        'mse': mse,
    }

    return render(request, 'interpolation/result.html', context)
