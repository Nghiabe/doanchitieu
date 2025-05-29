from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt
from .chatbot_views import chat_with_bot

urlpatterns = [
    # Chi tiêu cá nhân
    path('', views.index, name="expenses"),
    path('check-image-creation/', views.check_image_creation, name='check-image-creation'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('add-expense', views.add_expense, name="add-expenses"),
    path('edit-expense/<int:id>', views.expense_edit, name="expense-edit"),
    path('expense-delete/<int:id>', views.delete_expense, name="expense-delete"),
    path('search-expenses', csrf_exempt(views.search_expenses), name="search_expenses"),
    path('expense_category_summary', views.expense_category_summary, name='expense_category_summary'),
    path('stats', views.stats_view, name="stats"),
    path('set-daily-expense-limit/', views.set_expense_limit, name="set-daily-expense-limit"),

    # Hũ chi tiêu (Expense Jars)
    path('jars/', views.list_jars, name="jars"),
    path('jars/', views.list_jars, name='list_jars'),
    path('jars/create/', views.create_jar, name="create_jar"),
    path('jars/<int:jar_id>/edit/', views.edit_jar, name="edit_jar"),
    path('jars/<int:jar_id>/delete/', views.delete_jar, name='delete_jar'),
#     path('jars/<int:jar_id>/add-expense/', views.add_expense_to_jar, name="add_expense_to_jar"),
    path('jars/<int:jar_id>/detail/', views.jar_detail, name="jar_detail"),

    # Chia sẻ & huỷ chia sẻ hũ chi tiêu
    path('jars/<int:jar_id>/unshare/<int:user_id>/', views.unshare_jar, name="unshare_jar"),
    path('jars/<int:jar_id>/share/', views.share_jar, name='share_jar'),
    path('jars/create/', views.create_jar, name="create_jar"),  # URL cho việc tạo hũ chi tiêu
#     path('jars/', views.jars_view, name='jars'),
]

