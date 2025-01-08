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
                    'name': 'По поставленной задаче',
                    'x': [0.1, 0.2, 0.3, 0.35, 0.41, 0.5, 0.55, 0.6, 0.65, 0.7],
                    'y': [5.31, 8.568, 12.496, 14.74, 15.5135, 19.8, 26.78, 28.1152, 34.9685, 43.775],
                },
                {
                    'name': 'Кубическая',
                    'x': [-3, -2, -1, 0, 1, 2, 3, 4, 5, 6],
                    'y': [-15.92, -7.65, -2.73, 0, 1.79, 3.55, 6.99, 12.95, 22.65, 37.24,],
                },
                {
                    'name': 'Степенная',
                    'x': [0.1, 1, 2, 2.5, 3, 3.5, 4, 5],
                    'y': [0.00013, 2, 36.8, 93.9, 201.7, 385, 675, 1724],
                },
                {
                    'name': 'Линейная',
                    'x': [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8],
                    'y': [-7, -6.05, -5, -4.09, -3, -2, -1, 0.01, 1, 2, 3.05, 4, 5.11, 6],
                },
                {
                    'name': 'Гиперболическая',
                    'x': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2],
                    'y': [10, 5, 3.3333, 2.5, 2, 1.6667, 1.4286, 1.25, 1.1111, 1, 0.9091, 0.8333, 0.7692, 0.7143, 0.6667, 0.625, 0.5882, 0.5556, 0.5263, 0.5],
                },
                {
                    'name': 'Квадратичная',
                    'x': [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
                    'y': [16, 9, 4, 1, 0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225],
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
                    coefficients = np.polyfit(x, y, 4)
                else:  # Линейная или другие
                    coefficients = np.polyfit(x, y, 4)

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
