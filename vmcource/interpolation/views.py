from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import FunctionData
import numpy as np

def input_data(request):
    if request.method == 'POST':
        # Если нажата кнопка "Загрузить шаблон"
        if 'load_template' in request.POST:
            # Данные шаблонов
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
                    'y': [1 / -10, 1 / -5, 1 / -2, 1 / -1, 1 / 1, 1 / 2, 1 / 5, 1 / 8, 1 / 10],
                },
                {
                    'name': 'Квадратичная',
                    'x': [2.21, 2.24, 2.25, 2.3, 2.35, 2.37, 2.4, 2.41, 2.45, 2.47],
                    'y': [5.7816, 6.15292, 6.23877, 6.81036, 6.99732, 7.3326, 7.7662, 7.4108, 8.2008, 8.0025],
                },
            ]

            # Применяем МНК к каждой функции в шаблоне
            for template in templates:
                x = np.array(template['x'])
                y = np.array(template['y'])
                coefficients = np.polyfit(x, y, 1)  # Линейная аппроксимация
                polynomial = np.poly1d(coefficients)
                y_fit = polynomial(x)
                template['y_fit'] = y_fit.tolist()
                template['polynomial'] = str(polynomial)

            # Передаем данные в контекст шаблона
            return render(request, 'interpolation/result.html', {'templates': templates})

        # Обработка обычной формы ввода данных
        x_values = request.POST.get('x_values')
        y_values = request.POST.get('y_values')
        error = float(request.POST.get('error'))

        # Сохранение данных в базу
        FunctionData.objects.create(x_values=x_values, y_values=y_values, error=error)
        return redirect('result')

    return render(request, 'interpolation/input_data.html')

def result(request):
    # Проверяем, переданы ли шаблоны через контекст
    if 'templates' in request.session:
        templates = request.session.pop('templates')  # Удаляем из сессии после использования
        return render(request, 'interpolation/result.html', {'templates': templates})
    elif 'templates' in request.GET:
        templates = request.GET.get('templates')
        return render(request, 'interpolation/result.html', {'templates': templates})

    # Если шаблоны не переданы, используем последнюю запись из базы данных
    data = FunctionData.objects.last()
    if not data:
        return HttpResponse("No data available")

    x = np.array(data.get_x_list())
    y = np.array(data.get_y_list())

    # Проверка на достаточное количество точек
    if len(x) < 2:
        return HttpResponse("Not enough data points for linear approximation")

    # Проверка на постоянство данных
    if np.all(x == x[0]) or np.all(y == y[0]):
        return HttpResponse("Data is constant, cannot perform fitting")

    # Метод наименьших квадратов
    degree = int(request.GET.get('degree', 1))  # По умолчанию степень 1
    try:
        coefficients = np.polyfit(x, y, degree)
    except np.linalg.LinAlgError as e:
        return HttpResponse(f"Error in polynomial fitting: {e}")

    polynomial = np.poly1d(coefficients)
    y_fit = polynomial(x)

    # Вычисление среднеквадратичной ошибки
    mse = np.mean((y - y_fit) ** 2)

    context = {
        'x_values': x.tolist(),  # Преобразуем numpy.array в список
        'y_values': y.tolist(),
        'y_fit': y_fit.tolist(),
        'polynomial': str(polynomial),
        'error': data.error,
        'mse': mse,
    }

    return render(request, 'interpolation/result.html', context)