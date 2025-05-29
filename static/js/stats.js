fetch('http://127.0.0.1:8000/expense_category_summary')  // Không có dấu gạch chéo ở cuối
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
    })
    .catch(error => {
        console.error("Error fetching data:", error);
        const tableBody = document.getElementById('categoryTableBody');
        tableBody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Không thể tải dữ liệu.</td></tr>';
    });
