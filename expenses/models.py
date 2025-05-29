from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from decimal import Decimal

# Hũ chi tiêu - hỗ trợ chia sẻ cho nhiều người
class ExpenseJar(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_jars')
    members = models.ManyToManyField(User, related_name='shared_jars', blank=True)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2)
    current_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal(0))
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def remaining_budget(self):
        return self.total_budget - self.current_spent

    def __str__(self):
        return f'{self.name} (Chủ: {self.owner.username})'


# Chi tiêu cá nhân (có thể gắn với hũ)
class Expense(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Sử dụng Decimal thay vì Float
    date = models.DateField(default=now)
    description = models.TextField()
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)
    category = models.CharField(max_length=266)
    jar = models.ForeignKey(ExpenseJar, on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Kiểm tra xem đây là chi tiêu mới hay chỉnh sửa
        is_new = self.pk is None
        old_amount = Decimal(0)  # Đảm bảo giá trị là Decimal
        old_jar = None

        if not is_new:
            old_expense = Expense.objects.get(pk=self.pk)
            old_amount = old_expense.amount
            old_jar = old_expense.jar

        # Lưu chi tiêu mới hoặc chỉnh sửa
        super().save(*args, **kwargs)

        # Nếu có hũ chi tiêu, cập nhật số tiền đã chi trong hũ
        if self.jar:
            if is_new:
                self.jar.current_spent += self.amount  # Cộng số tiền chi vào hũ mới
            else:
                if old_jar == self.jar:
                    # Nếu hũ chi tiêu không thay đổi, chỉ cần điều chỉnh số tiền chi
                    diff = self.amount - old_amount
                    self.jar.current_spent += diff
                else:
                    # Nếu hũ chi tiêu thay đổi, trừ đi số tiền cũ trong hũ cũ
                    if old_jar:
                        old_jar.current_spent -= old_amount
                        old_jar.save()
                    # Cộng thêm số tiền chi vào hũ mới
                    self.jar.current_spent += self.amount
            self.jar.save()

    def __str__(self):
        return f'{self.category} - {self.amount}'

    class Meta:
        ordering = ['-date']


# Danh mục (category) chi tiêu
class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# Giới hạn chi tiêu
class ExpenseLimit(models.Model):
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)
    daily_expense_limit = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'{self.owner.username} - {self.daily_expense_limit} VNĐ/ngày'
