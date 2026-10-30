\# HUST MATH EXAM GENERATOR - ĐỒ ÁN 1

Sinh viên thực hiện: Phạm Toàn Thắng

Mã SV: 20237388





\## 1. GIỚI THIỆU

Đây là phần mềm hỗ trợ quản lý ngân hàng câu hỏi động và sinh đề thi môn Toán Giải tích. 

Phần mềm sử dụng Hệ thống Đại số Máy tính SymPy để tính toán và tự động xuất ra file PDF thông qua hệ thống sắp chữ LaTeX.

\*Lưu ý: Trong phần mềm (file .db) đã được em soạn sẵn các câu hỏi test phức tạp để Thầy tiện đánh giá các tính năng Auto-Reroll, tự tối giản biểu thức và Auto-Layout.\*





\## 2. YÊU CẦU HỆ THỐNG

Để phần mềm hoạt động và xuất được file PDF, máy tính CẦN CÓ:

1\. Python 3.8 trở lên.

2\. Trình biên dịch LaTeX: Máy tính bắt buộc phải cài đặt MiKTeX hoặc TeX Live (Nên ưu tiên TeX Live). 

3\. Nếu chưa có TeX Live hay MiKTeX, app sẽ chỉ xuất ra file .tex





\## 3. HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY CHƯƠNG TRÌNH

Bước 1: Mở Terminal (hoặc CMD) tại thư mục chứa mã nguồn này.

Bước 2: Cài đặt các thư viện Python cần thiết bằng lệnh:

> pip install -r requirements.txt

Bước 3: Chạy phần mềm:

> python main.py



\## 4. HƯỚNG DẪN THỬ NGHIỆM NHANH (TESTING)

1\. Mở app, Thầy sang tab "Tạo Đề Thi".

2\. Chọn chế độ "Soạn Thủ Công".

3\. Bấm "+ Chọn đích danh từ CSDL" và chọn vài câu hỏi (hoặc chọn tất cả).

4\. Tích vào ô "Mở Đề bài sau khi xuất".

5\. Bấm "XUẤT ĐỀ THI".

6\. Hệ thống sẽ mất khoảng 2-3 giây để biên dịch LaTeX và tự động bật file PDF lên màn hình với định dạng chia cột chuẩn mực.



Em xin chân thành cảm ơn Thầy đã dành thời gian đánh giá đồ án của em!

