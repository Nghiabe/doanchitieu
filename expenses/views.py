from django.shortcuts import render, redirect,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from .models import Category, Expense
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import json
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from userpreferences.models import UserPreference
import datetime
import requests
import pandas as pd
from .models import ExpenseJar
from .models import Expense, ExpenseJar
from sklearn.feature_extraction.text import TfidfVectorizer
from django.contrib.sessions.models import Session
from datetime import date
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
import datetime
from .models import ExpenseLimit
from .models import Expense
from django.core.mail import send_mail
from django.conf import settings
from .form import ExpenseJarForm

data = pd.read_csv('dataset.csv')

# Preprocessing
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
    return ' '.join(tokens)

data['clean_description'] = data['description'].apply(preprocess_text)

# Feature extraction
tfidf_vectorizer = TfidfVectorizer()
X = tfidf_vectorizer.fit_transform(data['clean_description'])

# Train a RandomForestClassifier
model = RandomForestClassifier()
model.fit(X, data['category'])
@login_required(login_url='/authentication/login')
def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user)
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=request.user)

    sort_order = request.GET.get('sort')

    if sort_order == 'amount_asc':
        expenses = expenses.order_by('amount')
    elif sort_order == 'amount_desc':
        expenses = expenses.order_by('-amount')
    elif sort_order == 'date_asc':
        expenses = expenses.order_by('date')
    elif sort_order == 'date_desc':
        expenses = expenses.order_by('-date')

    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    try:
        currency = UserPreference.objects.get(user=request.user).currency
    except:
        currency=None

    total = page_obj.paginator.num_pages
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
        'total': total,
        'sort_order': sort_order,

    }
    return render(request, 'expenses/index.html', context)

daily_expense_amounts = {}

@login_required(login_url='/authentication/login')
def add_expense(request):
    categories = Category.objects.all()
    jars = ExpenseJar.objects.filter(owner=request.user)  # Lấy danh sách các hũ chi tiêu của người dùng
    context = {
        'categories': categories,
        'jars': jars,  # Truyền danh sách hũ chi tiêu vào context
        'values': request.POST
    }

    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        date_str = request.POST.get('expense_date')
        jar_id = request.POST.get('jar')  # Lấy ID hũ chi tiêu đã chọn

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)

        description = request.POST['description']
        date = request.POST['expense_date']
        predicted_category = request.POST['category']

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/add_expense.html', context)

        initial_predicted_category = request.POST.get('initial_predicted_category')
        if predicted_category != initial_predicted_category:
            new_data = {
                'description': description,
                'category': predicted_category,
            }

            update_url = 'http://127.0.0.1:8000/api/update-dataset/'
            response = requests.post(update_url, json={'new_data': new_data})

        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.date.today()

            if date > today:
                messages.error(request, 'Date cannot be in the future')
                return render(request, 'expenses/add_expense.html', context)

            user = request.user
            expense_limits = ExpenseLimit.objects.filter(owner=user)
            if expense_limits.exists():
                daily_expense_limit = expense_limits.first().daily_expense_limit
            else:
                daily_expense_limit = 5000

            total_expenses_today = get_expense_of_day(user) + Decimal(amount)
            if total_expenses_today > daily_expense_limit:
                subject = 'Daily Expense Limit Exceeded'
                message = f'Hello {user.username},\n\nYour expenses for today have exceeded your daily expense limit. Please review your expenses.'
                from_email = settings.EMAIL_HOST_USER
                to_email = [user.email]
                send_mail(subject, message, from_email, to_email, fail_silently=False)
                messages.warning(request, 'Your expenses for today exceed your daily expense limit')

            # Tạo chi tiêu mới và gán cho hũ chi tiêu nếu có
            expense = Expense.objects.create(
                owner=request.user,
                amount=amount,
                date=date,
                category=predicted_category,
                description=description,
                jar_id=jar_id  # Gán hũ chi tiêu cho chi tiêu
            )

            # Cập nhật số tiền trong hũ chi tiêu
            if jar_id:
                jar = ExpenseJar.objects.get(id=jar_id)
                jar.current_spent += Decimal(amount)
                jar.save()

            messages.success(request, 'Expense saved successfully')
            return redirect('expenses')

        except ValueError:
            messages.error(request, 'Invalid date format')
            return render(request, 'expenses/add_expense.html', context)

@login_required(login_url='/authentication/login')
def expense_edit(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories
    }
    if request.method == 'GET':
        return render(request, 'expenses/edit-expense.html', context)
    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        date_str = request.POST.get('expense_date')

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit-expense.html', context)
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/edit-expense.html', context)

        try:
            # Convert the date string to a datetime object and validate the date
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.date.today()

            if date > today:
                messages.error(request, 'Date cannot be in the future')
                return render(request, 'expenses/add_expense.html', context)

            expense.owner = request.user
            expense.amount = amount
            expense. date = date
            expense.category = category
            expense.description = description

            expense.save()
            messages.success(request, 'Expense saved successfully')

            return redirect('expenses')
        except ValueError:
            messages.error(request, 'Invalid date format')
            return render(request, 'expenses/edit_income.html', context)

        # expense.owner = request.user
        # expense.amount = amount
        # expense. date = date
        # expense.category = category
        # expense.description = description

        # expense.save()

        # messages.success(request, 'Expense updated  successfully')

        # return redirect('expenses')

