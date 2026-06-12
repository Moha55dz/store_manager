from django import forms
from .models import (
    Customer, Expense, Employee, Attendance, Supplier, PurchasedPhone,
    MaintenanceTask, ElectronicService, Installment, DeliveryTracker, Treasury
)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'عنوان المصروف',
                'style': 'padding:10px 14px; border-radius:8px;'
            }),
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': 'المبلغ',
                'style': 'padding:10px 14px; border-radius:8px; text-align:center;'
            }),
        }

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        # Exclude the debt field here — it has its own section and will be added later
        exclude = ('debt',)

class PurchasedPhoneForm(forms.ModelForm):
    class Meta:
        model = PurchasedPhone
        fields = '__all__'
        widgets = {
            'purchase_price': forms.NumberInput(attrs={'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'min': '1'}),
        }

class MaintenanceTaskForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTask
        fields = '__all__'

class ElectronicServiceForm(forms.ModelForm):
    class Meta:
        model = ElectronicService
        fields = '__all__'

class InstallmentForm(forms.ModelForm):
    class Meta:
        model = Installment
        fields = '__all__'

class DeliveryTrackerForm(forms.ModelForm):
    class Meta:
        model = DeliveryTracker
        fields = '__all__'

class TreasuryForm(forms.ModelForm):
    class Meta:
        model = Treasury
        fields = '__all__'
