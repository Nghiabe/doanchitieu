from django.shortcuts import render, redirect, get_object_or_404
from .models import Goal
from .forms import GoalForm, AddAmountForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail

def add_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)  # Chưa lưu ngay
            goal.owner = request.user  # Gán chủ sở hữu là người dùng hiện tại
            goal.save()  # Lưu mục tiêu với chủ sở hữu
            return redirect('list_goals')

    form = GoalForm()
    return render(request, 'goals/add_goals.html', {'form': form})

@login_required(login_url='/authentication/login')
def list_goals(request):
    goals = Goal.objects.filter(owner=request.user)
    add_amount_form = AddAmountForm() 
    return render(request, 'goals/list_goals.html', {'goals': goals, 'add_amount_form': add_amount_form})

@login_required(login_url='/authentication/login')
def add_amount(request, goal_id):
    goal = get_object_or_404(Goal, pk=goal_id)

    if request.method == 'POST':
        form = AddAmountForm(request.POST)
        if form.is_valid():
            additional_amount = form.cleaned_data['additional_amount']
            amount_required = goal.amount_to_save - goal.current_saved_amount

            if additional_amount > amount_required:
                messages.error(request, f'Số tiền tối đa cần để hoàn thành mục tiêu là: {amount_required}.')
            else:
                goal.current_saved_amount += additional_amount
                goal.save()

                # Kiểm tra xem mục tiêu đã đạt được chưa
                if goal.current_saved_amount == goal.amount_to_save:
                    # Gửi email chúc mừng đến người dùng
                    send_congratulatory_email(request.user.email, goal)
                    messages.success(request, 'Chúc mừng! Bạn đã đạt được mục tiêu của mình.')

                    # Tắt nút "Thêm tiền"
                    goal.is_achieved = True
                    goal.delete()
                else:
                    messages.success(request, f'Số tiền đã được thêm thành công. Tổng số tiền đã tiết kiệm: {goal.current_saved_amount}.')
                    messages.info(request, f'Số tiền còn lại để đạt mục tiêu: {amount_required}.')

        return redirect('list_goals')

    # Chuyển hướng đến list_goals nếu phương thức yêu cầu không phải POST
    return redirect('list_goals')

def send_congratulatory_email(email, goal):
    subject = 'Chúc mừng bạn đã hoàn thành mục tiêu!'
    message = f'Chào bạn,\n\nChúc mừng bạn đã đạt được mục tiêu "{goal.name}". Bạn đã tiết kiệm thành công {goal.amount_to_save}.\n\nTiếp tục cố gắng nhé!\n\nTrân trọng,\nTeam Goal Tracker,\nTeam ExpenseWise'
    send_mail(subject, message, 'hemantshirsath24@gmail.com', [email])

def delete_goal(request, goal_id):
    try:
        goal = Goal.objects.get(id=goal_id, owner=request.user)
        goal.delete()
        return redirect('list_goals')
    except Goal.DoesNotExist:
        pass
