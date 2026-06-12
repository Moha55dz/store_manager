from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

# استيراد النماذج (Models)
from .models import (
    Customer, Expense, Supplier, Employee, MaintenanceTask,
    Attendance, ElectronicService, Installment, DeliveryTracker,
    PurchasedPhone, Treasury
)
import datetime

# Create your views here.

def login(request):
    """صفحة تسجيل الدخول"""
    
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    
    error_message = None

    if request.method == 'POST':
        user_name = request.POST.get('username')
        user_pass = request.POST.get('password')

        user = authenticate(request, username=user_name, password=user_pass)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard_home')
        else:
            error_message = "اسم المستخدم أو كلمة المرور غير صحيحة!"

    return render(request, 'login.html', {'error_message': error_message})


@login_required(login_url='/login/')
def dashboard_home(request):
    """الصفحة الرئيسية للوحة التحكم - مع حساب الإحصائيات"""
    
    # 1. حساب مجموع سعر الخدمات الإلكترونية
    total_electronic_services_price = ElectronicService.objects.aggregate(total=Sum('price'))['total'] or 0
    
    # 2. حساب تتبع الطلبيات
    delivery_orders_count = DeliveryTracker.objects.count()
    
    # 3. حساب إجمالي المبالغ المتبقية للأقساط
    total_remaining_installments = Installment.objects.aggregate(total=Sum('remaining_amount'))['total'] or 0
    
    # 4. حساب مجموع الرواتب
    total_salaries = Employee.objects.aggregate(total=Sum('salary'))['total'] or 0
    
    # 5. حساب الخزينة (يتم حسابه لاحقاً بالأسفل بعد حساب كل المتغيرات المطلوبة)
    
    # 6. حساب التوصيلات المكتملة والأرباح منها
    completed_deliveries = DeliveryTracker.objects.filter(status=True).count()
    total_deliveries = DeliveryTracker.objects.count()
    total_delivery_earnings = DeliveryTracker.objects.aggregate(total=Sum('delivery_price'))['total'] or 0
    
    # 7. حساب الحضور اليومي
    today_attendance = Attendance.objects.filter(is_present=True).count()
    
    # 8. حساب عدد المستخدمين
    users_count = User.objects.count()
    
    # 9. حساب عدد العمال
    employees_count = Employee.objects.count()
    
    # 10. حساب عدد الموردين
    suppliers_count = Supplier.objects.count()
    
    # 11. حساب مجموع ديون الزبائن
    total_customer_debts = Customer.objects.aggregate(total=Sum('debt'))['total'] or 0
    
    # 12. حساب مجموع ديون الموردين
    total_supplier_debts = Supplier.objects.aggregate(total=Sum('debt'))['total'] or 0
    
    # 13. حساب مجموع المصاريف
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # 14. حساب عدد الهواتف المشتراة
    phones_purchased_count = PurchasedPhone.objects.count()
    
    # 15. حساب مجموع المبالغ المستعملة (التكلفة الإجمالية = سعر الشراء * الكمية لكل سجل)
    total_expr = ExpressionWrapper(F('purchase_price') * F('quantity'), output_field=DecimalField(max_digits=14, decimal_places=2))
    total_spent_on_phones = PurchasedPhone.objects.aggregate(total=Sum(total_expr))['total'] or 0
    
    # 15a. حساب مجموع المصاريف المستعملة (الهواتف + الصيانة + المصاريف، بدون التوصيل)
    total_spendings = (
        (PurchasedPhone.objects.aggregate(total=Sum(total_expr))['total'] or 0)
        + (MaintenanceTask.objects.aggregate(total=Sum('cost'))['total'] or 0)
        + (Expense.objects.aggregate(total=Sum('amount'))['total'] or 0)
    )
    
    # 16. حساب الصيانة الجارية والمعلقة
    pending_maintenance = MaintenanceTask.objects.filter(status__in=['pending', 'in_progress']).count()
    total_maintenance = MaintenanceTask.objects.count()
    completed_maintenance = MaintenanceTask.objects.filter(status='completed').count()
    maintenance_status = f"{total_maintenance}/{completed_maintenance}"
    
    # 17. حساب الصيانة الخارجية
    external_maintenance = MaintenanceTask.objects.filter(status='external').count()
    
    # حساب الخزينة بالصيغة المالية الشاملة
    # الخزينة = رأس المال الافتتاحي + التدفقات النقدية الداخلة - التدفقات النقدية الخارجة
    treasury_obj = Treasury.objects.first()
    initial_capital = treasury_obj.initial_capital if treasury_obj else 0

    # التدفقات النقدية الداخلة
    completed_maintenance_revenue = MaintenanceTask.objects.filter(status='completed').aggregate(total=Sum('cost'))['total'] or 0
    total_paid_installments = Installment.objects.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_phone_sales_revenue = PurchasedPhone.objects.filter(is_sold=True).aggregate(total=Sum('selling_price'))['total'] or 0
    actual_phone_sales_cash = total_phone_sales_revenue - total_customer_debts

    # التدفقات النقدية الخارجة
    actual_phone_purchase_cash = total_spent_on_phones - total_supplier_debts

    total_treasury = (
        initial_capital
        + total_electronic_services_price
        + completed_maintenance_revenue
        + total_paid_installments
        + total_delivery_earnings
        + actual_phone_sales_cash
        - total_expenses
        - total_salaries
        - actual_phone_purchase_cash
    )

    # وضع جميع البيانات في قاموس Context لتمريرها إلى الـ HTML
    context = {
        'total_electronic_services_price': total_electronic_services_price,
        'delivery_orders_count': delivery_orders_count,
        'total_remaining_installments': total_remaining_installments,
        'total_salaries': total_salaries,
        'total_treasury': total_treasury,
        'completed_deliveries': completed_deliveries,
        'total_deliveries': total_deliveries,
        'total_delivery_earnings': total_delivery_earnings,
        'today_attendance': today_attendance,
        'users_count': users_count,
        'employees_count': employees_count,
        'suppliers_count': suppliers_count,
        'total_customer_debts': total_customer_debts,
        'total_supplier_debts': total_supplier_debts,
        'total_expenses': total_expenses,
        'phones_purchased_count': phones_purchased_count,
        'total_spent_on_phones': total_spent_on_phones,
        'total_spendings': total_spendings,
        'maintenance_status': maintenance_status,
        'external_maintenance': external_maintenance,
    }
    
    return render(request, 'dashboard/home.html', context)


