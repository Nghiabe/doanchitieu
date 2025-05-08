document.addEventListener("DOMContentLoaded", function () {
  // Lấy dữ liệu từ server
  fetch('/expenses/expense_category_summary')
      .then(response => response.json())
      .then(data => {
          const chartData = data.expense_category_data;
          const labels = Object.keys(chartData);
          const values = Object.values(chartData);

          // Biểu đồ tròn
          const pieChartCanvas = document.getElementById("pieChart");
          if (pieChartCanvas) {
              new Chart(pieChartCanvas, {
                  type: 'pie',
                  data: {
                      labels: labels,
                      datasets: [{
                          data: values,
                          backgroundColor: [
                              '#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'
                          ]
                      }]
                  },
                  options: {
                      responsive: true,
                      plugins: {
                          tooltip: {
                              callbacks: {
                                  label: function(tooltipItem) {
                                      return `${tooltipItem.label}: ${tooltipItem.raw.toLocaleString('vi-VN')} đ`;
                                  }
                              }
                          }
                      }
                  }
              });
          }

          // Biểu đồ cột
          const barChartCanvas = document.getElementById("barChart");
          if (barChartCanvas) {
              new Chart(barChartCanvas, {
                  type: 'bar',
                  data: {
                      labels: labels,
                      datasets: [{
                          label: 'Chi tiêu',
                          data: values,
                          backgroundColor: '#17a2b8'
                      }]
                  },
                  options: {
                      responsive: true,
                      scales: {
                          y: {
                              beginAtZero: true,
                              ticks: {
                                  callback: function(value) {
                                      return value.toLocaleString('vi-VN') + ' đ';
                                  }
                              }
                          }
                      }
                  }
              });
          }

          // Cập nhật bảng thống kê
          const tableBody = document.getElementById('categoryTableBody');
          tableBody.innerHTML = '';  // Xóa dữ liệu cũ
          labels.forEach((label, index) => {
              const row = `
                  <tr>
                      <td>${index + 1}</td>
                      <td>${label}</td>
                      <td>${values[index].toLocaleString('vi-VN')} đ</td>
                  </tr>
              `;
              tableBody.innerHTML += row;
          });
      })
      .catch(error => {
          console.error("Error fetching data:", error);
          // Hiển thị thông báo lỗi nếu không thể lấy dữ liệu
          const tableBody = document.getElementById('categoryTableBody');
          tableBody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Không thể tải dữ liệu.</td></tr>';
      });
});
