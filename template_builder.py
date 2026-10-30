import customtkinter as ctk
import random
import re
import sympy as sp
import matplotlib.pyplot as plt
from PIL import Image
import io
import json

class TemplateBuilderIDE(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.vars_list = [] 
        self.setup_ui()

    def setup_ui(self):
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # ==========================================
        # METADATA (XẾP DỌC CHỐNG TRÀN MÀN HÌNH)
        # ==========================================
        frame_meta = ctk.CTkFrame(self.main_scroll)
        frame_meta.pack(fill="x", pady=(0, 10), ipadx=10, ipady=10)
        
        frame_meta.columnconfigure(1, weight=1) # Cột 2 tự động giãn

        ctk.CTkLabel(frame_meta, text="Tuần:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.cb_week = ctk.CTkComboBox(frame_meta, values=[str(i) for i in range(1, 16)])
        self.cb_week.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(frame_meta, text="Chủ đề:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.cb_topic = ctk.CTkComboBox(frame_meta, values=["1 - Đại cương về chuỗi số", "2 - Chuỗi số dương", "3 - Chuỗi có dấu tùy ý", "7 - Chuỗi lũy thừa", "9 - Khai triển Maclaurin/Taylor", "11 - Chuỗi Fourier"])
        self.cb_topic.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(frame_meta, text="Độ khó:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.cb_diff = ctk.CTkComboBox(frame_meta, values=["1 - Dễ", "2 - Trung bình", "3 - Khó"])
        self.cb_diff.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(frame_meta, text="Loại câu hỏi:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.cb_qtype = ctk.CTkComboBox(frame_meta, values=["Tự luận", "Trắc nghiệm 1 ĐÁ", "Trắc nghiệm Nhiều ĐÁ", "Trắc nghiệm Logic"], width=180, command=self.toggle_options_frame)        
        self.cb_qtype.grid(row=3, column=1, sticky="ew", padx=10, pady=5)



        # ==========================================
        # BƯỚC 1: KHAI BÁO THAM SỐ
        # ==========================================
        frame_vars = ctk.CTkFrame(self.main_scroll)
        frame_vars.pack(fill="x", pady=(0, 10), ipadx=10, ipady=10)

        ctk.CTkLabel(frame_vars, text="BƯỚC 1: KHAI BÁO THAM SỐ", font=("Arial", 16, "bold"), text_color="#F39C12").pack(anchor="w", pady=(5, 5), padx=10)

        self.container_vars = ctk.CTkFrame(frame_vars, fg_color="transparent")
        self.container_vars.pack(fill="x", padx=10)

        btn_frame = ctk.CTkFrame(frame_vars, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_frame, text="+ Biến số (Khoảng)", fg_color="#2980B9", command=self.add_var_range).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="+ Biến số (Tập hợp)", fg_color="#16A085", command=lambda: self.add_var_list("Số")).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="+ Biến hàm (Tập hợp)", fg_color="#8E44AD", command=lambda: self.add_var_list("Hàm")).pack(side="left")

        # Sinh mẫu
        self.add_var_range("a", "2", "99", "1")
        self.add_var_list("Số", "b", "5, 10, 15, 20")
        self.add_var_list("Hàm", "f", "sin, cos")

        # ==========================================
        # BƯỚC 2: XƯỞNG CHẾ TẠO & TEST HÀM (ĐÃ NÂNG CẤP EVAL)
        # ==========================================
        frame_sandbox = ctk.CTkFrame(self.main_scroll, border_width=2, border_color="#27AE60")
        frame_sandbox.pack(fill="x", pady=(0, 10), ipadx=10, ipady=10)

        ctk.CTkLabel(frame_sandbox, text="BƯỚC 2: TẠO VÀ TEST HÀM", font=("Arial", 16, "bold"), text_color="#27AE60").pack(anchor="w", pady=(5, 5), padx=10)

        
        # --- BẮT ĐẦU CHÈN THÊM NÚT TỪ ĐIỂN ---
        help_frame = ctk.CTkFrame(frame_sandbox, fg_color="transparent")
        help_frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkButton(help_frame, text="📖 Từ điển LaTeX", width=120, fg_color="#D35400", hover_color="#E67E22", command=self.show_latex_dict).pack(side="left", padx=(0, 10))
        ctk.CTkButton(help_frame, text="🐍 Từ điển Python (SymPy)", width=170, fg_color="#16A085", hover_color="#1ABC9C", command=self.show_python_dict).pack(side="left")
        # --- KẾT THÚC CHÈN NÚT TỪ ĐIỂN ---
        
        sb_input = ctk.CTkFrame(frame_sandbox, fg_color="transparent"); sb_input.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(sb_input, text="Biểu thức LaTeX:").pack(side="left", padx=(0, 10))
        self.ent_sandbox = ctk.CTkTextbox(sb_input, height=60, wrap="char")
        self.ent_sandbox.pack(side="left", fill="x", expand=True)
        self.ent_sandbox.insert("0.0", r"\lim_{x \to 0}\frac{e^{@a@x}-1}{x} = @lim((exp(a*x)-1)/x, x, 0).doit()@")
        ctk.CTkButton(sb_input, text="👀 Vẽ Preview", fg_color="#2980B9", command=self.test_single_expression).pack(side="left", padx=10)
        ctk.CTkButton(sb_input, text="📋 Copy", width=80, fg_color="#E67E22", hover_color="#D35400", command=self.copy_raw_latex).pack(side="left")

        self.lbl_sandbox_res = ctk.CTkLabel(frame_sandbox, text="[Ảnh Preview sẽ hiện ở đây]", height=80, fg_color="#2B2B2B", corner_radius=5)
        self.lbl_sandbox_res.pack(fill="x", padx=10, pady=5)
        self.lbl_sandbox_debug = ctk.CTkLabel(frame_sandbox, text="", text_color="gray")
        self.lbl_sandbox_debug.pack()

        # ==========================================
        # BƯỚC 3: LẮP RÁP CÂU HỎI & ĐÁP ÁN
        # ==========================================
        frame_content = ctk.CTkFrame(self.main_scroll)
        frame_content.pack(fill="x", pady=(0, 10), ipadx=10, ipady=10)

        ctk.CTkLabel(frame_content, text="BƯỚC 3: LẮP RÁP VÀ LƯU", font=("Arial", 16, "bold"), text_color="#3498DB").pack(anchor="w", pady=(5, 5), padx=10)

        ctk.CTkLabel(frame_content, text="Đề bài:").pack(anchor="w", padx=10)
        self.txt_question = ctk.CTkTextbox(frame_content, height=80)
        self.txt_question.pack(fill="x", padx=10, pady=5)

        self.dynamic_frame = ctk.CTkFrame(frame_content, fg_color="transparent")
        self.dynamic_frame.pack(fill="x", padx=10)
        self.layout_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        ctk.CTkLabel(self.layout_frame, text="Trình bày PDF:").pack(side="left", pady=5)
        self.cb_cols = ctk.CTkComboBox(self.layout_frame, values=["1 cột", "2 cột", "4 cột"], width=120)
        self.cb_cols.pack(side="left", padx=10, pady=5)

        # 1. Khung Tự luận
        self.solution_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        ctk.CTkLabel(self.solution_frame, text="HD Chấm Tự Luận:").pack(anchor="w")
        self.txt_solution = ctk.CTkTextbox(self.solution_frame, height=60)
        self.txt_solution.pack(fill="x", pady=5)

        # 2. Khung Trắc nghiệm Thường (Lưới Động)
        self.opts_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        self.opts_grid = ctk.CTkFrame(self.opts_frame, fg_color="transparent"); self.opts_grid.pack(fill="x", pady=5)
        self.opt_entries = {}
        self.opt_widgets = [] 
        for _ in range(4): self.add_mcq_option()
        
        btn_mcq_frame = ctk.CTkFrame(self.opts_frame, fg_color="transparent"); btn_mcq_frame.pack(anchor="w", pady=(0, 5))
        ctk.CTkButton(btn_mcq_frame, text="+ Thêm đáp án", width=120, fg_color="#8E44AD", hover_color="#9B59B6", command=self.add_mcq_option).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_mcq_frame, text="- Xóa đáp án cuối", width=120, fg_color="#C0392B", hover_color="#E74C3C", command=self.remove_mcq_option).pack(side="left")
        
        ctk.CTkLabel(self.opts_frame, text="Đáp án ĐÚNG (Nhập A, B, C...):").pack(anchor="w", pady=(5,0))
        self.ent_correct = ctk.CTkEntry(self.opts_frame, width=300); self.ent_correct.pack(anchor="w", pady=5)

        # 3. Khung Trắc nghiệm LOGIC (MỚI)
        self.logic_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        ctk.CTkLabel(self.logic_frame, text="Tập đáp án khả thi (Ans Pool - Cách nhau bằng dấu GẠCH ĐỨNG '|'):", text_color="#E67E22").pack(anchor="w")
        self.ent_ans_pool = ctk.CTkEntry(self.logic_frame)
        self.ent_ans_pool.pack(fill="x", pady=5)
        self.ent_ans_pool.insert("0", "Hội tụ | Phân kì | Bán hội tụ | Đan dấu")

        ctk.CTkLabel(self.logic_frame, text="Quy tắc chọn (Logic Rule) - Viết code Python định nghĩa biến 'correct_ans':", text_color="#E67E22").pack(anchor="w", pady=(5,0))
        self.txt_logic_rule = ctk.CTkTextbox(self.logic_frame, height=80, font=("Consolas", 13))
        self.txt_logic_rule.pack(fill="x", pady=5)
        self.txt_logic_rule.insert("0.0", "if a > 5:\n    correct_ans = 'Hội tụ'\nelse:\n    correct_ans = 'Phân kì'")

        btn_test_logic = ctk.CTkButton(self.logic_frame, text="⚙️ Test thử Logic ngay", fg_color="#F39C12", hover_color="#D35400", command=self.test_logic_rule)
        btn_test_logic.pack(anchor="w", pady=5)
        self.lbl_logic_res = ctk.CTkLabel(self.logic_frame, text="", text_color="gray")
        self.lbl_logic_res.pack(anchor="w")

    # NÚT LƯU CSDL
        self.btn_save = ctk.CTkButton(self.main_scroll, text="💾 LƯU VÀO CƠ SỞ DỮ LIỆU", height=45, font=("Arial", 14, "bold"), fg_color="#27AE60", command=self.save_to_db)
        self.btn_save.pack(fill="x", pady=10)        
        self.toggle_options_frame(self.cb_qtype.get())

    def set_edit_mode(self, ex_id, parent_app, toplevel_window):
        """Kích hoạt chế độ Chỉnh sửa thay vì Thêm mới"""
        self.edit_id = ex_id
        self.parent_app = parent_app
        self.toplevel_window = toplevel_window
        self.btn_save.configure(text="💾 CẬP NHẬT THAY ĐỔI CÂU HỎI", fg_color="#E67E22", hover_color="#D35400")

    def set_temp_mode(self, callback, toplevel_window):
        """Kích hoạt chế độ Viết câu hỏi Tạm thời (Không lưu CSDL)"""
        self.is_temp_mode = True
        self.temp_callback = callback
        self.toplevel_window = toplevel_window
        self.btn_save.configure(text="💾 LƯU VÀO ĐỀ (TẠM THỜI)", fg_color="#8E44AD", hover_color="#9B59B6")

    def load_data(self, ex_data):
        """Đổ dữ liệu từ CSDL vào Form"""
        old_week, old_topic, old_diff, old_latex, old_qtype, old_opts_json, old_logic, old_func_text, old_bad_seeds = ex_data
        
        self.cb_week.set(str(old_week))
        self.cb_diff.set(f"{old_diff} - Dễ" if old_diff == 1 else f"{old_diff} - Trung bình" if old_diff == 2 else f"{old_diff} - Khó")
        try:
            topic_str = [t for t in self.cb_topic.cget("values") if t.startswith(str(old_topic) + " - ")][0]
            self.cb_topic.set(topic_str)
        except: pass
        self.cb_qtype.set(old_qtype if old_qtype else "Tự luận")
        self.toggle_options_frame(self.cb_qtype.get())
        
        # Load Đề bài
        self.txt_question.delete("0.0", "end")
        self.txt_question.insert("0.0", old_latex)
        
        # Xóa các biến hiện tại và nạp biến cũ
        for v in self.vars_list:
            v["frame"].destroy()
        self.vars_list.clear()
        
        try:
            var_data = json.loads(old_func_text)
            for v in var_data:
                if v["type"] == "range":
                    self.add_var_range(v["name"], str(v["range"][0]), str(v["range"][1]), str(v["range"][2]))
                elif v["type"] == "list":
                    self.add_var_list("Tập hợp", v["name"], ", ".join(map(str, v["set"])))
        except: pass

        # Load Đáp án / Logic
        if old_opts_json:
            try:
                opts_dict = json.loads(old_opts_json)
                self.cb_cols.set(f"{opts_dict.get('cols', 1)} cột")
                if opts_dict.get("is_logic_pool"):
                    self.ent_ans_pool.delete(0, 'end')
                    self.ent_ans_pool.insert(0, " | ".join(opts_dict.get("ans_pool", [])))
                    self.txt_logic_rule.delete("0.0", "end")
                    self.txt_logic_rule.insert("0.0", opts_dict.get("logic_rule", ""))
                else:
                    # --- FIX LỖI TREO MÁY Ở ĐÂY ---
                    # Xóa thủ công toàn bộ widget đáp án hiện có thay vì dùng while
                    for char, lbl, ent in self.opt_widgets:
                        lbl.destroy()
                        ent.destroy()
                    self.opt_widgets.clear()
                    self.opt_entries.clear()
                    # -------------------------------

                    # Điền lại
                    for char in [chr(65+i) for i in range(26)]:
                        if char in opts_dict and char != "correct":
                            self.add_mcq_option()
                            self.opt_entries[char].insert(0, opts_dict[char])
                    self.ent_correct.delete(0, 'end')
                    self.ent_correct.insert(0, opts_dict.get("correct", ""))
            except: pass
        else:
            self.txt_solution.delete("0.0", "end")
            self.txt_solution.insert("0.0", old_logic if old_logic else "")
    # --- HÀM ẨN HIỆN KHUNG ---
    def toggle_options_frame(self, choice):
        # Ẩn toàn bộ các khung đi trước
        self.solution_frame.pack_forget()
        self.opts_frame.pack_forget()
        self.logic_frame.pack_forget()
        self.layout_frame.pack_forget() # Ẩn luôn khung chọn số cột

        # Hiển thị lại dựa theo lựa chọn
        if choice == "Trắc nghiệm Logic":
            self.layout_frame.pack(fill="x", pady=(0, 5)) # Hiện chọn cột
            self.logic_frame.pack(fill="x")
        elif "Trắc nghiệm" in choice:
            self.layout_frame.pack(fill="x", pady=(0, 5)) # Hiện chọn cột
            self.opts_frame.pack(fill="x")
        else:
            self.solution_frame.pack(fill="x") # Tự luận thì không hiện chọn cột

    # --- HÀM TEST LOGIC (Cho phép thầy cô thử xem code mình viết có chạy đúng không) ---
    def test_logic_rule(self):
        params = self.get_random_params()
        pool_str = self.ent_ans_pool.get().strip()
        logic_code = self.txt_logic_rule.get("0.0", "end").strip()

        if not pool_str or not logic_code:
            self.lbl_logic_res.configure(text="Lỗi: Hãy nhập Ans Pool và Logic Rule", text_color="red")
            return

        pool = [x.strip() for x in pool_str.split("|")]
        local_env = params.copy() # Bơm các tham số (VD: a=3) vào môi trường nội bộ

        try:
            # Dùng lệnh exec() để chạy khối code if/else của thầy cô
            exec(logic_code, {"__builtins__": {}}, local_env)
            
            if "correct_ans" not in local_env:
                self.lbl_logic_res.configure(text="Lỗi: Code của bạn phải gán giá trị cho biến 'correct_ans'!", text_color="red")
                return

            correct_ans = str(local_env["correct_ans"])
            if correct_ans not in pool:
                self.lbl_logic_res.configure(text=f"Cảnh báo: '{correct_ans}' không nằm trong Ans Pool!", text_color="#E67E22")
            
            wrongs = [ans for ans in pool if ans != correct_ans]
            
            # Hiển thị kết quả ra màn hình cho thầy cô yên tâm
            debug_str = f"✅ Với bộ số {params}:\n- Đáp án ĐÚNG được chọn: [{correct_ans}]\n- Đáp án SAI tự sinh: {wrongs}"
            self.lbl_logic_res.configure(text=debug_str, text_color="#27AE60")
        except Exception as e:
            self.lbl_logic_res.configure(text=f"Lỗi cú pháp Python trong logic: {e}", text_color="red")
    
    def add_mcq_option(self):
        current_count = len(self.opt_entries)
        if current_count >= 26: return 
        
        char = chr(65 + current_count) 
        row, col = current_count // 2, (current_count % 2) * 2 
        
        lbl = ctk.CTkLabel(self.opts_grid, text=f"{char}:")
        lbl.grid(row=row, column=col, sticky="e", padx=(0, 5), pady=5)
        ent = ctk.CTkEntry(self.opts_grid, width=300)
        ent.grid(row=row, column=col+1, sticky="w", padx=(0, 20), pady=5)
        
        self.opt_entries[char] = ent
        self.opt_widgets.append((char, lbl, ent)) # Lưu lại cụm widget để xóa

    def remove_mcq_option(self):
        if len(self.opt_widgets) > 2: # Giữ lại tối thiểu 2 đáp án A, B
            char, lbl, ent = self.opt_widgets.pop()
            lbl.destroy() # Xóa chữ cái
            ent.destroy() # Xóa ô nhập
            del self.opt_entries[char] # Xóa khỏi danh sách theo dõi

    # --- CÁC HÀM THÊM BIẾN ---
    def add_var_range(self, default_name="", default_start="", default_end="", default_step=""):
        row = ctk.CTkFrame(self.container_vars, fg_color="transparent"); row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Biến (Khoảng):").pack(side="left", padx=2)
        ent_name = ctk.CTkEntry(row, width=40); ent_name.pack(side="left", padx=2); ent_name.insert("0", default_name)
        ctk.CTkLabel(row, text="Từ:").pack(side="left", padx=2)
        ent_start = ctk.CTkEntry(row, width=40); ent_start.pack(side="left", padx=2); ent_start.insert("0", default_start)
        ctk.CTkLabel(row, text="Đến:").pack(side="left", padx=2)
        ent_end = ctk.CTkEntry(row, width=40); ent_end.pack(side="left", padx=2); ent_end.insert("0", default_end)
        ctk.CTkLabel(row, text="Bước:").pack(side="left", padx=2)
        ent_step = ctk.CTkEntry(row, width=40); ent_step.pack(side="left", padx=2); ent_step.insert("0", default_step)
        ctk.CTkButton(row, text="X", width=30, fg_color="#C0392B", command=row.destroy).pack(side="left", padx=10)
        self.vars_list.append({"type": "range", "name": ent_name, "start": ent_start, "end": ent_end, "step": ent_step, "frame": row})

    def add_var_list(self, label_prefix, default_name="", default_vals=""):
        row = ctk.CTkFrame(self.container_vars, fg_color="transparent"); row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=f"Biến ({label_prefix}):").pack(side="left", padx=2)
        ent_name = ctk.CTkEntry(row, width=40); ent_name.pack(side="left", padx=2); ent_name.insert("0", default_name)
        ctk.CTkLabel(row, text="Tập hợp (cách nhau dấu ,):").pack(side="left", padx=2)
        ent_vals = ctk.CTkEntry(row, width=250); ent_vals.pack(side="left", padx=2, fill="x", expand=True); ent_vals.insert("0", default_vals)
        ctk.CTkButton(row, text="X", width=30, fg_color="#C0392B", command=row.destroy).pack(side="left", padx=10)
        self.vars_list.append({"type": "list", "name": ent_name, "vals": ent_vals, "frame": row})

    # --- HÀM VẼ ẢNH LATEX ---
    def render_latex_image(self, formula):
        try:
            fig = plt.figure(figsize=(7, 1.5), dpi=100)
            fig.patch.set_facecolor('#2B2B2B')
            if not formula.strip().startswith('$'): formula = f"${formula}$"
            plt.text(0.5, 0.5, formula, size=16, ha='center', va='center', color='white')
            plt.axis('off')
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
            buf.seek(0)
            img = Image.open(buf)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            self.lbl_sandbox_res.configure(image=ctk_img, text="")
            plt.close(fig)
        except Exception as e:
            self.lbl_sandbox_res.configure(image="", text=f"Lỗi vẽ ảnh: {e}")

    # --- THUẬT TOÁN TEST & PREVIEW ĐƯỢC NÂNG CẤP ---
    def get_random_params(self):
        current_vars = {}
        for v in self.vars_list:
            if v["frame"].winfo_exists():
                name = v["name"].get().strip()
                if v["type"] == "range":
                    try:
                        start, end, step = int(v["start"].get()), int(v["end"].get()), int(v["step"].get())
                        current_vars[name] = random.choice(range(start, end + 1, step))
                    except: pass
                elif v["type"] == "list":
                    vals = [x.strip() for x in v["vals"].get().split(',')]
                    if vals and vals[0]: current_vars[name] = random.choice(vals)
        return current_vars

    def test_single_expression(self):
        expr = self.ent_sandbox.get("0.0", "end").strip()
        if not expr: return
        
        params = self.get_random_params()
        self.lbl_sandbox_debug.configure(text=f"Đã bốc ngẫu nhiên: {params}")
        
        import sympy as sp
        import re
        
        safe_env = {
            'x': sp.Symbol('x'), 'n': sp.Symbol('n'), 'y': sp.Symbol('y'),
            'lim': sp.limit, 'limit': sp.limit,
            'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
            'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
            'pi': sp.pi, 'oo': sp.oo, 'sp': sp,
            'abs': sp.Abs, 'sqrt': sp.sqrt, 'root': sp.root,
            'integrate': sp.integrate, 'diff': sp.diff,
            'Sum': sp.Sum, 'simplify': sp.simplify, 'series': sp.series,
            'ln': sp.log, 
            'log': lambda val, base=10: sp.log(val, base),
            'e': sp.E
        }

        def evaluate_match(match):
            inner_code = match.group(1).strip() 
            for k, v in params.items():
                inner_code = re.sub(rf'\b{k}\b', str(v), inner_code)
            try:
                result = eval(inner_code, {"__builtins__": {}}, safe_env)
                if result == sp.sin: return r"\sin "
                if result == sp.cos: return r"\cos "
                if result == sp.tan: return r"\tan "
                if result == sp.exp: return r"e^"
                if result == sp.log: return r"\ln "
                
                if isinstance(result, (sp.Basic, sp.MatrixBase)): 
                    if "series" in inner_code:
                        return sp.latex(result, ln_notation=True, order='rev-lex')
                    return sp.latex(result, ln_notation=True) 
                return str(result)
            except:
                return str(inner_code)

        try:
            final_latex = re.sub(r'@(.*?)@', evaluate_match, expr)
            final_latex = final_latex.replace("asin", r"\arcsin").replace("acos", r"\arccos")
            
            def clean_log(m):
                A = m.group(1).replace(r'\left(', '').replace(r'\right)', '').strip()
                B = m.group(2).replace(r'\left(', '').replace(r'\right)', '').strip()
                if A.startswith('(') and A.endswith(')'): A = A[1:-1]
                if B.startswith('(') and B.endswith(')'): B = B[1:-1]
                return rf'\log_{{{B}}}\left({A}\right)'
                
            final_latex = re.sub(r'\\frac\{\\ln\s*\{(.*?)\}\}\{\\ln\s*\{(.*?)\}\}', clean_log, final_latex)
            
            # --- BƯỚC TẠM CẤT CẬN TÍCH PHÂN & TỔNG ĐỂ BẢO VỆ ---
            protected = []
            def protect(m):
                protected.append(m.group(0))
                return f"__PROT{len(protected)-1}__"
            # Nhận diện \int_{0}^{1}, \sum_{1}^{1}... và giấu đi
            final_latex = re.sub(r'\\(?:int|sum|prod)(?:\\limits)?_(?:\{[^}]*\}|[a-zA-Z0-9])\^(?:\{1\}|1)(?!\d)', protect, final_latex)

            # --- 1. DỌN LỖI 1^n (Đã nâng cấp chống lỗi số thập phân .1) ---
            final_latex = re.sub(r'(?<![\d.])1\^\{[^\}]+\}', '1', final_latex)
            final_latex = re.sub(r'(?<![\d.])1\^[a-zA-Z0-9]+', '1', final_latex)
            final_latex = re.sub(r'\\left\(1\\right\)\^\{[^\}]+\}', '1', final_latex)
            final_latex = re.sub(r'\\left\(1\\right\)\^[a-zA-Z0-9]+', '1', final_latex)

            # --- 1.5. TỐI GIẢN PHÉP NHÂN TƯỜNG MINH VỚI 1 (\cdot 1 hoặc 1 \cdot) ---
            final_latex = re.sub(r'(?<![\d.])1\s*(?:\\cdot|\*)\s*', '', final_latex) # Xóa "1 \cdot " đứng trước
            final_latex = re.sub(r'\s*(?:\\cdot|\*)\s*1(?![\d.])', '', final_latex)  # Xóa " \cdot 1" đứng sau

            # --- 2. TỐI GIẢN TÍCH 1x ---
            final_latex = re.sub(r'(^|[-+=({\[<>/,\s]+)1\s*(?:\\cdot\s*|\*\s*)?(?!\\(?:times|cdot|div|pm|mp|ge|le|neq|approx|right|limits|quad|qquad)\b)([a-zA-Z]|\\[a-zA-Z]+)', r'\1\2', final_latex)
            
            # --- 3. TỐI GIẢN PHÂN SỐ CHIA 1 ---
            final_latex = re.sub(r'\\frac\{((?:[^{}]|\{[^{}]*\})*)\}\{1\}', r'\1', final_latex)
            final_latex = final_latex.replace(r"\frac{1}{1}", "1").replace("1/1", "1")
            
            # --- 4. XÓA SẠCH MŨ 1 (Bao gồm cả ln(x)^1) ---
            # Do tích phân đã giấu đi nên chém toàn bộ ^1 ở đây an toàn tuyệt đối!
            final_latex = re.sub(r'\^\{1\}', '', final_latex)
            final_latex = re.sub(r'\^1(?!\d)', '', final_latex)

            # --- BƯỚC TRẢ LẠI CẬN TÍCH PHÂN TỪ NƠI CẤT GIẤU ---
            for i, p in enumerate(protected):
                final_latex = final_latex.replace(f"__PROT{i}__", p)

            final_latex = final_latex.replace(r"\left(\left(", r"\left(").replace(r"\right)\right)", r"\right)")
            final_latex = final_latex.replace(r"((", r"(").replace(r"))", r")")

            # --- XÓA ĐUÔI .0 (VD: 30.0 -> 30, 5.0x -> 5x) ---
            final_latex = re.sub(r'\.0+(?!\d)', '', final_latex)
            
            self.render_latex_image(final_latex)
        except Exception as e:
            self.lbl_sandbox_debug.configure(text=f"Lỗi: {e}")
    
    def copy_raw_latex(self):
        raw_text = self.ent_sandbox.get("0.0", "end").strip()
        if raw_text:
            self.clipboard_clear()
            self.clipboard_append(raw_text)
            self.update()
            self.lbl_sandbox_debug.configure(text="Đã copy biểu thức vào khay nhớ tạm!", text_color="#27AE60")

    # --- HÀM LƯU CSDL ---
    def save_to_db(self):
        week = self.cb_week.get().replace("Tuần ", "")
        topic = self.cb_topic.get()
        diff = self.cb_diff.get()
        q_type = self.cb_qtype.get()
        cols_val = int(self.cb_cols.get().split()[0]) # Lấy con số 1, 2, hoặc 4
        
        var_data = []
        for v in self.vars_list:
            if v["frame"].winfo_exists():
                if v["type"] == "range":
                    var_data.append({"type": "range", "name": v["name"].get(), "range": [v["start"].get(), v["end"].get(), v["step"].get()]})
                else:
                    var_data.append({"type": "list", "name": v["name"].get(), "set": v["vals"].get().split(',')})
        func_text = json.dumps(var_data, ensure_ascii=False) 
        
        latex_template = self.txt_question.get("0.0", "end").strip()
        solution_logic = ""
        options_json = ""
        bad_seeds_list = [] # Lưu trữ các seed sinh đáp án trùng
        
        if q_type == "Trắc nghiệm Logic":
            opts = {
                "cols": cols_val,  # <--- Thêm dòng này
                "is_logic_pool": True,
                "ans_pool": [x.strip() for x in self.ent_ans_pool.get().split("|")],
                "logic_rule": self.txt_logic_rule.get("0.0", "end").strip()
            }
            options_json = json.dumps(opts, ensure_ascii=False)
        elif "Trắc nghiệm" in q_type:
            opts = {"cols": cols_val} # <--- Thêm dòng này
            for char, ent in self.opt_entries.items():
                val = ent.get().strip()
                if val: opts[char] = val
            opts["correct"] = self.ent_correct.get().strip()
            options_json = json.dumps(opts, ensure_ascii=False)
            
            # --- KIỂM TRA BAD SEEDS ---
            safe_env = {
                'x': sp.Symbol('x'), 'n': sp.Symbol('n'), 'y': sp.Symbol('y'),
                'lim': sp.limit, 'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
                'pi': sp.pi, 'oo': sp.oo, 'sp': sp, 'abs': sp.Abs, 'sqrt': sp.sqrt, 
                'integrate': sp.integrate, 'diff': sp.diff, 'Sum': sp.Sum, 'simplify': sp.simplify
            }
            
            def simulate_eval(template_str, p_dict):
                if not template_str: return ""
                def evaluate_match(match):
                    inner_code = match.group(1).strip()
                    for k, v in p_dict.items():
                        inner_code = re.sub(rf'\b{k}\b', str(v), inner_code)
                    try:
                        res = eval(inner_code, {"__builtins__": {}}, safe_env)
                        if isinstance(res, (sp.Basic, sp.MatrixBase)): return sp.latex(res)
                        return str(res)
                    except: return str(inner_code)
                return re.sub(r'@(.*?)@', evaluate_match, template_str)

            for s in range(1, 101):
                random.seed(s)
                sim_params = {}
                for v in var_data:
                    name = v["name"]
                    if v["type"] == "range":
                        sim_params[name] = random.choice(range(int(v["range"][0]), int(v["range"][1]) + 1, int(v["range"][2])))
                    elif v["type"] == "list":
                        val = random.choice(v["set"])
                        try:
                            if val.strip().lstrip('-').isdigit(): val = int(val.strip())
                        except: pass
                        sim_params[name] = val
                
                evaluated_vals = []
                # --- KIỂM TRA TRÙNG CHO CẢ LOGIC VÀ TRẮC NGHIỆM THƯỜNG ---
                if opts.get("is_logic_pool"):
                    pool = opts.get("ans_pool", [])
                    for v in pool:
                        evaluated_vals.append(simulate_eval(str(v), sim_params))
                else:
                    for char in ['A', 'B', 'C', 'D', 'E', 'F']:
                        if char in opts and char != "correct":
                            evaluated_vals.append(simulate_eval(str(opts[char]), sim_params))
                
                # Nếu có bất kỳ đáp án nào giống hệt nhau -> Seed này bị dính Bad Seed
                if len(set(evaluated_vals)) < len(evaluated_vals):
                    bad_seeds_list.append(str(s))
            
            random.seed() # Reset lại random

        else:
            solution_logic = self.txt_solution.get("0.0", "end").strip()
            
        try:
            import database
            diff_val = int(diff.split(" - ")[0])
            bad_seeds_str = ",".join(bad_seeds_list)

            # --- CHẾ ĐỘ LƯU TẠM THỜI (DÀNH CHO SOẠN ĐỀ THỦ CÔNG) ---
            if getattr(self, 'is_temp_mode', False):
                # Tạo ID tạm nếu chưa có, hoặc giữ nguyên ID tạm cũ nếu đang Edit
                temp_id = getattr(self, 'edit_id', f"Temp_{random.randint(10000, 99999)}")
                
                # Trả về 1 tuple 11 phần tử chứa đầy đủ thông tin để in đề
                temp_tuple = (temp_id, func_text, 1, latex_template, q_type, options_json, solution_logic, bad_seeds_str, int(week), int(topic.split(" - ")[0]), diff_val)
                self.temp_callback(temp_tuple)
                
                if hasattr(self, 'toplevel_window') and self.toplevel_window:
                    self.toplevel_window.destroy()
                return # Thoát hàm, không chạy phần lưu CSDL bên dưới nữa!
            # =======================================================
            
            # --- PHÂN NHÁNH: UPDATE HOẶC INSERT ---
            if hasattr(self, 'edit_id') and self.edit_id:
                database.update_exercise(self.edit_id, int(week), int(topic.split(" - ")[0]), diff_val, func_text, latex_template, q_type, options_json, solution_logic, bad_seeds_str)
                msg = "Đã cập nhật câu hỏi thành công!"
            else:
                database.insert_exercise(
                    week_id=int(week), topic_id=int(topic.split(" - ")[0]), difficulty=diff_val, 
                    function_text=func_text, has_parameter=1, latex_template=latex_template, 
                    q_type=q_type, options=options_json, logic=solution_logic, bad_seeds=bad_seeds_str
                )
                msg = "Đã lưu Template vào Ngân hàng đề!"
            
            from tkinter import messagebox
            if bad_seeds_list:
                messagebox.showwarning("Cảnh báo Seed trùng", f"{msg}\nTUY NHIÊN, các Seed sau sẽ tạo ra đáp án giống nhau:\n{bad_seeds_str}")
            else:
                messagebox.showinfo("Thành công", msg)
                
            # Đóng cửa sổ và Refesh bảng nếu đang ở chế độ Edit
            if hasattr(self, 'toplevel_window') and self.toplevel_window:
                self.toplevel_window.destroy()
                if self.parent_app:
                    self.parent_app.load_db_data()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi CSDL", f"Không thể lưu: {e}")
            
            from tkinter import messagebox
            if bad_seeds_list:
                messagebox.showwarning("Cảnh báo Seed trùng", f"Câu hỏi đã được lưu.\nTUY NHIÊN, các Seed sau đây sẽ tạo ra 2 hoặc nhiều đáp án trắc nghiệm giống nhau:\n{bad_seeds_str}\n(Đã lưu cảnh báo này vào CSDL).")
            else:
                messagebox.showinfo("Thành công", "Đã lưu Template vào Ngân hàng đề! (100 Seed đều an toàn).")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi CSDL", f"Không thể lưu: {e}")
# --- BẮT ĐẦU DÁN 2 HÀM TỪ ĐIỂN ---
    def show_latex_dict(self):
        win = ctk.CTkToplevel(self)
        win.title("Từ điển câu lệnh LaTeX")
        win.geometry("650x550")
        win.attributes("-topmost", True) # Giữ cửa sổ luôn nổi lên trên
        
        txt = ctk.CTkTextbox(win, font=("Consolas", 14), wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        
        content = """📚 TỪ ĐIỂN LATEX CƠ BẢN DÀNH CHO GIÁO VIÊN

CHÚ Ý: 
    - Thêm \displaystyle vào đầu công thức sẽ giúp LaTeX hiển thị đẹp hơn, đặc biệt là với các biểu thức dài, các hàm lim, tổng Sigma hoặc có phân số. 
    - Muốn xuống dòng thì thêm \\newline vào cuối dòng trước đó.
    - Nên cho toàn bộ biểu thức vào giữa 2 dấu $ để đảm bảo hiển thị đúng khi dán vào khung Đề bài/Đáp án (ví dụ: $\dfrac{1}{x+1}$).
    
Ví dụ: \displaystyle \dfrac{1}{x+1}.

1. Phân số: 
   - Cú pháp: \dfrac{Tử}{Mẫu}  (hoặc \\frac{}{})
   - Ví dụ:   \dfrac{1}{x+1}

2. Lũy thừa & Chỉ số dưới:
   - Cú pháp: Cơ_số^{Mũ} hoặc Biến_{Chỉ_số}
   - Ví dụ:   x^2,  e^{5x},  u_n,  x_{12}

3. Giới hạn (Limit):
   - Cú pháp: \lim_{biến \\to giá_trị}
   - Ví dụ:   \lim_{x \\to 0},  \lim_{n \\to \infty}

4. Tích phân (Integral):
   - Cú pháp: \int_{Cận_dưới}^{Cận_trên}
   - Ví dụ:   \int_{0}^{\pi} \sin(x) dx

5. Tổng Sigma:
   - Cú pháp: \sum_{Chỉ_số_dưới}^{Chỉ_số_trên}
   - Ví dụ:   \sum_{n=1}^{\infty} \dfrac{1}{n^2}

6. Các ký hiệu đặc biệt:
   - Vô cùng:       \infty (hoặc +\infty)
   - Số Pi:         \pi
   - Dấu nhân:      \\times
   - Dấu cộng trừ:  \pm
   - Căn bậc hai:   \sqrt{x}
   - Căn bậc n:     \sqrt[n]{x}

MẸO: Khung test (Sandbox) đã tự động xử lý hình ảnh, nhưng khi dán xuống khung Đề bài/Đáp án để xuất file, hãy nhớ bọc công thức giữa 2 dấu $ (ví dụ: $\dfrac{1}{2}$).
"""
        txt.insert("0.0", content)
        txt.configure(state="disabled") # Khóa chỉ cho phép Copy, không cho gõ bậy vào

    def show_python_dict(self):
        win = ctk.CTkToplevel(self)
        win.title("Từ điển câu lệnh Python (SymPy)")
        win.geometry("750x600")
        win.attributes("-topmost", True)
        
        txt = ctk.CTkTextbox(win, font=("Consolas", 14), wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        
        content = """🐍 TỪ ĐIỂN PYTHON (SYMPY) ĐỂ TÍNH TOÁN TRONG @...@

CHÚ Ý: Mọi biểu thức toán học muốn phần mềm tự tính thì phải kẹp giữa @...@.
Trong môi trường này, 'x' và 'n' đã được cấu hình sẵn là biến số.
Khi được kẹp trong @...@, nên sử dụng cú pháp Python thay vì cú pháp LaTeX.

1. Phép toán cơ bản:
   - Lũy thừa: Dùng ** (KHÔNG dùng ^). Ví dụ: a**2 (a bình phương)
   - Nhân chia: Phải có dấu * rõ ràng (Ví dụ: 2*x thay vì 2x)
   - Vô cực: "oo" (gõ hai chữ o viết thường)

1.1 Hàm số mũ & Logarit:
   - Hàm căn bậc n: sp.root(x, n) hoặc x**(1/n)
   - Logarit cơ số b: sp.log(x, b) hoặc log(x, b)
   - Logarit tự nhiên: sp.log(x) hoặc log(x)
   
2. Các hàm Lượng giác & Cơ bản:
   - sin(x), cos(x), tan(x)
   - exp(x)  (tương đương e^x)
   - abs(x)  (trị tuyệt đối)
   - log(x)  (logarit tự nhiên ln)
   - sqrt(x) (căn bậc 2)
   - pi      (số Pi)
   - oo      (Vô cực, gõ hai chữ o viết thường)

3. Tính Giới hạn (Limit):
   - Cú pháp: @lim(biểu_thức, biến, giá_trị).doit()@
   - Ví dụ:   @lim((exp(a*x)-1)/x, x, 0).doit()@

4. Tính Tích phân (Integral):
   - Cú pháp:               @sp.integrate(biểu_thức, (biến, cận_dưới, cận_trên))@
   - Tích phân bất định:    @sp.integrate(biểu_thức, biến)@
   - Ví dụ:                 @sp.integrate(x**2, (x, 0, a))@

4.1 Tích phân bội:
    - Cú pháp: @sp.integrate(biểu_thức, (x, x_min, x_max), (y, y_min, y_max))@
    - Ví dụ:   @sp.integrate(x*y, (x, 0, 1), (y, 0, 2))@

5. Tính Đạo hàm (Derivative):
   - Cú pháp:           @sp.diff(biểu_thức, biến)@
   - Bậc 2 trở lên:     @sp.diff(biểu_thức, biến, bậc)@
   - Đạo hàm hỗn hợp:   @sp.diff(biểu_thức, biến1, biến2)@
   - Ví dụ:             @sp.diff(sin(a*x), x)@

6. Tính Tổng chuỗi số (Sum):
   - Cú pháp: @sp.Sum(biểu_thức, (biến, từ, đến)).doit()@
   - Ví dụ:   @sp.Sum(a * (1/2)**n, (n, 1, oo)).doit()@

7. Rút gọn biểu thức (Simplify):
   - Cú pháp: @sp.simplify(biểu_thức)@
   - Ví dụ:   @sp.simplify(sin(x)**2 + cos(x)**2)@

8. Khai triển Taylor/Maclaurin:
   - Cú pháp: @sp.series(biểu_thức, biến, điểm_phát_triển, bậc).removeO()@
   - Ví dụ:   @sp.series(exp(x), x, 0, 5).removeO()@
   - Có thể xoá removeO() nếu muốn giữ lại phần dư (O(x^n))

LƯU Ý: CÁC HÀM TRÊN CHỈ LÀ MỘT PHẦN NHỎ TRONG SYMPY. ĐỂ KHÁM PHÁ THÊM, VUI LÒNG THAM KHẢO TÀI LIỆU CHÍNH THỨC: https://docs.sympy.org/latest/index.html
CÁC HÀM TRÊN KHI KHÔNG HOẠT ĐỘNG HÃY THÊM ĐẦU "sp." VÀO TRƯỚC TÊN HÀM (ví dụ: sp.exp, sp.sin) HOẶC THỬ CÁC BIẾN SỐ ĐÃ KHAI BÁO TRONG BƯỚC 1.
"""
        txt.insert("0.0", content)
        txt.configure(state="disabled")
    # --- KẾT THÚC DÁN 2 HÀM TỪ ĐIỂN ---

if __name__ == "__main__":
    # Tạo một cửa sổ ảo để chứa Frame nếu chạy file này trực tiếp
    app = ctk.CTk()
    app.title("Test Độc Lập Template Builder")
    app.geometry("1100x900")
    frame = TemplateBuilderIDE(app)
    frame.pack(fill="both", expand=True)
    app.mainloop()