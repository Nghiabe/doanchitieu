from django import forms
from .models import Goal

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'start_date', 'end_date', 'amount_to_save']

class AddAmountForm(forms.Form):
    additional_amount = forms.DecimalField(
        label='Số Tiền Thêm Vào',  # Thay nhãn bằng tiếng Việt
        min_value=0,
        max_value=9999999,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01'}),
        error_messages={
            'required': 'Vui lòng điền vào ô này.',  # Thông báo lỗi khi trường trống
            'invalid': 'Số tiền không hợp lệ.',  # Thông báo lỗi khi giá trị không hợp lệ
            'max_value': 'Số tiền không được vượt quá 9,999,999.',  # Thông báo lỗi khi giá trị vượt quá max
            'min_value': 'Số tiền phải lớn hơn hoặc bằng 0.'  # Thông báo lỗi khi giá trị nhỏ hơn min
        }
    )
