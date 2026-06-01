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
        fields = '__all__'

class PurchasedPhoneForm(forms.ModelForm):
    class Meta:
        model = PurchasedPhone
        fields = '__all__'

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
