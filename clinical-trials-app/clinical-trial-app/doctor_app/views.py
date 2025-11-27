from django.shortcuts import render
from django.db import DatabaseError, connection
from .forms import PatientDataForm
from .models import Study
from django.utils import timezone
import statistics


def input_data(request):
    # Подготавливаем данные о препаратах для JavaScript
    studies_data = {}
    for study in Study.objects.all():
        studies_data[study.id] = {
            'name': study.name,
            'drug_name': study.drug_name
        }

    if request.method == 'POST':
        form = PatientDataForm(request.POST)
        if form.is_valid():
            try:
                patient_id = form.cleaned_data['patient_id']
                study = form.cleaned_data['study']
                condition_score = form.cleaned_data['condition_score']
                drug = form.cleaned_data['drug']

                trial_id = study.id

                with connection.cursor() as cursor:
                    cursor.execute("SELECT COALESCE(MAX(measurement_id), 0) + 1 FROM measurements")
                    next_id = cursor.fetchone()[0]

                    cursor.execute(
                        "INSERT INTO measurements (measurement_id, patient_id, trial_id, measurement_date, drug, condition_score) VALUES (%s, %s, %s, %s, %s, %s)",
                        [next_id, patient_id, trial_id, timezone.now(), drug, condition_score]
                    )

                # Анализ данных
                analysis_result = analyze_condition_score(drug, condition_score)

                context = {
                    'form': form,
                    'analysis_result': analysis_result['message'],
                    'patient_id': patient_id,
                    'study_name': study.name,
                    'condition_score': condition_score,
                    'drug_taken': drug,
                    'is_normal': analysis_result['is_normal'],
                    'show_result': True,
                    'success_message': f'✅ Данные успешно сохранены в БД! ID измерения: {next_id}',
                    'analysis_details': analysis_result['details'],
                    'studies_data': studies_data
                }
                return render(request, 'doctor_app/input_form.html', context)

            except Exception as e:
                context = {
                    'form': form,
                    'error': f'Ошибка: {str(e)}',
                    'studies_data': studies_data
                }
        else:
            context = {
                'form': form,
                'studies_data': studies_data
            }
    else:
        form = PatientDataForm()
        context = {
            'form': form,
            'studies_data': studies_data
        }

    return render(request, 'doctor_app/input_form.html', context)


def analyze_condition_score(drug, current_score):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT condition_score 
                FROM measurements 
                WHERE drug = %s AND condition_score IS NOT NULL
                ORDER BY measurement_date
            """, [drug])

            results = cursor.fetchall()
            historical_scores = [row[0] for row in results] if results else []

        if len(historical_scores) < 3:
            if not historical_scores:
                avg_score = current_score
                records_count = 0
            else:
                avg_score = statistics.mean(historical_scores)
                records_count = len(historical_scores)

            lower_bound = avg_score * 0.9
            upper_bound = avg_score * 1.1
            is_normal = True

            if not historical_scores:
                message = f"📊 Первая запись для препарата '{drug}'. Ваша оценка: {current_score} баллов. Диапазон нормы будет уточнен после накопления данных."
            else:
                message = f"📊 Мало данных для анализа ({len(historical_scores)} записей). Ваша оценка: {current_score} баллов. Требуется больше измерений."

        else:
            avg_score = statistics.mean(historical_scores)
            stdev = statistics.stdev(historical_scores)
            records_count = len(historical_scores)

            lower_bound = avg_score * 0.9
            upper_bound = avg_score * 1.1

            lower_bound = max(0, lower_bound)
            upper_bound = min(100, upper_bound)

            is_normal = lower_bound <= current_score <= upper_bound

            if is_normal:
                message = f"✅ Самочувствие в норме! Ваша оценка {current_score} баллов входит в диапазон нормы ({lower_bound:.1f}-{upper_bound:.1f} баллов). Среднее по препарату: {avg_score:.1f} баллов."
            else:
                if current_score < lower_bound:
                    deviation = lower_bound - current_score
                    message = f"⚠️ Самочувствие ниже нормы! Ваша оценка {current_score} баллов, норма: {lower_bound:.1f}-{upper_bound:.1f} баллов. Отклонение: {deviation:.1f} баллов."
                else:
                    deviation = current_score - upper_bound
                    message = f"⚠️ Самочувствие выше нормы! Ваша оценка {current_score} баллов, норма: {lower_bound:.1f}-{upper_bound:.1f} баллов. Отклонение: {deviation:.1f} баллов."

        details = {
            'average_score': round(avg_score, 2),
            'lower_bound': round(lower_bound, 2),
            'upper_bound': round(upper_bound, 2),
            'current_score': current_score,
            'is_in_range': is_normal,
            'records_count': records_count,
            'analysis_based_on': 'historical_data' if records_count >= 3 else 'insufficient_data'
        }

        if records_count >= 3:
            details['standard_deviation'] = round(stdev, 2)

        return {
            'is_normal': is_normal,
            'message': message,
            'details': details
        }

    except Exception as e:
        print(f"❌ ОШИБКА АНАЛИЗА: {e}")
        return {
            'is_normal': True,
            'message': f"Оценка самочувствия: {current_score} баллов (ошибка анализа: {str(e)})",
            'details': {
                'average_score': current_score,
                'lower_bound': current_score * 0.9,
                'upper_bound': current_score * 1.1,
                'current_score': current_score,
                'is_in_range': True,
                'records_count': 'ошибка',
                'analysis_based_on': 'error'
            }
        }