def logout(request):
    """تسجيل الخروج"""
    auth_logout(request)
    return redirect('login')


@login_required
def settings_view(request):
    """صفحة الإعدادات"""
    password_form = PasswordChangeForm(request.user)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            username = request.POST.get('username')
            
            if username:
                if User.objects.filter(username=username).exclude(id=request.user.id).exists():
                    messages.error(request, "اسم المستخدم موجود مسبقاً!")
                else:
                    request.user.username = username
                    request.user.save()
                    messages.success(request, "تم تحديث البيانات بنجاح!")
                    return redirect('settings')
                    
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important to keep user logged in
                messages.success(request, "تم تغيير كلمة المرور بنجاح!")
                return redirect('settings')
            else:
                for field, errors in password_form.errors.items():
                    for error in errors:
                        messages.error(request, error)

    return render(request, 'dashboard/settings.html', {
        'password_form': password_form
    })


@login_required
def manage_users_view(request):
    """صفحة إدارة المستخدمين - متاحة فقط للمسؤولين والسوبريوزر"""
    # حماية الصفحة: إذا لم يكن المستخدم سوبر أو ليس في مجموعة Admin يتم طرده
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
    if not is_admin:
        return redirect('dashboard_home')

    all_users = User.objects.all().prefetch_related('groups').order_by('id')

    if request.method == 'POST':
        user_name = request.POST.get('username', '').strip()
        user_pass = request.POST.get('password', '').strip()
        role = request.POST.get('role')

        if not user_name or not user_pass:
            messages.error(request, 'يجب تعبئة جميع الحقول المطلوبة!')
        elif User.objects.filter(username=user_name).exists():
            messages.error(request, f'اسم المستخدم «{user_name}» موجود بالفعل!')
        elif role not in ['Admin', 'Normal_User']:
            messages.error(request, 'الرتبة المختارة غير صحيحة!')
        else:
            try:
                group = Group.objects.get(name=role)
                new_user = User.objects.create_user(username=user_name, password=user_pass)
                new_user.groups.add(group)
                messages.success(request, f'تم إنشاء حساب «{user_name}» بنجاح كـ {role}!')
                return redirect('manage_users')
            except Group.DoesNotExist:
                messages.error(request, f'مجموعة «{role}» غير موجودة. تأكد من إنشائها أولاً من لوحة تحكم Django.')

    context = {
        'users': all_users,
    }
    return render(request, 'dashboard/manage_users.html', context)


