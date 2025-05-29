from django.shortcuts import render
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime
from django.utils.timezone import now
from django.contrib import messages
from django.conf import settings
import matplotlib.pyplot as plt
from expenses.models import Expense

def forecast(request):
    expenses = Expense.objects.filter(owner=request.user).order_by('-date')[:30]

    if len(expenses) < 10:
        messages.error(request, "Not enough expenses to make a forecast. Please add more expenses.")
        return render(request, 'expense_forecast/index.html')

    data = pd.DataFrame(list(expenses.values('date', 'amount', 'category')))
    data.set_index('date', inplace=True)

    # Clean the data to make sure 'amount' and 'category' are valid
    data['category'] = data['category'].astype(str)
    data['amount'] = pd.to_numeric(data['amount'], errors='coerce')  # Convert to numeric, invalid will be NaN
    data = data.dropna(subset=['category', 'amount'])

    if data.empty:
        messages.error(request, "No valid data available for forecasting.")
        return render(request, 'expense_forecast/index.html')

    # Grouping data by category
    try:
        category_forecasts = data.groupby('category')['amount'].sum().to_dict()
    except Exception as e:
        messages.error(request, f"Error in grouping data: {e}")
        return render(request, 'expense_forecast/index.html')

    # Fit ARIMA model and forecast
    try:
        model = ARIMA(data['amount'], order=(5, 1, 0))  
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=30)
    except Exception as e:
        messages.error(request, f"An error occurred while fitting the ARIMA model: {str(e)}")
        return render(request, 'expense_forecast/index.html')

    # Prepare forecast data
    forecast_data = pd.DataFrame({'Date': pd.date_range(start=now().date() + pd.DateOffset(1), periods=30, freq='D'), 'Forecasted_Expenses': forecast})
    forecast_data_list = forecast_data.reset_index().to_dict(orient='records')
    
    total_forecasted_expenses = np.sum(forecast)

    # Plotting the forecast
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(data.index, data['amount'], label='Chi tiêu thực tế', color='blue')
        plt.plot(forecast_data['Date'], forecast, label='Chi tiêu dự báo', color='red')
        plt.xlabel('Ngày')  # Đổi tên trục X thành "Ngày"
        plt.ylabel('Chi tiêu (VNĐ)')  # Đổi tên trục Y thành "Chi tiêu (VNĐ)"
        plt.title('Dự báo Chi tiêu trong 30 Ngày tới')  # Đổi tiêu đề đồ thị
        plt.legend(title="Dữ liệu", labels=['Chi tiêu thực tế', 'Chi tiêu dự báo'])

        # Save plot to static/img folder
        plot_file = 'img/forecast_plot.png'
        plt.savefig(f'{settings.BASE_DIR}/static/{plot_file}')
        plt.close()
    except Exception as e:
        messages.error(request, f"An error occurred while creating the plot: {str(e)}")
        return render(request, 'expense_forecast/index.html')

    # Pass the plot and other variables to the template
    context = {
        'forecast_data': forecast_data_list,
        'total_forecasted_expenses': total_forecasted_expenses,
        'category_forecasts': category_forecasts,
        'plot_file': plot_file,  # Pass the path of the plot
    }
    return render(request, 'expense_forecast/index.html', context)
