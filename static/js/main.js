console.log("HEmant");

document.addEventListener("DOMContentLoaded", function () {
  // Kiểm tra sự tồn tại của nút "generate-report"
  const generateReportButton = document.getElementById("generate-report");

  if (generateReportButton) {
    // Gắn sự kiện click cho nút "generate-report"
    generateReportButton.addEventListener("click", function () {
      // Kiểm tra sự tồn tại của phần tử "export-options"
      const exportOptions = document.getElementById("export-options");
      if (exportOptions) {
        // Nếu phần tử tồn tại, loại bỏ class "hidden"
        exportOptions.classList.remove("hidden");
      } else {
        console.log('export-options không tồn tại');
      }
    });
  } else {
    console.log('generate-report không tồn tại');
  }
});