@login_required
def delete_user_view(request, user_id):
    """حذف مستخدم - متاح فقط للمسؤولين والسوبريوزر"""
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()
    if not is_admin:
        return redirect('dashboard_home')

    if request.method == 'POST':
        try:
            user_to_delete = User.objects.get(id=user_id)
            # منع المسؤول من حذف نفسه
            if user_to_delete == request.user:
                messages.error(request, 'لا يمكنك حذف حسابك الخاص!')
            # منع حذف السوبريوزر
            elif user_to_delete.is_superuser:
                messages.error(request, 'لا يمكن حذف حساب مدير النظام!')
            else:
                username = user_to_delete.username
                user_to_delete.delete()
                messages.success(request, f'تم حذف حساب «{username}» بنجاح!')
        except User.DoesNotExist:
            messages.error(request, 'المستخدم غير موجود!')

    return redirect('manage_users')


@login_required
def maintenance_list(request):
    """دالة عرض جدول الصيانة"""
    tasks = MaintenanceTask.objects.all().order_by('-created_at')
    return render(request, 'dashboard/maintenance_list.html', {'tasks': tasks})


@login_required
def add_maintenance(request):
    """دالة إضافة جهاز جديد للصيانة"""
    if request.method == 'POST':
        c_name = request.POST.get('customer_name')
        d_info = request.POST.get('device_info')
        cost = request.POST.get('cost')
        status = request.POST.get('status')

        MaintenanceTask.objects.create(
            customer_name=c_name,
            device_info=d_info,
            cost=cost or 0,
            status=status
        )
        return redirect('maintenance_list')
        
    return render(request, 'dashboard/add_maintenance.html')


@login_required
def edit_maintenance(request, pk):
    """دالة تعديل بيانات جهاز معين بناءً على الـ ID"""
    task = get_object_or_404(MaintenanceTask, pk=pk)

    if request.method == 'POST':
        task.customer_name = request.POST.get('customer_name')
        task.device_info = request.POST.get('device_info')
        task.cost = request.POST.get('cost') or 0
        task.status = request.POST.get('status')
        task.save()
        return redirect('maintenance_list')

    return render(request, 'dashboard/edit_maintenance.html', {'task': task})

# --- AUTOGENERATED CRUD VIEWS ---
from django.urls import reverse
from .forms import *


@login_required
def customer_list(request):
    items = Customer.objects.all()
    return render(request, 'dashboard/customer_list.html', {'items': items})

@login_required
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة الزبائن',
        'cancel_url': reverse('customer_list')
    })

@login_required
def edit_customer(request, pk):
    item = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل الزبائن',
        'cancel_url': reverse('customer_list')
    })

@login_required
def expense_list(request):
    items = Expense.objects.all()
    return render(request, 'dashboard/expense_list.html', {'items': items})

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة المصاريف',
        'cancel_url': reverse('expense_list')
    })

@login_required
def edit_expense(request, pk):
    item = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل المصاريف',
        'cancel_url': reverse('expense_list')
    })


@login_required
def employee_list(request):
    items = Employee.objects.all()
    return render(request, 'dashboard/employee_list.html', {'items': items})

@login_required
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة العمال',
        'cancel_url': reverse('employee_list')
    })

@login_required
def edit_employee(request, pk):
    item = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل العمال',
        'cancel_url': reverse('employee_list')
    })

@login_required
def attendance_list(request):
    items = Attendance.objects.all()
    return render(request, 'dashboard/attendance_list.html', {'items': items})

@login_required
def add_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('attendance_list')
    else:
        form = AttendanceForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة الحضور والمغادرة',
        'cancel_url': reverse('attendance_list')
    })

@login_required
def edit_attendance(request, pk):
    item = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('attendance_list')
    else:
        form = AttendanceForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل الحضور والمغادرة',
        'cancel_url': reverse('attendance_list')
    })

@login_required
def supplier_list(request):
    items = Supplier.objects.all()
    return render(request, 'dashboard/supplier_list.html', {'items': items})


@login_required
def supplier_debts(request):
    """عرض ديون الموردين: اسم المورد، رقم الهاتف، وقيمة الدين"""
    items = Supplier.objects.all().order_by('-debt')
    total_debt = items.aggregate(total=Sum('debt'))['total'] or 0
    return render(request, 'dashboard/supplier_debts.html', {'items': items, 'total_debt': total_debt})


