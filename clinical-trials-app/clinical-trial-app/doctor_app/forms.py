from django import forms
from .models import Study

class PatientDataForm(forms.Form):
    patient_id = forms.IntegerField(
        label="ID пациента",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ID пациента'
        })
    )

    study = forms.ModelChoiceField(
        queryset=Study.objects.all(),
        label="Исследование",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    condition_score = forms.IntegerField(
        label="Оценка самочувствия",
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите оценку самочувствия (0-100)'
        })
    )

    # CharField с Select widget
    drug = forms.CharField(
        label="Принимаемый препарат",
        widget=forms.Select(attrs={'class': 'form-control'}, choices=[]),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Инициализируем пустые choices для виджета
        self.fields['drug'].widget.choices = [('', '--- Сначала выберите исследование ---')]

    def clean_patient_id(self):
        patient_id = self.cleaned_data['patient_id']
        if patient_id < 0:
            raise forms.ValidationError("ID пациента должен быть неотрицательным числом")
        return patient_id

    def clean_condition_score(self):
        score = self.cleaned_data['condition_score']
        if score < 0 or score > 100:
            raise forms.ValidationError("Оценка самочувствия должна быть от 0 до 100")
        return score

    def clean_drug(self):
        drug = self.cleaned_data.get('drug')
        if not drug:
            raise forms.ValidationError("Выберите препарат из списка")
        return drug