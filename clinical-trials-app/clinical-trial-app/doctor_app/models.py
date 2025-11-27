from django.db import models

class Study(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название исследования")
    drug_name = models.CharField(max_length=100, verbose_name="Название препарата")
    med = models.CharField(max_length=100, blank=True, null=True, verbose_name="Тестируемый препарат")

    def __str__(self):
        return f"{self.name}"

    def get_test_drug(self):
        """Возвращает тестируемый препарат"""
        return self.med if self.med else self.drug_name

class Measurements(models.Model):
    measurement_id = models.AutoField(primary_key=True, verbose_name="ID измерения")
    patient_id = models.IntegerField(verbose_name="ID пациента")
    trial_id = models.IntegerField(verbose_name="ID испытания")
    measurement_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата измерения")
    drug = models.CharField(max_length=100, verbose_name="Принимаемый препарат")
    condition_score = models.IntegerField(verbose_name="Оценка самочувствия")

    class Meta:
        db_table = 'measurements'
        managed = False

    def __str__(self):
        return f"Измерение {self.measurement_id}"