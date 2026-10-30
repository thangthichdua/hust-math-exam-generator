import sympy as sp
import random

# Định nghĩa các biến cơ bản trong SymPy
x, n, k = sp.symbols('x n k')

# --- NGÂN HÀNG HÀM CƠ BẢN (FUNCTION POOLS) ---
# Đây là các "viên gạch" an toàn để xây lên bài toán
POLYNOMIALS = [
    n, n**2, n+1, 2*n+1, n**2+1, n**2-n+1, 3*n-2, n**3+1
]

TRIGONOMETRIC = [
    sp.sin(n), sp.cos(n), sp.sin(2*n), sp.cos(n/2)
]

EXPONENTIALS = [
    2**n, 3**n, 4**n, sp.exp(n), 5**n
]

LOGARITHMICS = [
    sp.log(n), sp.log(n+1), sp.log(n**2+1)
]

def generate_random_function(topic_id, difficulty):
    """
    Hàm lõi: Tự động lắp ráp hàm f(n) dựa trên Chủ đề và Độ khó.
    Trả về: Biểu thức SymPy (expr) và biểu diễn LaTeX (latex_str)
    """
    expr = None

    # --- CHỦ ĐỀ 1 & 2: CHUỖI SỐ DƯƠNG ---
    if topic_id in [1, 2]:
        if difficulty == 1: # Dễ: Đa thức / Đa thức (Dạng 1/n^2)
            tu = random.choice([1, 2, 3, k])
            mau = random.choice(POLYNOMIALS) * random.choice([n, n+1, n+2])
            expr = tu / mau
            
        elif difficulty == 2: # Trung bình: Lũy thừa / Đa thức
            tu = random.choice([1, k]) * random.choice(EXPONENTIALS)
            mau = random.choice(POLYNOMIALS)
            # Random đảo ngược tử mẫu để đa dạng
            expr = tu / mau if random.choice([True, False]) else mau / tu
            
        elif difficulty == 3: # Khó: Trộn cả Đa thức, Lượng giác, Logarit
            tu = random.choice(TRIGONOMETRIC)**2 + random.choice([1, k])
            mau = random.choice(EXPONENTIALS) * random.choice(LOGARITHMICS)
            expr = tu / mau

    # --- CHỦ ĐỀ 3: CHUỖI ĐAN DẤU ---
    elif topic_id == 3:
        # Cấu trúc chung: (-1)^n * (Phần dương)
        sign = (-1)**n
        if difficulty == 1:
            phan_duong = 1 / random.choice(POLYNOMIALS)
        elif difficulty == 2:
            phan_duong = random.choice([n, n+1]) / random.choice([n**2+1, n**2+n])
        else: # difficulty == 3
            phan_duong = random.choice(LOGARITHMICS) / random.choice(EXPONENTIALS)
        
        expr = sign * phan_duong


    if expr is None:
        expr = n**2 + k # Giá trị mặc định chống lỗi

    return expr, sp.latex(expr)

# Chạy thử file này để xem hàm sinh
if __name__ == "__main__":
    for i in range(5):
        func, tex = generate_random_function(topic_id=2, difficulty=2)
        print(f"Lần {i+1}: {func}")