@login_required
def update_supplier_debt(request, pk):
    """Handle POST to update a supplier's debt amount."""
    if request.method != 'POST':
        return redirect('supplier_debts')

    supplier = get_object_or_404(Supplier, pk=pk)
    debt_value = request.POST.get('debt')
    try:
        # convert to Decimal via float-safe parsing
        from decimal import Decimal

        if debt_value is None or debt_value == '':
            supplier.debt = Decimal('0.00')
        else:
            supplier.debt = Decimal(debt_value)
        supplier.save()
        messages.success(request, f'تم تحديث دين المورد «{supplier.name}» بنجاح.')
    except Exception:
        messages.error(request, 'قيمة الدين غير صالحة.')

    return redirect('supplier_debts')

@login_required
def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة الموردون',
        'cancel_url': reverse('supplier_list')
    })

@login_required
def edit_supplier(request, pk):
    item = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل الموردون',
        'cancel_url': reverse('supplier_list')
    })

@login_required
def purchased_phone_list(request):
    items = PurchasedPhone.objects.all()
    # compute grand total for all purchased phones
    total_all = 0
    for it in items:
        try:
            price = it.purchase_price or 0
            qty = it.quantity or 0
            total_all += price * qty
        except Exception:
            continue
    return render(request, 'dashboard/purchased_phone_list.html', {'items': items, 'total_all': total_all})


@login_required
def spendings_list(request):
    """Consolidated list of all outflows: purchased phones, deliveries, maintenance, expenses."""
    entries = []

    # Purchased phones: aggregate per record
    for p in PurchasedPhone.objects.all():
        try:
            amount = (p.purchase_price or 0) * (p.quantity or 0)
        except Exception:
            amount = 0
        entries.append({
            'type': 'شراء هواتف',
            'reference': f"{p.model_name} ({p.supplier.name if p.supplier else '—'})",
            'date': p.date_purchased,
            'amount': amount,
            'note': p.imei or ''
        })

    # Maintenance costs
    for m in MaintenanceTask.objects.all():
        entries.append({
            'type': 'صيانة',
            'reference': m.customer_name,
            'date': m.created_at,
            'amount': m.cost or 0,
            'note': m.device_info or ''
        })

    # Expenses
    for e in Expense.objects.all():
        entries.append({
            'type': 'مصروف',
            'reference': e.title,
            'date': e.date,
            'amount': e.amount or 0,
            'note': ''
        })

    # normalize dates to timezone-aware datetimes so sorting works across date/datetime
    def _normalize_date(d):
        if d is None:
            return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        if isinstance(d, datetime.datetime):
            if d.tzinfo is None:
                return d.replace(tzinfo=datetime.timezone.utc)
            return d.astimezone(datetime.timezone.utc)
        if isinstance(d, datetime.date):
            return datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc)
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

    entries.sort(key=lambda x: _normalize_date(x.get('date')), reverse=True)

    # total excluding delivery tracker costs from the main spendings sum
    total_sum = sum([e['amount'] for e in entries if e['type'] != 'تكاليف التوصيل'])

    return render(request, 'dashboard/spendings_list.html', {
        'entries': entries,
        'total_sum': total_sum
    })

@login_required
def add_purchased_phone(request):
    if request.method == 'POST':
        form = PurchasedPhoneForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('purchased_phone_list')
    else:
        form = PurchasedPhoneForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة الهواتف المشتراة',
        'cancel_url': reverse('purchased_phone_list')
    })

@login_required
def edit_purchased_phone(request, pk):
    item = get_object_or_404(PurchasedPhone, pk=pk)
    if request.method == 'POST':
        form = PurchasedPhoneForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('purchased_phone_list')
    else:
        form = PurchasedPhoneForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل الهواتف المشتراة',
        'cancel_url': reverse('purchased_phone_list')
    })

@login_required
def electronic_service_list(request):
    items = ElectronicService.objects.all()
    return render(request, 'dashboard/electronic_service_list.html', {'items': items})

@login_required
def add_electronic_service(request):
    if request.method == 'POST':
        form = ElectronicServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('electronic_service_list')
    else:
        form = ElectronicServiceForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة الخدمات الإلكترونية',
        'cancel_url': reverse('electronic_service_list')
    })

@login_required
def edit_electronic_service(request, pk):
    item = get_object_or_404(ElectronicService, pk=pk)
    if request.method == 'POST':
        form = ElectronicServiceForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('electronic_service_list')
    else:
        form = ElectronicServiceForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل الخدمات الإلكترونية',
        'cancel_url': reverse('electronic_service_list')
    })

