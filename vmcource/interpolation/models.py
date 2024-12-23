from django.db import models

class FunctionData(models.Model):
    x_values = models.TextField()  # Строка с x-значениями, разделенными запятыми
    y_values = models.TextField()  # Строка с y-значениями, разделенными запятыми
    error = models.FloatField()    # Максимальная систематическая ошибка δ

    def get_x_list(self):
        return list(map(float, self.x_values.split(',')))

    def get_y_list(self):
        return list(map(float, self.y_values.split(',')))