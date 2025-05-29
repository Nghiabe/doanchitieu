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
import os
import pandas as pd
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from .models import Expense, ExpenseJar
import pandas as pd
from django.http import HttpResponse




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

    # Lấy giá trị sắp xếp từ GET
    sort_order = request.GET.get('sort')

    # Điều chỉnh thứ tự sắp xếp
    if sort_order == 'amount_asc':
        expenses = expenses.order_by('amount')  # Sắp xếp theo số tiền tăng dần
    elif sort_order == 'amount_desc':
        expenses = expenses.order_by('-amount')  # Sắp xếp theo số tiền giảm dần
    elif sort_order == 'date_asc':
        expenses = expenses.order_by('date')  # Sắp xếp theo ngày tăng dần
    elif sort_order == 'date_desc':
        expenses = expenses.order_by('-date')  # Sắp xếp theo ngày giảm dần (mới nhất lên đầu)
    else:
        # Nếu không có tham số sắp xếp, mặc định sắp xếp theo ngày giảm dần
        expenses = expenses.order_by('-date')

    # Phân trang (hiển thị 5 chi phí mỗi trang)
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Lấy thông tin đơn vị tiền tệ người dùng chọn
    try:
        currency = UserPreference.objects.get(user=request.user).currency
    except UserPreference.DoesNotExist:
        currency = None

    # Tổng số trang
    total_pages = page_obj.paginator.num_pages

    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
        'total': total_pages,
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
@login_required
def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date - datetime.timedelta(days=30*6)
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

    for category in category_list:
        finalrep[category] = get_expense_category_amount(category)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)
@login_required(login_url='/authentication/login')



@login_required(login_url='/authentication/login')
@login_required(login_url='/authentication/login')
@login_required(login_url='/authentication/login')
def stats_view(request):
    try:
        # Fetching the expenses data for the logged-in user
        expenses = Expense.objects.filter(owner=request.user).order_by('date')
        if not expenses.exists():
            messages.error(request, "No expenses found for the logged-in user.")
            return render(request, 'expenses/stats.html')

        data = pd.DataFrame(list(expenses.values('date', 'amount', 'category')))
        
        # Converting 'date' to datetime and setting it as index
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        data.dropna(subset=['date'], inplace=True)  # Remove rows where date conversion failed
        data.set_index('date', inplace=True)

        # 1. Pie chart for expenses by category
        category_expenses = data.groupby('category')['amount'].sum()
        if category_expenses.empty:
            raise ValueError("No valid category data to plot pie chart.")

        plt.figure(figsize=(8, 6))
        category_expenses.plot(kind='pie', autopct='%1.1f%%', startangle=90, legend=False)
        plt.title('Chi tiêu theo danh mục')
        pie_plot_filename = 'category_expenses_pie_chart.png'
        pie_plot_path = os.path.join(settings.BASE_DIR, 'static', 'img', pie_plot_filename)
        plt.savefig(pie_plot_path)
        plt.close()

        # 2. Bar chart for total expenses by jar (if expense jars are used)
        jars_expenses = ExpenseJar.objects.filter(owner=request.user)
        jar_data = {jar.name: jar.current_spent for jar in jars_expenses}

        if not jar_data:
            raise ValueError("No data available for 'Expense Jars' to plot bar chart.")

        plt.figure(figsize=(10, 6))
        plt.bar(jar_data.keys(), jar_data.values(), color='skyblue')
        plt.title('Chi tiêu theo Hũ')
        plt.xlabel('Hũ Chi tiêu')
        plt.ylabel('Số tiền (VNĐ)')
        bar_plot_filename = 'jar_expenses_bar_chart.png'
        bar_plot_path = os.path.join(settings.BASE_DIR, 'static', 'img', bar_plot_filename)
        plt.savefig(bar_plot_path)
        plt.close()

        # 3. Line chart for expenses over time
        total_expenses_over_time = data['amount'].resample('D').sum()

        if total_expenses_over_time.empty:
            raise ValueError("No valid data for plotting expenses over time.")

        plt.figure(figsize=(10, 6))
        plt.plot(total_expenses_over_time, label='Chi tiêu theo ngày', color='green')
        plt.title('Chi tiêu theo ngày')
        plt.xlabel('Ngày')
        plt.ylabel('Số tiền (VNĐ)')
        line_plot_filename = 'daily_expenses_line_chart.png'
        line_plot_path = os.path.join(settings.BASE_DIR, 'static', 'img', line_plot_filename)
        plt.savefig(line_plot_path)
        plt.close()

        # Passing plot filenames and data to the template
        context = {
            'pie_plot_file': pie_plot_filename,
            'bar_plot_file': bar_plot_filename,
            'line_plot_file': line_plot_filename,
            'category_expenses': category_expenses.to_dict(),  # Data for category summary
            'total_expenses': data['amount'].sum(),
        }

        return render(request, 'expenses/stats.html', context)

    except ValueError as ve:
        # Specific exception handling for ValueError
        messages.error(request, f"Error: {str(ve)}")
        print(f"ValueError occurred: {str(ve)}")  # In error to console
        return render(request, 'expenses/stats.html')
    
    except Exception as e:
        # General exception handling
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        print(f"Unexpected error: {str(e)}")  # In error to console
        return render(request, 'expenses/stats.html')

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
def generate_report(request):
    # Thực hiện logic để tạo báo cáo ở đây, ví dụ:
    data = {'some_data': 'value'}  # Đưa vào dữ liệu bạn muốn
    html_content = render_to_string('expenses/report_template.html', data)  # Lấy template HTML cho báo cáo
    
    # Tạo file PDF (ví dụ dùng WeasyPrint để tạo PDF từ HTML)
    pdf = HTML(string=html_content).write_pdf()

    # Trả về file PDF cho người dùng
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    return response
def check_image_creation(request):
    try:
        # Đường dẫn lưu file ảnh trong thư mục static
        image_path = os.path.join(settings.BASE_DIR, 'static', 'test_image.png')
        
        # Tạo một bức ảnh đơn giản với matplotlib
        plt.figure(figsize=(6, 6))
        plt.pie([20, 30, 50], labels=['A', 'B', 'C'], autopct='%1.1f%%', startangle=90)
        plt.title('Test Pie Chart')
        
        # Lưu ảnh vào thư mục static
        plt.savefig(image_path)
        plt.close()  # Đóng cửa sổ hình ảnh để giải phóng tài nguyên
        
        # Trả về thông báo thành công
        return HttpResponse(f"Tệp ảnh đã được tạo thành công tại: {image_path}")
    
    except Exception as e:
        # Trả về thông báo lỗi nếu có vấn đề
        return HttpResponse(f"Đã xảy ra lỗi khi tạo ảnh: {str(e)}")
    try:
        test_file_path = os.path.join(settings.BASE_DIR, 'static', 'test_file.txt')
        
        # Tạo file thử nghiệm
        with open(test_file_path, 'w') as f:
            f.write("This is a test file.")
        
        return HttpResponse(f"Tệp thử nghiệm đã được tạo thành công tại: {test_file_path}")
    
    except Exception as e:
        return HttpResponse(f"Đã xảy ra lỗi: {str(e)}")