@login_required
def installment_list(request):
    items = Installment.objects.all()
    return render(request, 'dashboard/installment_list.html', {'items': items})

@login_required
def add_installment(request):
    if request.method == 'POST':
        form = InstallmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('installment_list')
    else:
        form = InstallmentForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة الأقساط',
        'cancel_url': reverse('installment_list')
    })

@login_required
def edit_installment(request, pk):
    item = get_object_or_404(Installment, pk=pk)
    if request.method == 'POST':
        form = InstallmentForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('installment_list')
    else:
        form = InstallmentForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل الأقساط',
        'cancel_url': reverse('installment_list')
    })

@login_required
def delivery_tracker_list(request):
    items = DeliveryTracker.objects.all()
    return render(request, 'dashboard/delivery_tracker_list.html', {'items': items})

@login_required
def add_delivery_tracker(request):
    if request.method == 'POST':
        form = DeliveryTrackerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('delivery_tracker_list')
    else:
        form = DeliveryTrackerForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة تتبع الطلبيات',
        'cancel_url': reverse('delivery_tracker_list')
    })

@login_required
def edit_delivery_tracker(request, pk):
    item = get_object_or_404(DeliveryTracker, pk=pk)
    if request.method == 'POST':
        form = DeliveryTrackerForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('delivery_tracker_list')
    else:
        form = DeliveryTrackerForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل تتبع الطلبيات',
        'cancel_url': reverse('delivery_tracker_list')
    })

@login_required
def treasury_list(request):
    items = Treasury.objects.all()
    return render(request, 'dashboard/treasury_list.html', {'items': items})

@login_required
def add_treasury(request):
    if request.method == 'POST':
        form = TreasuryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('treasury_list')
    else:
        form = TreasuryForm()
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'إضافة الخزينة',
        'cancel_url': reverse('treasury_list')
    })

@login_required
def edit_treasury(request, pk):
    item = get_object_or_404(Treasury, pk=pk)
    if request.method == 'POST':
        form = TreasuryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('treasury_list')
    else:
        form = TreasuryForm(instance=item)
    return render(request, 'dashboard/generic_form.html', {
        'form': form, 
        'title': 'تعديل الخزينة',
        'cancel_url': reverse('treasury_list')
    })

@login_required
def used_amounts_list(request):
    items = PurchasedPhone.objects.all()
    total_spent = items.aggregate(total=Sum('purchase_price'))['total'] or 0
    return render(request, 'dashboard/used_amounts_list.html', {'items': items, 'total_spent': total_spent})

@login_required
def external_maintenance_list(request):
    tasks = MaintenanceTask.objects.filter(status='external').order_by('-created_at')
    return render(request, 'dashboard/external_maintenance_list.html', {'tasks': tasks})

@login_required
def supplier_debts_list(request):
    items = Supplier.objects.filter(debt__gt=0)
    total_debt = items.aggregate(total=Sum('debt'))['total'] or 0
    return render(request, 'dashboard/supplier_debts_list.html', {'items': items, 'total_debt': total_debt})



@login_required
def delete_customer(request, pk):
    item = get_object_or_404(Customer, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'customer_list'))

@login_required
def delete_expense(request, pk):
    item = get_object_or_404(Expense, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'expense_list'))

@login_required
def delete_employee(request, pk):
    item = get_object_or_404(Employee, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'employee_list'))

@login_required
def delete_attendance(request, pk):
    item = get_object_or_404(Attendance, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'attendance_list'))

@login_required
def delete_supplier(request, pk):
    item = get_object_or_404(Supplier, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'supplier_list'))

@login_required
def delete_purchased_phone(request, pk):
    item = get_object_or_404(PurchasedPhone, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'purchased_phone_list'))

@login_required
def delete_electronic_service(request, pk):
    item = get_object_or_404(ElectronicService, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'electronic_service_list'))

@login_required
def delete_installment(request, pk):
    item = get_object_or_404(Installment, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'installment_list'))

@login_required
def delete_delivery_tracker(request, pk):
    item = get_object_or_404(DeliveryTracker, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'delivery_tracker_list'))

@login_required
def delete_treasury(request, pk):
    item = get_object_or_404(Treasury, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'treasury_list'))

@login_required
def delete_maintenance(request, pk):
    item = get_object_or_404(MaintenanceTask, pk=pk)
    item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'maintenance_list'))
