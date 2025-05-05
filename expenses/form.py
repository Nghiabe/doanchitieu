from django import forms
from .models import ExpenseJar

class ExpenseJarForm(forms.ModelForm):
    class Meta:
        model = ExpenseJar
        fields = ['name', 'total_budget', 'members']  # 'name' thay cho 'jar_name'