@login_required(login_url='/authentication/login')
def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense removed')
    return redirect('expenses')

@login_required(login_url='/authentication/login')
def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date-datetime.timedelta(days=30*6)
    expenses = Expense.objects.filter(owner=request.user,
                                      date__gte=six_months_ago, date__lte=todays_date)
    finalrep = {}

    def get_category(expense):
        return expense.category
    category_list = list(set(map(get_category, expenses)))

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category=category)

        for item in filtered_by_category:
            amount += item.amount
        return amount

    for x in expenses:
        for y in category_list:
            finalrep[y] = get_expense_category_amount(y)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)

@login_required(login_url='/authentication/login')
def stats_view(request):
    return render(request, 'expenses/stats.html')

@login_required(login_url='/authentication/login')
def predict_category(description):
    predict_category_url = 'http://localhost:8000/api/predict-category/'  # Use the correct URL path
    data = {'description': description}
    response = requests.post(predict_category_url, data=data)

    if response.status_code == 200:
        # Get the predicted category from the response
        predicted_category = response.json().get('predicted_category')
        return predicted_category
    else:
        # Handle the case where the prediction request failed
        return None
    

def set_expense_limit(request):
    if request.method == "POST":
        daily_expense_limit = request.POST.get('daily_expense_limit')
        
        existing_limit = ExpenseLimit.objects.filter(owner=request.user).first()
        
        if existing_limit:
            existing_limit.daily_expense_limit = daily_expense_limit
            existing_limit.save()
        else:
            ExpenseLimit.objects.create(owner=request.user, daily_expense_limit=daily_expense_limit)
        
        messages.success(request, "Daily Expense Limit Updated Successfully!")
        return HttpResponseRedirect('/preferences/')
    else:
        return HttpResponseRedirect('/preferences/')
    
def get_expense_of_day(user):
    current_date=date.today()
    expenses=Expense.objects.filter(owner=user,date=current_date)
    total_expenses=sum(expense.amount for expense in expenses)
    return total_expenses
@login_required
def list_jars(request):
    owned_jars = ExpenseJar.objects.filter(owner=request.user)
    shared_jars = ExpenseJar.objects.filter(members=request.user)
    return render(request, 'expenses/jarlist.html', {
        'owned_jars': owned_jars,
        'shared_jars': shared_jars,
    })

# Tạo hũ chi tiêu mới
@login_required
def create_jar(request):
    if request.method == 'POST':
        form = ExpenseJarForm(request.POST)
        if form.is_valid():
            jar = form.save(commit=False)
            jar.owner = request.user
            jar.save()
            form.save_m2m()  # lưu members nếu có
            return redirect('list_jars')
    else:
        form = ExpenseJarForm()
    return render(request, 'expenses/create_jar.html', {'form': form})

# Chỉnh sửa tên hũ
@login_required
def edit_jar(request, jar_id):
    jar = get_object_or_404(ExpenseJar, id=jar_id, owner=request.user)
    
    if request.method == 'POST':
        new_name = request.POST.get('jar_name')
        if new_name:
            jar.name = new_name
            jar.save()
            return redirect('list_jars')

    return render(request, 'expenses/edit_jar.html', {'jar': jar})

# Chi tiết hũ chi tiêu: chỉ xem nếu là chủ hoặc được chia sẻ
from django.shortcuts import render, get_object_or_404
from .models import ExpenseJar, Expense  # Đảm bảo import đúng

def jar_detail(request, jar_id):
    jar = get_object_or_404(ExpenseJar, id=jar_id)
    expenses = Expense.objects.filter(jar=jar)

    return render(request, 'expenses/jar_detail.html', {
        'jar': jar,
        'expenses': expenses
    })


# Dừng chia sẻ hũ với người khác
@login_required
def unshare_jar(request, jar_id, user_id):
    jar = get_object_or_404(ExpenseJar, id=jar_id, owner=request.user)
    try:
        shared_user = User.objects.get(id=user_id)
        jar.members.remove(shared_user)
        messages.success(request, f"Đã ngừng chia sẻ hũ với {shared_user.username}")
    except User.DoesNotExist:
        messages.error(request, "Không tìm thấy người dùng")
    return redirect('list_jars')
from django.shortcuts import render, get_object_or_404
from .models import ExpenseJar

def share_jar(request, jar_id):
    jar = get_object_or_404(ExpenseJar, id=jar_id)
    # Xử lý chia sẻ, ví dụ gửi email, thêm user...
    return render(request, 'expenses/share_jar.html', {'jar': jar})
@login_required
def delete_jar(request, jar_id):
    jar = get_object_or_404(ExpenseJar, id=jar_id, owner=request.user)

    if request.method == 'POST':
        jar.delete()
        return redirect('jars')  # Sau khi xóa, quay về trang danh sách hũ chi tiêu

    return render(request, 'expenses/confirm_delete_jar.html', {'jar': jar})
