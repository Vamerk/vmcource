from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import FunctionData
import numpy as np

def input_data(request):
    if request.method == 'POST':
        x_values = request.POST.get('x_values')
        y_values = request.POST.get('y_values')
        error = float(request.POST.get('error'))

        # Сохранение данных в базу
        FunctionData.objects.create(x_values=x_values, y_values=y_values, error=error)

        return redirect('result')

    return render(request, 'interpolation/input_data.html')

def result(request):
    # Получение последних данных из базы
    data = FunctionData.objects.last()
    if not data:
        return HttpResponse("No data available")

    x = np.array(data.get_x_list())
    y = np.array(data.get_y_list())

    # Метод наименьших квадратов (например, линейная аппроксимация)
    coefficients = np.polyfit(x, y, 1)
    polynomial = np.poly1d(coefficients)

    # Вычисление значений аппроксимирующей функции
    y_fit = polynomial(x)

    context = {
        'x_values': x,
        'y_values': y,
        'y_fit': y_fit,
        'polynomial': str(polynomial),
        'error': data.error,
    }

    return render(request, 'interpolation/result.html', context)