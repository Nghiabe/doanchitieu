# Generated by Django 5.1.1 on 2025-05-05 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0003_alter_expense_options_expensejar_expense_jar'),
    ]

    operations = [
        migrations.AddField(
            model_name='expensejar',
            name='current_spent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='expense',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.AlterField(
            model_name='expenselimit',
            name='daily_expense_limit',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
    ]
