import sympy as sp
import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from template_builder import TemplateBuilderIDE
import configparser
import database
import math_engine
import io
import matplotlib
import matplotlib.pyplot as plt
import fitz  # Thư viện PyMuPDF dùng để đọc và hiển thị PDF
from PIL import Image

matplotlib.use("Agg") # Chạy render ngầm, không mở popup
from tkinter import ttk  # Thêm dòng này để vẽ Bảng (Treeview)

# --- BỘ NHỚ CẤU HÌNH ---
CONFIG_FILE = "settings.ini"
config = configparser.ConfigParser()

def save_config(section, key, value):
    if not config.has_section(section): config.add_section(section)
    config.set(section, key, value)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: config.write(f)


# --- GIAO DIỆN CHÍNH ---
class HustMathApp(ctk.CTk):

    def setup_db_tab(self):
        """Tab 3: Quản lý, Lọc và Sắp xếp CSDL"""
        ctk.CTkLabel(self.tab_db, text="QUẢN TRỊ NGÂN HÀNG CÂU HỎI", font=("Arial", 20, "bold")).pack(pady=10)

        filter_frame = ctk.CTkFrame(self.tab_db)
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Căn chỉnh lại các Combobox để nhét vừa ô Chủ đề
        ctk.CTkLabel(filter_frame, text="Tuần:").pack(side="left", padx=(10, 2), pady=10)
        self.cb_filter_week = ctk.CTkComboBox(filter_frame, values=["Tất cả"] + [str(i) for i in range(1, 16)], width=70)
        self.cb_filter_week.pack(side="left", padx=2, pady=10)

        ctk.CTkLabel(filter_frame, text="Chủ đề:").pack(side="left", padx=(10, 2), pady=10)
        self.cb_filter_topic = ctk.CTkComboBox(filter_frame, values=["Tất cả"] + self.topic_list, width=180)
        self.cb_filter_topic.pack(side="left", padx=2, pady=10)

        ctk.CTkLabel(filter_frame, text="Độ khó:").pack(side="left", padx=(10, 2), pady=10)
        self.cb_filter_diff = ctk.CTkComboBox(filter_frame, values=["Tất cả", "1 - Dễ", "2 - TB", "3 - Khó"], width=90)
        self.cb_filter_diff.pack(side="left", padx=2, pady=10)

        ctk.CTkLabel(filter_frame, text="Sắp xếp:").pack(side="left", padx=(10, 2), pady=10)
        self.cb_sort = ctk.CTkComboBox(filter_frame, values=["Mới nhất", "Cũ nhất", "Tuần (Tăng dần)", "Độ khó (Tăng dần)"], width=130)
        self.cb_sort.pack(side="left", padx=2, pady=10)

        ctk.CTkButton(filter_frame, text="Áp dụng", fg_color="#F39C12", hover_color="#D68910", width=70, command=self.load_db_data).pack(side="right", padx=10, pady=10)

        table_frame = ctk.CTkFrame(self.tab_db)
        table_frame.pack(fill="both", expand=True, padx=20, pady=5)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=30, fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 11, 'bold'))

        # Thêm cột Loại câu hỏi (q_type)
        columns = ("id", "week", "topic", "diff", "q_type", "func")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Thêm thuộc tính selectmode="extended" để cho phép chọn nhiều dòng bằng cách quét chuột hoặc giữ Ctrl/Shift
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15, selectmode="extended")

        self.tree.heading("id", text="ID")
        self.tree.heading("week", text="Tuần")
        self.tree.heading("topic", text="Chủ đề")
        self.tree.heading("diff", text="Độ khó")
        self.tree.heading("q_type", text="Loại câu hỏi")
        self.tree.heading("func", text="Trích dẫn Đề bài (Preview)") # Đổi tên hiển thị
        
        
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("week", width=50, anchor="center")
        self.tree.column("topic", width=70, anchor="center")
        self.tree.column("diff", width=80, anchor="center")
        self.tree.column("q_type", width=130, anchor="center") # Kích thước cột mới
        self.tree.column("func", width=300, anchor="w")
        
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ctk.CTkFrame(self.tab_db, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Làm mới bảng", command=self.load_db_data).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Xóa câu đã chọn (Kéo/Ctrl)", fg_color="#E74C3C", hover_color="#C0392B", command=self.delete_selected).pack(side="right", padx=10)        
        ctk.CTkButton(btn_frame, text="Chỉnh sửa câu đã chọn", fg_color="#3498DB", hover_color="#2980B9", command=self.edit_selected).pack(side="right", padx=10)

        self.after(500, self.load_db_data)

    def load_db_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            week_val = self.cb_filter_week.get()
            topic_val = self.cb_filter_topic.get() # LẤY GIÁ TRỊ CHỦ ĐỀ
            diff_val = self.cb_filter_diff.get()
            sort_val = self.cb_sort.get()
            
            # TRUYỀN THÊM BIẾN TOPIC VÀO
            rows = database.get_filtered_exercises(week=week_val, topic=topic_val, diff=diff_val, sort_by=sort_val)

            if not rows: return
            diff_map = {1: "Dễ", 2: "Trung bình", 3: "Khó"}

            import json, re
            for r in rows:
                # Do đã sửa database.py, r bây giờ có 7 phần tử:
                row_id, week, topic, diff, q_type, f_text, latex_template = r
                
                # --- TẠO PREVIEW TỪ JSON VÀ LATEX ---
                preview_text = latex_template
                try:
                    var_data = json.loads(f_text)
                    params = {}
                    for v in var_data: # Thay thử giá trị đầu tiên vào
                        if v["type"] == "range": params[v["name"]] = str(v["range"][0])
                        elif v["type"] == "list": params[v["name"]] = str(v["set"][0])
                    
                    def eval_preview(match):
                        code = match.group(1).strip()
                        for k, v in params.items():
                            code = re.sub(rf'\b{k}\b', v, code)
                        return code # Chỉ thay chữ, không eval tính toán
                        
                    preview_text = re.sub(r'@(.*?)@', eval_preview, latex_template)
                    preview_text = preview_text.replace("\n", " ") # Xóa xuống dòng
                    if len(preview_text) > 80: preview_text = preview_text[:80] + "..."
                except:
                    preview_text = latex_template[:80] + "..." if len(latex_template)>80 else latex_template
                # ------------------------------------

                topic_str = f"CĐ {topic}"
                diff_str = diff_map.get(diff, str(diff))
                self.tree.insert("", "end", values=(row_id, week, topic_str, diff_str, q_type, preview_text))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi hiển thị dữ liệu: {e}")    
    def delete_selected(self):
        """Xóa câu hỏi đang được chọn trong bảng"""
        selected_item = self.tree.selection()
        if not selected_item:
            return messagebox.showwarning("Cảnh báo", "Hãy click chọn một câu hỏi trong bảng để xóa!")
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa câu hỏi này khỏi CSDL?"):
            for item in selected_item:
                # Lấy ID (nằm ở cột đầu tiên, index 0)
                ex_id = self.tree.item(item, "values")[0]
                database.delete_exercise(ex_id)
                self.tree.delete(item)
            messagebox.showinfo("Thành công", "Đã xóa câu hỏi khỏi ngân hàng!")

    def edit_selected(self):
        """Mở cửa sổ Template Builder để chỉnh sửa câu hỏi"""
        selected_item = self.tree.selection()
        if not selected_item: return messagebox.showwarning("Cảnh báo", "Hãy click chọn một câu hỏi!")
        if len(selected_item) > 1: return messagebox.showwarning("Cảnh báo", "Chỉ có thể chỉnh sửa 1 câu cùng lúc!")

        ex_id = self.tree.item(selected_item[0], "values")[0]
        
        import sqlite3
        import database
        try:
            conn = sqlite3.connect(database.DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT week_id, topic_id, difficulty, latex_template, question_type, options_template, solution_logic, function_text, bad_seeds FROM Exercises WHERE id = ?', (ex_id,))
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            return messagebox.showerror("Lỗi CSDL", f"Không thể lấy dữ liệu: {e}")

        if not row: return messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu!")

        # Tạo Cửa sổ độc lập
        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"Chỉnh sửa Câu hỏi ID: {ex_id}")
        edit_win.geometry("950x850")
        #edit_win.attributes('-topmost', True)
        
        # Gọi module Builder nhét vào cửa sổ này
        builder_ui = TemplateBuilderIDE(edit_win)
        builder_ui.pack(fill="both", expand=True)
        
        # Bật chế độ Edit và truyền dữ liệu
        builder_ui.set_edit_mode(ex_id=ex_id, parent_app=self, toplevel_window=edit_win)
        builder_ui.load_data(row)
    def __init__(self):
        super().__init__()
        import database
        database.init_db()
        self.title("HUST Math Exam Generator")
        self.geometry("850x850") 
        ctk.set_appearance_mode("system")

        # Load Paths
        config.read(CONFIG_FILE, encoding='utf-8')
        self.path_de = ctk.StringVar(value=config.get('Paths', 'de', fallback=os.getcwd()))
        self.path_da = ctk.StringVar(value=config.get('Paths', 'da', fallback=os.getcwd()))
        
        # --- CHÈN DANH SÁCH CHỦ ĐỀ VÀO ĐÂY ---
        self.topic_list = [
            "1 - Đại cương về chuỗi số", "2 - Chuỗi số dương", "3 - Chuỗi số có số hạng có dấu bất kỳ",
            "4 - Chuỗi luỹ thừa", "5 - Chuỗi Fourier", "6 - PTVP cấp một",
            "7 - PTVP cấp hai (đến hết PTVPTT thuần nhất)", "8 - PTVPTT cấp 2 không thuần nhất và Hệ PTVP cấp 1",
            "9 - Biến đổi Laplace, BĐ Laplace của đạo hàm và tích phân", "10 - Phép tịnh tiến, đạo hàm và tích phân của phép BĐ"
        ]
        # Tạo Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_gen = self.tabview.add("Tạo Đề Thi")
        self.tab_edit = self.tabview.add("Nhập câu hỏi")
        self.tab_db = self.tabview.add("Ngân hàng câu hỏi")

        self.setup_generator_tab()
        self.setup_editor_tab()
        self.setup_db_tab()

        if os.path.exists("logo.ico"):
            self.after(200, lambda: self.iconbitmap("logo.ico"))

    def setup_generator_tab(self):
        """Tab 1: Sinh đề thi đa năng (Có chọn Độ khó)"""
        ctk.CTkLabel(self.tab_gen, text="TẠO ĐỀ THI TỪ NGÂN HÀNG", font=("Arial", 22, "bold")).pack(pady=10)

        cfg_frame = ctk.CTkFrame(self.tab_gen)
        cfg_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Radio chọn Chế độ
        mode_frame = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(mode_frame, text="Chế độ:").pack(side="left", padx=10)
        self.gen_mode_var = ctk.StringVar(value="topic")
        ctk.CTkRadioButton(mode_frame, text="Theo Chủ đề", variable=self.gen_mode_var, value="topic", command=self.update_gen_options).pack(side="left", padx=5)
        ctk.CTkRadioButton(mode_frame, text="Theo Tuần", variable=self.gen_mode_var, value="week", command=self.update_gen_options).pack(side="left", padx=5)
        ctk.CTkRadioButton(mode_frame, text="Soạn Thủ Công", variable=self.gen_mode_var, value="manual", command=self.update_gen_options).pack(side="left", padx=(5, 20))

        # Thêm ô chọn Độ khó (dùng chung cho auto)
        self.lbl_auto_diff = ctk.CTkLabel(mode_frame, text="Độ khó:")
        self.lbl_auto_diff.pack(side="left", padx=5)
        self.cb_gen_diff = ctk.CTkComboBox(mode_frame, values=["Tất cả", "1 - Dễ", "2 - Trung bình", "3 - Khó"], width=120)
        self.cb_gen_diff.pack(side="left", padx=5)

        # --- KHUNG CHO CHẾ ĐỘ TỰ ĐỘNG ---
        self.auto_frame = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        
        chk_top_frame = ctk.CTkFrame(self.auto_frame, fg_color="transparent")
        chk_top_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(chk_top_frame, text="Chọn nội dung:").pack(side="left")
        ctk.CTkButton(chk_top_frame, text="Bỏ chọn tất cả", width=90, height=24, fg_color="#7F8C8D", command=self.deselect_all_gen).pack(side="right", padx=5)
        ctk.CTkButton(chk_top_frame, text="Chọn tất cả", width=80, height=24, fg_color="#27AE60", command=self.select_all_gen).pack(side="right", padx=5)

        self.gen_scroll = ctk.CTkScrollableFrame(self.auto_frame, height=180)
        self.gen_scroll.pack(fill="x", padx=10, pady=5)
        self.gen_checkboxes = {} 

        # --- KHUNG CHO CHẾ ĐỘ THỦ CÔNG ---
        self.manual_frame = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        
        btn_manual_top = ctk.CTkFrame(self.manual_frame, fg_color="transparent")
        btn_manual_top.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkButton(btn_manual_top, text="+ Viết câu hỏi mới", fg_color="#8E44AD", command=self.manual_create_new).pack(side="left", padx=5)
        ctk.CTkButton(btn_manual_top, text="+ Chọn đích danh từ CSDL", fg_color="#2980B9", command=self.manual_pick_specific).pack(side="left", padx=5)
        ctk.CTkButton(btn_manual_top, text="+ Bốc ngẫu nhiên 1 câu", fg_color="#16A085", command=self.manual_pick_random).pack(side="left", padx=5)
        ctk.CTkButton(btn_manual_top, text="Xóa sạch", fg_color="#C0392B", command=self.manual_clear_all).pack(side="right", padx=5)

        self.manual_scroll = ctk.CTkScrollableFrame(self.manual_frame, height=250)
        self.manual_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        self.manual_chosen_ids = [] # Danh sách ID câu hỏi thủ công


        # 3. Khung số lượng, Mã đề và SEED
        num_frame = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        num_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(num_frame, text="Số câu:").pack(side="left", padx=(10, 5))
        self.ent_num = ctk.CTkEntry(num_frame, width=50)
        self.ent_num.insert(0, "5")
        self.ent_num.pack(side="left")
        
        ctk.CTkLabel(num_frame, text="Mã đề:").pack(side="left", padx=(15, 5))
        self.ent_code = ctk.CTkEntry(num_frame, width=50)
        self.ent_code.insert(0, "101")
        self.ent_code.pack(side="left")

        import random
        ctk.CTkLabel(num_frame, text="Seed (1-100):").pack(side="left", padx=(15, 5))
        self.ent_seed = ctk.CTkEntry(num_frame, width=50)
        self.ent_seed.insert(0, str(random.randint(1, 100)))
        self.ent_seed.pack(side="left")

        # 4. Khung chọn đường dẫn
        self.p_frame = ctk.CTkFrame(self.tab_gen)
        self.p_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self.p_frame, text="Chọn nơi lưu ĐỀ", command=lambda: self.set_path('de')).grid(row=0, column=0, pady=10, padx=10)
        ctk.CTkLabel(self.p_frame, textvariable=self.path_de, font=("Arial", 10)).grid(row=0, column=1)

        # 5. Khung chức năng Xuất PDF
        action_frame = ctk.CTkFrame(self.tab_gen, fg_color="transparent")
        action_frame.pack(pady=20)

        # Checkboxes chọn mở file và xuất tex
        chk_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        chk_frame.pack(side="left", padx=(0, 20))
        
        self.chk_open_de_var = ctk.BooleanVar(value=True) 
        self.chk_open_da_var = ctk.BooleanVar(value=False)
        self.chk_keep_tex_var = ctk.BooleanVar(value=True) # Mặc định xuất kèm file TEX
        
        ctk.CTkCheckBox(chk_frame, text="Mở Đề bài sau khi xuất", variable=self.chk_open_de_var).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(chk_frame, text="Mở Đáp án sau khi xuất", variable=self.chk_open_da_var).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(chk_frame, text="Xuất kèm file mã nguồn (.tex)", variable=self.chk_keep_tex_var).pack(anchor="w", pady=2)

        # Nút xuất PDF duy nhất
        ctk.CTkButton(action_frame, text="📥 XUẤT ĐỀ THI", height=50, font=("Arial", 16, "bold"), fg_color="#2980B9", hover_color="#1F618D", command=self.run_generate).pack(side="left")

        self.update_gen_options()

    def select_all_gen(self):
        """Tích chọn tất cả các ô trong danh sách hiện tại"""
        for var in self.gen_checkboxes.values():
            var.set(True)

    def deselect_all_gen(self):
        """Bỏ chọn tất cả các ô trong danh sách hiện tại"""
        for var in self.gen_checkboxes.values():
            var.set(False)

    def update_gen_options(self):
        mode = self.gen_mode_var.get()
        
        if mode == "manual":
            self.auto_frame.pack_forget()
            self.lbl_auto_diff.pack_forget()
            self.cb_gen_diff.pack_forget()
            self.ent_num.configure(state="disabled") # Khóa ô nhập số lượng
            self.manual_frame.pack(fill="both", expand=True, pady=5)
            self.render_manual_list()
        else:
            self.manual_frame.pack_forget()
            self.lbl_auto_diff.pack(side="left", padx=5)
            self.cb_gen_diff.pack(side="left", padx=5)
            self.ent_num.configure(state="normal")
            self.auto_frame.pack(fill="both", expand=True, pady=5)
            
            for widget in self.gen_scroll.winfo_children(): widget.destroy()
            self.gen_checkboxes.clear()
            items = self.topic_list if mode == "topic" else [f"Tuần {i}" for i in range(1, 16)]
            for i, item_text in enumerate(items):
                var = ctk.BooleanVar(value=False)
                chk = ctk.CTkCheckBox(self.gen_scroll, text=item_text, variable=var)
                chk.grid(row=i//2, column=i%2, padx=10, pady=5, sticky="w")
                self.gen_checkboxes[item_text] = var

    def get_preview_text(self, f_text, latex_template):
        """Hàm dùng chung để dịch JSON thành chữ dễ đọc cho Preview"""
        import json, re
        preview_text = latex_template
        try:
            var_data = json.loads(f_text)
            params = {}
            for v in var_data:
                if v["type"] == "range": params[v["name"]] = str(v["range"][0])
                elif v["type"] == "list": params[v["name"]] = str(v["set"][0])
            def eval_preview(match):
                code = match.group(1).strip()
                for k, v in params.items(): code = re.sub(rf'\b{k}\b', v, code)
                return code
            preview_text = re.sub(r'@(.*?)@', eval_preview, latex_template).replace("\n", " ")
        except: pass
        if len(preview_text) > 85: preview_text = preview_text[:85] + "..."
        return preview_text
    
    # ================= CÁC HÀM XỬ LÝ CHẾ ĐỘ THỦ CÔNG =================
    def render_manual_list(self):
        for w in self.manual_scroll.winfo_children(): w.destroy()
        if not self.manual_chosen_ids:
            ctk.CTkLabel(self.manual_scroll, text="Chưa có câu hỏi nào. Hãy thêm câu hỏi!").pack(pady=20)
            self.ent_num.configure(state="normal"); self.ent_num.delete(0, "end"); self.ent_num.insert(0, "0"); self.ent_num.configure(state="disabled")
            return
            
        import database
        for i, q_id in enumerate(self.manual_chosen_ids):
            q_data = database.get_exercise_by_id_full(q_id)
            if not q_data: continue
            _, f_text, _, latex_template, q_type, opts, _, _ = q_data
            
            frame = ctk.CTkFrame(self.manual_scroll, fg_color="#2B2B2B", corner_radius=8)
            frame.pack(fill="x", pady=5, padx=5, ipadx=5, ipady=5)
            
            lbl_top = ctk.CTkFrame(frame, fg_color="transparent")
            lbl_top.pack(fill="x")
            ctk.CTkLabel(lbl_top, text=f"Câu {i+1} (ID: {q_id})", font=("Arial", 14, "bold"), text_color="#F39C12").pack(side="left")
            ctk.CTkLabel(lbl_top, text=f" [{q_type}]", text_color="#BDC3C7").pack(side="left")
            
            preview = self.get_preview_text(f_text, latex_template)
            ctk.CTkLabel(frame, text=preview, anchor="w", justify="left").pack(fill="x", pady=(5, 0))
            
            btn_box = ctk.CTkFrame(frame, fg_color="transparent")
            btn_box.pack(fill="x", pady=(5, 0))
            
            # Hàm nặc danh cần bind cẩn thận id
            ctk.CTkButton(btn_box, text="Xóa", width=60, fg_color="#C0392B", command=lambda idx=q_id: self.manual_remove_item(idx)).pack(side="right", padx=2)
            ctk.CTkButton(btn_box, text="Sửa", width=60, fg_color="#2980B9", command=lambda idx=q_id: self.manual_edit_item(idx)).pack(side="right", padx=2)
            
        self.ent_num.configure(state="normal"); self.ent_num.delete(0, "end"); self.ent_num.insert(0, str(len(self.manual_chosen_ids))); self.ent_num.configure(state="disabled")


    # ================= CÁC HÀM XỬ LÝ CHẾ ĐỘ THỦ CÔNG MỚI =================
    def manual_get_db_questions(self, week="Tất cả", topic="Tất cả", diff="Tất cả", sort_by="Mới nhất"):
        """Hàm truy vấn CSDL cực mạnh, tự loại bỏ các câu đã được chọn vào đề"""
        import sqlite3, database
        conn = sqlite3.connect(database.DB_FILE)
        cur = conn.cursor()
        query = "SELECT id, function_text, has_parameter, latex_template, question_type, options_template, solution_logic, bad_seeds, week_id, topic_id, difficulty FROM Exercises WHERE 1=1"
        params = []
        
        # Lọc bỏ những câu đã có trong danh sách thủ công
        db_ids = [item[0] for item in getattr(self, "manual_chosen_items", []) if isinstance(item[0], int)]
        if db_ids:
            query += f" AND id NOT IN ({','.join(['?']*len(db_ids))})"
            params.extend(db_ids)
            
        if week != "Tất cả":
            query += " AND week_id = ?"
            params.append(int(week))
        if topic != "Tất cả":
            query += " AND topic_id = ?"
            params.append(int(topic.split(" - ")[0]))
        if diff != "Tất cả":
            query += " AND difficulty = ?"
            params.append(int(diff.split(" - ")[0]))
            
        # Áp dụng sắp xếp
        if sort_by == "Mới nhất": query += " ORDER BY id DESC"
        elif sort_by == "Cũ nhất": query += " ORDER BY id ASC"
        elif sort_by == "Tuần (Tăng dần)": query += " ORDER BY week_id ASC, topic_id ASC"
        elif sort_by == "Độ khó (Tăng dần)": query += " ORDER BY difficulty ASC, week_id ASC"
        else: query += " ORDER BY id DESC"
            
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    def render_manual_list(self):
        for w in self.manual_scroll.winfo_children(): w.destroy()
        if not getattr(self, "manual_chosen_items", []):
            ctk.CTkLabel(self.manual_scroll, text="Chưa có câu hỏi nào. Hãy thêm câu hỏi!").pack(pady=20)
            self.ent_num.configure(state="normal"); self.ent_num.delete(0, "end"); self.ent_num.insert(0, "0"); self.ent_num.configure(state="disabled")
            return
            
        for i, q_data in enumerate(self.manual_chosen_items):
            q_id, f_text, has_param, latex_template, q_type, opts, logic, bad_seeds, week, topic, diff = q_data
            
            frame = ctk.CTkFrame(self.manual_scroll, fg_color="#2B2B2B", corner_radius=8)
            frame.pack(fill="x", pady=5, padx=5, ipadx=5, ipady=5)
            
            lbl_top = ctk.CTkFrame(frame, fg_color="transparent"); lbl_top.pack(fill="x")
            
            # Phân biệt Câu hỏi từ CSDL và Câu hỏi viết tạm
            id_text = f"ID: {q_id}" if isinstance(q_id, int) else "Câu hỏi Tạm"
            ctk.CTkLabel(lbl_top, text=f"Câu {i+1} ({id_text})", font=("Arial", 14, "bold"), text_color="#F39C12").pack(side="left")
            ctk.CTkLabel(lbl_top, text=f" [{q_type}]", text_color="#BDC3C7").pack(side="left")
            
            preview = self.get_preview_text(f_text, latex_template)
            ctk.CTkLabel(frame, text=preview, anchor="w", justify="left").pack(fill="x", pady=(5, 0))
            
            btn_box = ctk.CTkFrame(frame, fg_color="transparent"); btn_box.pack(fill="x", pady=(5, 0))
            ctk.CTkButton(btn_box, text="Xóa", width=60, fg_color="#C0392B", command=lambda idx=i: self.manual_remove_item(idx)).pack(side="right", padx=2)
            ctk.CTkButton(btn_box, text="Sửa", width=60, fg_color="#2980B9", command=lambda idx=i: self.manual_edit_item(idx)).pack(side="right", padx=2)
            
        self.ent_num.configure(state="normal"); self.ent_num.delete(0, "end"); self.ent_num.insert(0, str(len(self.manual_chosen_items))); self.ent_num.configure(state="disabled")

    def manual_remove_item(self, idx):
        self.manual_chosen_items.pop(idx)
        self.render_manual_list()

    def manual_clear_all(self):
        self.manual_chosen_items.clear()
        self.render_manual_list()

    def manual_create_new(self):
        if not hasattr(self, "manual_chosen_items"): self.manual_chosen_items = []
        add_win = ctk.CTkToplevel(self)
        add_win.title("Soạn câu hỏi mới (Tạm thời)")
        add_win.geometry("950x850")
        
        from template_builder import TemplateBuilderIDE
        builder = TemplateBuilderIDE(add_win)
        builder.pack(fill="both", expand=True)
        
        def on_temp_save(new_11_tuple):
            self.manual_chosen_items.append(new_11_tuple)
            self.render_manual_list()
            
        builder.set_temp_mode(on_temp_save, add_win)

    def manual_edit_item(self, idx):
        q_data = self.manual_chosen_items[idx]
        q_id = q_data[0]
        
        edit_win = ctk.CTkToplevel(self)
        edit_win.title(f"Sửa câu hỏi: {q_id}")
        edit_win.geometry("950x850")
        
        from template_builder import TemplateBuilderIDE
        builder = TemplateBuilderIDE(edit_win)
        builder.pack(fill="both", expand=True)
        
        # Đóng gói 9 tham số cũ cho hàm load_data
        load_tuple = (q_data[8], q_data[9], q_data[10], q_data[3], q_data[4], q_data[5], q_data[6], q_data[1], q_data[7])
        builder.load_data(load_tuple)
        builder.edit_id = q_id
        
        if isinstance(q_id, str) and q_id.startswith("Temp"):
            # Nếu là câu hỏi Tạm, ấn Lưu sẽ ghi đè vào RAM
            def update_temp(new_11_tuple):
                self.manual_chosen_items[idx] = new_11_tuple
                self.render_manual_list()
            builder.set_temp_mode(update_temp, edit_win)
        else:
            # Nếu là câu hỏi CSDL, ấn Lưu sẽ ghi vào DB, sau đó ta nạp lại bản mới nhất từ DB
            builder.set_edit_mode(ex_id=q_id, parent_app=self, toplevel_window=edit_win)
            def on_close():
                import sqlite3, database
                conn = sqlite3.connect(database.DB_FILE); cur = conn.cursor()
                cur.execute("SELECT id, function_text, has_parameter, latex_template, question_type, options_template, solution_logic, bad_seeds, week_id, topic_id, difficulty FROM Exercises WHERE id=?", (q_id,))
                updated_row = cur.fetchone(); conn.close()
                if updated_row:
                    self.manual_chosen_items[idx] = updated_row
                    self.render_manual_list()
            edit_win.bind("<Destroy>", lambda e: self.after(100, on_close) if e.widget == edit_win else None)

    def manual_pick_random(self):
        if not hasattr(self, "manual_chosen_items"): self.manual_chosen_items = []
        win = ctk.CTkToplevel(self)
        win.title("Bốc ngẫu nhiên")
        win.geometry("400x300")
        
        ctk.CTkLabel(win, text="Tuần:").pack(pady=(10, 0))
        cb_week = ctk.CTkComboBox(win, values=["Tất cả"] + [str(i) for i in range(1, 16)], width=250)
        cb_week.pack(pady=5)
        
        ctk.CTkLabel(win, text="Chủ đề:").pack(pady=(5, 0))
        cb_topic = ctk.CTkComboBox(win, values=["Tất cả"] + self.topic_list, width=250)
        cb_topic.pack(pady=5)
        
        ctk.CTkLabel(win, text="Độ khó:").pack(pady=(5, 0))
        cb_diff = ctk.CTkComboBox(win, values=["Tất cả", "1 - Dễ", "2 - Trung bình", "3 - Khó"], width=250)
        cb_diff.pack(pady=5)
        
        def do_pick():
            import random
            rows = self.manual_get_db_questions(week=cb_week.get(), topic=cb_topic.get(), diff=cb_diff.get())
            if not rows: return messagebox.showwarning("Trống", "Không còn câu hỏi nào phù hợp với bộ lọc!", parent=win)
            
            picked = random.choice(rows)
            self.manual_chosen_items.append(picked)
            self.render_manual_list()
            win.destroy()
            
        ctk.CTkButton(win, text="Bốc ngay", fg_color="#16A085", command=do_pick).pack(pady=15)

    def manual_pick_specific(self):
        if not hasattr(self, "manual_chosen_items"): self.manual_chosen_items = []
        win = ctk.CTkToplevel(self)
        win.title("Chọn đích danh từ Ngân hàng")
        win.geometry("1000x700") # Mở rộng bề ngang để chứa thanh Filter
        
        # --- 1. KHUNG BỘ LỌC (FILTER BAR) Ở TRÊN CÙNG ---
        filter_frame = ctk.CTkFrame(win)
        filter_frame.pack(side="top", fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(filter_frame, text="Tuần:").pack(side="left", padx=(10, 2), pady=10)
        cb_m_week = ctk.CTkComboBox(filter_frame, values=["Tất cả"] + [str(i) for i in range(1, 16)], width=70)
        cb_m_week.pack(side="left", padx=2, pady=10)

        ctk.CTkLabel(filter_frame, text="Chủ đề:").pack(side="left", padx=(10, 2), pady=10)
        cb_m_topic = ctk.CTkComboBox(filter_frame, values=["Tất cả"] + self.topic_list, width=180)
        cb_m_topic.pack(side="left", padx=2, pady=10)

        ctk.CTkLabel(filter_frame, text="Độ khó:").pack(side="left", padx=(10, 2), pady=10)
        cb_m_diff = ctk.CTkComboBox(filter_frame, values=["Tất cả", "1 - Dễ", "2 - TB", "3 - Khó"], width=90)
        cb_m_diff.pack(side="left", padx=2, pady=10)

        ctk.CTkLabel(filter_frame, text="Sắp xếp:").pack(side="left", padx=(10, 2), pady=10)
        cb_m_sort = ctk.CTkComboBox(filter_frame, values=["Mới nhất", "Cũ nhất", "Tuần (Tăng dần)", "Độ khó (Tăng dần)"], width=130)
        cb_m_sort.pack(side="left", padx=2, pady=10)

        # --- 2. KHUNG NÚT BẤM (NEO Ở ĐÁY) ---
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=10)
        
        # --- 3. KHUNG CHỨA BẢNG TREEVIEW ---
        table_frame = ctk.CTkFrame(win, fg_color="transparent")
        table_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        from tkinter import ttk
        columns = ("id", "week", "topic", "diff", "q_type", "func")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        tree.heading("id", text="ID"); tree.column("id", width=40, anchor="center")
        tree.heading("week", text="Tuần"); tree.column("week", width=50, anchor="center")
        tree.heading("topic", text="Chủ đề"); tree.column("topic", width=70, anchor="center")
        tree.heading("diff", text="Độ khó"); tree.column("diff", width=80, anchor="center")
        tree.heading("q_type", text="Loại"); tree.column("q_type", width=120, anchor="center")
        tree.heading("func", text="Đề bài"); tree.column("func", width=400, anchor="w")
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # --- HÀM LOAD DỮ LIỆU ĐỘNG ---
        current_rows = []
        def refresh_table():
            nonlocal current_rows
            for row in tree.get_children():
                tree.delete(row)
            
            w_val = cb_m_week.get()
            t_val = cb_m_topic.get()
            d_val = cb_m_diff.get()
            s_val = cb_m_sort.get()
            
            current_rows = self.manual_get_db_questions(week=w_val, topic=t_val, diff=d_val, sort_by=s_val)
            diff_map = {1: "Dễ", 2: "TB", 3: "Khó"}
            for r in current_rows:
                q_id, f_text, has_param, latex_t, q_type, opts, logic, bad_seeds, week, topic, diff = r
                preview = self.get_preview_text(f_text, latex_t)
                tree.insert("", "end", values=(q_id, week, f"CĐ {topic}", diff_map.get(diff, str(diff)), q_type, preview))
        
        # Gắn hàm Refresh vào nút Áp dụng trên thanh Filter
        ctk.CTkButton(filter_frame, text="Áp dụng", fg_color="#F39C12", hover_color="#D68910", width=70, command=refresh_table).pack(side="right", padx=10, pady=10)
        
        # Load lần đầu tiên
        refresh_table()
            
        # --- HÀM THÊM CÂU VÀO ĐỀ ---
        def do_add():
            sel = tree.selection()
            if not sel: return
            for item in sel:
                q_id = int(tree.item(item, "values")[0])
                for r in current_rows:
                    if r[0] == q_id:
                        self.manual_chosen_items.append(r)
                        break
            self.render_manual_list()
            win.destroy()
            
        ctk.CTkButton(btn_frame, text="Thêm các câu đã chọn", font=("Arial", 14, "bold"), height=40, fg_color="#2980B9", command=do_add).pack()
    def run_generate(self):
        try:
            mode = self.gen_mode_var.get()
            import database, random
            
            questions = []
            
            # BƯỚC 1: LẤY SEED
            try:
                seed_val = int(self.ent_seed.get())
                random.seed(seed_val)
            except:
                from tkinter import messagebox
                return messagebox.showerror("Lỗi", "Seed phải là số nguyên từ 1 đến 100!")
            
            # KIỂM TRA CHẾ ĐỘ THỦ CÔNG/TỰ ĐỘNG
            if mode == "manual":
                if not getattr(self, "manual_chosen_items", []):
                    from tkinter import messagebox
                    return messagebox.showwarning("Cảnh báo", "Bạn chưa chọn câu hỏi nào vào đề!")
                questions = [item[:8] for item in self.manual_chosen_items]
                num_q = len(questions)
                ma_de = self.ent_code.get().zfill(3)
                diff_val = "Tất cả"
                selected_ids = []
            else:
                diff_val = self.cb_gen_diff.get()
                selected_items = [text for text, var in self.gen_checkboxes.items() if var.get()]
                if not selected_items:
                    from tkinter import messagebox
                    return messagebox.showwarning("Cảnh báo", "Hãy chọn ít nhất 1 Chủ đề/Tuần!")
                selected_ids = [int(item.split(" - ")[0]) if mode == "topic" else int(item.replace("Tuần ", "")) for item in selected_items]
                num_q = int(self.ent_num.get())
                ma_de = self.ent_code.get().zfill(3)
                
                all_questions = database.get_exercises_by_custom_filter(mode, selected_ids, diff_val)
                if not all_questions or len(all_questions) < num_q: 
                    from tkinter import messagebox
                    return messagebox.showerror("Lỗi", f"Ngân hàng không đủ {num_q} câu hỏi cho bộ lọc này!")
                questions = random.sample(all_questions, num_q)
            
            # KIỂM TRA BAD SEEDS
            warn_q_ids = []
            for q_data in questions:
                q_id = q_data[0]
                q_bad_seeds = q_data[7]
                if q_bad_seeds and str(seed_val) in q_bad_seeds.split(","):
                    warn_q_ids.append(str(q_id))
            
            if warn_q_ids:
                from tkinter import messagebox
                answer = messagebox.askyesno("Cảnh báo Seed trùng", f"Seed '{seed_val}' sẽ sinh ra các đáp án trắc nghiệm GIỐNG NHAU ở các câu hỏi ID: {', '.join(warn_q_ids)}.\nBạn có chắc chắn muốn tiếp tục in đề với Seed này không?")
                if not answer: 
                    random.seed()
                    return

            exam_body = ""
            key_body = ""

            # BỘ BIÊN DỊCH TOÁN HỌC
            import sympy as sp
            import re
            safe_env = {
                'x': sp.Symbol('x'), 'n': sp.Symbol('n'), 'y': sp.Symbol('y'),
                'lim': sp.limit, 'limit': sp.limit, 'exp': sp.exp, 'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
                'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan, 'pi': sp.pi, 'oo': sp.oo, 'sp': sp,
                'abs': sp.Abs, 'sqrt': sp.sqrt, 'root': sp.root, 'integrate': sp.integrate, 'diff': sp.diff,
                'Sum': sp.Sum, 'simplify': sp.simplify, 'series': sp.series, 'ln': sp.log,
                'log': lambda val, base=10: sp.log(val, base),
                'e': sp.E
            }

            def eval_template(template_str, params_dict):
                template_str = str(template_str)
                if not template_str.strip(): return ""
                def evaluate_match(match):
                    inner_code = match.group(1).strip()
                    for k, v in params_dict.items():
                        inner_code = re.sub(rf'\b{k}\b', str(v), inner_code)
                    try:
                        result = eval(inner_code, {"__builtins__": {}}, safe_env)
                        if result == sp.sin: return r"\sin "
                        if result == sp.cos: return r"\cos "
                        if result == sp.tan: return r"\tan "
                        if result == sp.exp: return r"e^"
                        if result == sp.log: return r"\ln "
                        if isinstance(result, (sp.Basic, sp.MatrixBase)):
                            if "series" in inner_code: return sp.latex(result, ln_notation=True, order='rev-lex')
                            return sp.latex(result, ln_notation=True)
                        return str(result)
                    except: return str(inner_code)
                
                res = re.sub(r'@(.*?)@', evaluate_match, template_str)
                res = res.replace("asin", r"\arcsin").replace("acos", r"\arccos")
                
                def clean_log(m):
                    A = m.group(1).replace(r'\left(', '').replace(r'\right)', '').strip()
                    B = m.group(2).replace(r'\left(', '').replace(r'\right)', '').strip()
                    if A.startswith('(') and A.endswith(')'): A = A[1:-1]
                    if B.startswith('(') and B.endswith(')'): B = B[1:-1]
                    return rf'\log_{{{B}}}\left({A}\right)'
                res = re.sub(r'\\frac\{\\ln\s*\{(.*?)\}\}\{\\ln\s*\{(.*?)\}\}', clean_log, res)
                
                # --- BẢO VỆ CẬN TÍCH PHÂN ---
                protected = []
                def protect(m):
                    protected.append(m.group(0))
                    return f"__PROT{len(protected)-1}__"
                res = re.sub(r'\\(?:int|sum|prod)(?:\\limits)?_(?:\{[^}]*\}|[a-zA-Z0-9])\^(?:\{1\}|1)(?!\d)', protect, res)

                # --- 1. DỌN LỖI 1^n (Đã nâng cấp chống lỗi số thập phân .1) ---
                res = re.sub(r'(?<![\d.])1\^\{[^\}]+\}', '1', res)
                res = re.sub(r'(?<![\d.])1\^[a-zA-Z0-9]+', '1', res)
                res = re.sub(r'\\left\(1\\right\)\^\{[^\}]+\}', '1', res)
                res = re.sub(r'\\left\(1\\right\)\^[a-zA-Z0-9]+', '1', res)

                # --- 1.5. TỐI GIẢN PHÉP NHÂN TƯỜNG MINH VỚI 1 (\cdot 1 hoặc 1 \cdot) ---
                res = re.sub(r'(?<![\d.])1\s*(?:\\cdot|\*)\s*', '', res) # Xóa "1 \cdot " đứng trước
                res = re.sub(r'\s*(?:\\cdot|\*)\s*1(?![\d.])', '', res)  # Xóa " \cdot 1" đứng sau

                # --- 2. TỐI GIẢN TÍCH 1x (Nhân ẩn) ---
                res = re.sub(r'(^|[-+=({\[<>/,\s]+)1\s*(?:\\cdot\s*|\*\s*)?(?!\\(?:times|cdot|div|pm|mp|ge|le|neq|approx|right|limits|quad|qquad)\b)([a-zA-Z]|\\[a-zA-Z]+)', r'\1\2', res)
                
                # --- 3. TỐI GIẢN PHÂN SỐ CHIA 1 ---
                res = re.sub(r'\\frac\{((?:[^{}]|\{[^{}]*\})*)\}\{1\}', r'\1', res)
                res = res.replace(r"\frac{1}{1}", "1").replace("1/1", "1")
                
                # --- 4. XÓA MŨ 1 (Kể cả ln(x)^1) ---
                res = re.sub(r'\^\{1\}', '', res)
                res = re.sub(r'\^1(?!\d)', '', res)

                # --- TRẢ LẠI CẬN TÍCH PHÂN ---
                for i, p in enumerate(protected):
                    res = res.replace(f"__PROT{i}__", p)

                res = res.replace(r"\left(\left(", r"\left(").replace(r"\right)\right)", r"\right)")
                res = res.replace(r"((", r"(").replace(r"))", r")")

                # --- XÓA ĐUÔI .0 (VD: 30.0 -> 30, 5.0x -> 5x) ---
                res = re.sub(r'\.0+(?!\d)', '', res)

                return res

            def auto_wrap_math(val):
                """Hàm tự động bọc công thức bằng $ và tự động phóng to phân số"""
                val_str = str(val).strip()
                if not val_str: return val_str
                
                # 1. NẾU LÀ VĂN BẢN (có tiếng Việt hoặc từ tiếng Anh liền nhau) -> Không can thiệp
                if re.search(r'[áàãạảăắằẵặẳâấầẫậẩéèẽẹẻêếềễệểíìĩịỉóòõọỏôốồỗộổơớờỡợởúùũụủưứừữựửýỳỹỵỷđ]', val_str, re.IGNORECASE):
                    return val_str
                if re.search(r'(?<!\\)\b[a-zA-Z]{2,}\s+(?<!\\)\b[a-zA-Z]{2,}', val_str):
                    return val_str
                    
                # 2. XỬ LÝ PHÓNG TO CHO CÔNG THỨC TOÁN
                # Kiểm tra xem có chứa Phân số, Tích phân, Tổng và chưa có sẵn \displaystyle không?
                needs_display = (r'\frac' in val_str or r'\int' in val_str or r'\sum' in val_str) and (r'\displaystyle' not in val_str)
                
                if needs_display:
                    if val_str.startswith('$') and val_str.endswith('$'):
                        # Nếu bạn đã bọc $...$ -> Lột bỏ $, nhét displaystyle vào, bọc lại
                        inner_math = val_str[1:-1].strip()
                        return rf"$\displaystyle {inner_math}$"
                    elif '$' in val_str:
                        # Nếu có dấu $ lộn xộn -> Chỉ chèn displaystyle ngay sau dấu $ đầu tiên
                        return val_str.replace('$', r'$\displaystyle ', 1)
                    else:
                        # Nếu bạn chưa gõ $ -> Máy tự bọc mới
                        return rf"$\displaystyle {val_str}$"
                
                # 3. NẾU KHÔNG CẦN PHÓNG TO MÀ CHƯA CÓ $ -> TỰ BỌC $
                if '$' not in val_str:
                    return f"${val_str}$"
                    
                return val_str

            for i, q_data in enumerate(questions, 1):
                q_id, f_text, has_param, latex_template, q_type, options_json, logic, bad_seeds = q_data      
                is_new_format = f_text.strip().startswith("[") or f_text.strip().startswith("{")
                
                q_text = ""
                params = {}
                expr = None 
                
                if is_new_format:
                    import json, random
                    try:
                        var_data = json.loads(f_text)
                        for attempt in range(20):
                            params = {}
                            for v in var_data:
                                name = v["name"]
                                if v["type"] == "range":
                                    start, end, step = int(v["range"][0]), int(v["range"][1]), int(v["range"][2])
                                    params[name] = random.choice(range(start, end + 1, step))
                                elif v["type"] == "list":
                                    val = random.choice(v["set"])
                                    try:
                                        if val.strip().lstrip('-').isdigit(): val = int(val.strip())
                                    except: pass
                                    params[name] = val
                            
                            has_collision = False
                            if q_type and "Trắc nghiệm" in q_type and options_json:
                                opts_dict = json.loads(options_json)
                                
                                # 1. Check trùng cho Trắc nghiệm Thường
                                if not opts_dict.get("is_logic_pool"): 
                                    eval_vals = []
                                    for char in ['A', 'B', 'C', 'D', 'E', 'F']:
                                        if char in opts_dict and char != "correct":
                                            eval_vals.append(eval_template(str(opts_dict[char]), params))
                                    if len(set(eval_vals)) < len(eval_vals):
                                        has_collision = True
                                        
                                # 2. Check trùng cho Trắc nghiệm Logic
                                else:
                                    eval_vals = []
                                    for v in opts_dict.get("ans_pool", []):
                                        eval_vals.append(eval_template(str(v), params))
                                    if len(set(eval_vals)) < len(eval_vals):
                                        has_collision = True
                                        
                            if not has_collision:
                                break
                                
                        q_text = eval_template(latex_template, params)
                    except Exception as e:
                        q_text = rf"Lỗi đọc template mới: {e}"
                else:
                    try:
                        expr = sp.sympify(f_text)
                        if has_param:
                            import random
                            expr = expr.subs('k', random.randint(2, 7)) 
                        latex_fx = sp.latex(expr)
                        if not latex_template or latex_template.strip() == "":
                            q_text = rf"Tính: ${latex_fx}$"
                        else:
                            q_text = latex_template.replace("{f_x}", latex_fx)
                    except Exception as e:
                        q_text = rf"Lỗi đọc template cũ: {e}"

                exam_body += rf"\noindent \textbf{{Câu {i}:}} {q_text}" + "\n\n"
                ans_text = ""
                
                if q_type and "Trắc nghiệm" in q_type and options_json:
                    import json, random
                    try:
                        opts = json.loads(options_json)
                        available_chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K']
                        
                        if opts.get("is_logic_pool"):
                            # [LOẠI 1] TRẮC NGHIỆM LOGIC
                            pool = opts["ans_pool"]
                            logic_rule = opts["logic_rule"]
                            local_env = params.copy()
                            exec(logic_rule, {"__builtins__": {}}, local_env)
                            raw_correct = str(local_env.get("correct_ans", "Lỗi gán đáp án"))
                            
                            # --- BIÊN DỊCH TOÀN BỘ POOL SANG TOÁN HỌC TRƯỚC ---
                            eval_pool = [eval_template(v, params) for v in pool]
                            eval_correct = eval_template(raw_correct, params)
                            
                            # --- LỌC ĐÁP ÁN SAI DỰA TRÊN KẾT QUẢ ĐÃ BIÊN DỊCH CHUẨN ---
                            eval_wrongs = []
                            for ans in eval_pool:
                                if ans != eval_correct and ans not in eval_wrongs:
                                    eval_wrongs.append(ans)
                                    
                            random.shuffle(eval_wrongs)
                            selected_wrongs = eval_wrongs[:3] 
                            
                            final_choices = [eval_correct] + selected_wrongs
                            random.shuffle(final_choices)
                            
                            correct_char = available_chars[final_choices.index(eval_correct)]
                            
                            # Bọc Math và tự động thêm \displaystyle
                            final_choices = [auto_wrap_math(v) for v in final_choices]
                            
                            # --- CHIA CỘT BẰNG MINIPAGE ---
                            cols = opts.get("cols", 1) 
                            exam_body += "\n\\vspace{10pt}\n\n"
                            
                            if cols == 4:
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} A. {final_choices[0]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} B. {final_choices[1]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} C. {final_choices[2]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} D. {final_choices[3]} \end{{minipage}}" + "\n\n\\vspace{10pt}\n\n"
                            elif cols == 2:
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} A. {final_choices[0]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} B. {final_choices[1]} \end{{minipage}}" + "\n\n\\vspace{10pt}\n\n"
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} C. {final_choices[2]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} D. {final_choices[3]} \end{{minipage}}" + "\n\n\\vspace{10pt}\n\n"
                            else:
                                exam_body += r"\begin{itemize}" + "\n"
                                for idx, val in enumerate(final_choices):
                                    char = available_chars[idx]
                                    exam_body += rf"\item[{char}.] {val}" + "\n"
                                exam_body += r"\end{itemize}" + "\n\\vspace{10pt}\n\n"
                            
                            ans_text = rf"\textbf{{Đáp án: {correct_char}}}"
                            
                        else:
                            valid_chars = [c for c in available_chars if c in opts]
                            original_correct_str = opts.get("correct", "").replace(" ", "")
                            correct_keys = original_correct_str.split(",")
                            
                            raw_values = []
                            for k in valid_chars:
                                val = opts[k]
                                if is_new_format: val = eval_template(val, params)
                                raw_values.append((k, val))
                                
                            correct_values = [v for k, v in raw_values if k in correct_keys]
                            random.shuffle(raw_values)
                            final_vals = [v for k, v in raw_values]
                            
                            final_vals = [auto_wrap_math(v) for v in final_vals]
                            
                            # --- CHIA CỘT BẰNG MINIPAGE (CĂN HÀNG THẲNG TẮP) ---
                            cols = opts.get("cols", 1) 
                            exam_body += "\n\\vspace{10pt}\n\n"
                            
                            if cols == 4:
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} A. {final_vals[0]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} B. {final_vals[1]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} C. {final_vals[2]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.24\textwidth}} D. {final_vals[3]} \end{{minipage}}" + "\n\n\\vspace{10pt}\n\n"
                            elif cols == 2:
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} A. {final_vals[0]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} B. {final_vals[1]} \end{{minipage}}" + "\n\n\\vspace{10pt}\n\n"
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} C. {final_vals[2]} \end{{minipage}}\hfill"
                                exam_body += rf"\begin{{minipage}}{{0.48\textwidth}} D. {final_vals[3]} \end{{minipage}}" + "\n\n\\vspace{10pt}\n\n"
                            else:
                                exam_body += r"\begin{itemize}" + "\n"
                                for idx, val in enumerate(final_vals):
                                    char = available_chars[idx]
                                    exam_body += rf"\item[{char}.] {val}" + "\n"
                                exam_body += r"\end{itemize}" + "\n\\vspace{10pt}\n\n"
                            
                            new_correct_keys = []
                            for idx, (old_k, val) in enumerate(raw_values):
                                char = available_chars[idx]
                                if val in correct_values: new_correct_keys.append(char)
                            
                            new_correct_str = ", ".join(sorted(new_correct_keys))
                            ans_text = rf"\textbf{{Đáp án: {new_correct_str}}}"
                            
                    except Exception as e: 
                        ans_text = rf"Lỗi xử lý đáp án: {e}"
                        
                else:
                    exam_body += "\n\\vspace{40pt}\n\n"
                    if logic and logic.strip() and logic != "Để trống nếu muốn SymPy tự giải...":
                        ans_text = eval_template(logic, params) if is_new_format else logic
                    else:
                        if is_new_format:
                            ans_text = "Câu hỏi tự luận (GV tự chấm)."
                        else:
                            try:
                                n = sp.symbols('n') 
                                lim = sp.limit(expr, n, sp.oo)
                                ans_text = rf"Giới hạn $\lim_{{n \to \infty}} u_n = {sp.latex(lim)}$"
                                if lim != 0: ans_text += r" $\neq 0 \Rightarrow$ \textbf{Chuỗi Phân kỳ}."
                                else:
                                    series_sum = sp.Sum(expr, (n, 1, sp.oo))
                                    is_conv = series_sum.is_convergent()
                                    if is_conv is True: ans_text += r" $\Rightarrow$ \textbf{Chuỗi Hội tụ}."
                                    elif is_conv is False: ans_text += r" $\Rightarrow$ \textbf{Chuỗi Phân kỳ}."
                                    else: ans_text += r" $\Rightarrow$ (Cần dùng tiêu chuẩn xét tiếp)."
                            except:
                                ans_text = "Câu hỏi tự luận (GV tự chấm)."

                key_body += rf"\noindent \textbf{{Câu {i}:}} {ans_text}" + "\n\n\\vspace{5pt}\n\n"

            title_mode = "CHỦ ĐỀ" if mode == "topic" else "TUẦN"
            title_ids = ", ".join(map(str, selected_ids))
            diff_str = "" if diff_val == "Tất cả" else f" - ĐỘ KHÓ: {diff_val.split(' - ')[1].upper()}"
            
            title_de = f"ĐỀ ÔN TẬP: {title_mode} {title_ids}{diff_str}"
            title_da = f"HƯỚNG DẪN CHẤM (MÃ ĐỀ {ma_de})"
            
            path_save = self.path_de.get()
            fname_de = f"De_On_Tap_Ma_{ma_de}"
            fname_da = f"Dap_An_Ma_{ma_de}"
            
            # --- ĐỌC CẤU HÌNH XUẤT FILE TEX TỪ GIAO DIỆN ---
            keep_tex_flag = getattr(self, "chk_keep_tex_var", None) and self.chk_keep_tex_var.get()
            
            self.export_pdf(path_save, fname_de, exam_body, title_de, keep_tex_flag)
            self.export_pdf(path_save, fname_da, key_body, title_da, keep_tex_flag)
            
            pdf_de_path = os.path.join(path_save, f"{fname_de}.pdf")
            pdf_da_path = os.path.join(path_save, f"{fname_da}.pdf")
            
            if getattr(self, "chk_open_de_var", None) and self.chk_open_de_var.get() and os.path.exists(pdf_de_path):
                os.startfile(pdf_de_path)
            if getattr(self, "chk_open_da_var", None) and self.chk_open_da_var.get() and os.path.exists(pdf_da_path):
                os.startfile(pdf_da_path)
            
            from tkinter import messagebox
            msg = f"Đã xuất file {fname_de}.pdf và {fname_da}.pdf"
            if keep_tex_flag:
                msg += "\n(Đã xuất kèm 2 file mã nguồn .tex)"
            messagebox.showinfo("Xong!", msg)

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi Thuật Toán", f"Có lỗi xảy ra: {e}")
    
    def setup_editor_tab(self):
        # Triệu hồi toàn bộ giao diện từ file template_builder.py và nhúng vào tab_edit
        self.builder_ui = TemplateBuilderIDE(self.tab_edit)
        self.builder_ui.pack(fill="both", expand=True)

    def toggle_options_frame(self, choice):
        """Hiện khung Trắc nghiệm hoặc Khung Lời giải tùy theo Loại câu hỏi"""
        if "Trắc nghiệm" in choice:
            self.solution_frame.pack_forget()
            self.opts_frame.pack(fill="x")
        else:
            self.opts_frame.pack_forget()
            self.solution_frame.pack(fill="x")
    def render_latex_to_image(self, latex_str, text_color):
        fig = plt.figure(figsize=(4, 1.2), dpi=100)
        fig.patch.set_alpha(0.0) 
        fig.text(0.5, 0.5, f"${latex_str}$", size=18, ha='center', va='center', math_fontfamily='cm', color=text_color)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, transparent=True)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)

    def update_preview(self, *args):
        f_text = self.func_var.get().strip()
        if not f_text:
            self.lbl_preview.configure(image="", text="Gõ hàm số để xem trước...")
            return

        try:
            # Đã bỏ evaluate=False để SymPy chuẩn hóa phân số gọn gàng
            expr = sp.sympify(f_text)
            latex_str = sp.latex(expr)
            
            img_black = self.render_latex_to_image(latex_str, "black")
            img_white = self.render_latex_to_image(latex_str, "white")
            
            ctk_img = ctk.CTkImage(light_image=img_black, dark_image=img_white, size=(img_black.width, img_black.height))
            self.lbl_preview.configure(image=ctk_img, text="")
        except Exception:
            self.lbl_preview.configure(image="", text="Đang gõ cú pháp...")

    def save_to_db(self):
        try:
            week = self.cb_week.get().replace("Tuần ", "")
            topic = self.cb_topic.get()
            diff = self.cb_diff.get()
            func_text = self.txt_function.get().strip() 
            has_param = 1 if self.chk_param.get() else 0
            latex_template = self.txt_latex.get("0.0", "end").strip()
            q_type = self.cb_qtype.get()

            # Lấy Lời giải tự luận
            solution_logic = ""
            if "Tự luận" in q_type:
                solution_text = self.txt_solution.get("0.0", "end").strip()
                if solution_text and solution_text != "Để trống nếu muốn SymPy tự giải...":
                    solution_logic = solution_text

            # Lấy Đáp án trắc nghiệm
            options_json = ""
            if "Trắc nghiệm" in q_type:
                opts = {}
                for char, ent in self.opt_entries.items():
                    val = ent.get().strip()
                    if val: 
                        opts[char] = val
                opts["correct"] = self.ent_correct.get().strip()
                import json
                options_json = json.dumps(opts, ensure_ascii=False)

            week_id = int(week)
            topic_id = int(topic.split(" - ")[0])
            import database 
            database.add_exercise(week_id, topic_id, diff, func_text, has_param, latex_template, q_type, options_json, solution_logic)
            
            from tkinter import messagebox
            messagebox.showinfo("Thành công", "Đã lưu câu hỏi vào CSDL!")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi Lưu CSDL", f"Có lỗi xảy ra: {e}")

    def auto_generate_function(self):
        """Gọi Engine Toán học để sinh hàm tự động dựa trên cấu hình đang chọn"""
        try:
            # Lấy thông tin hiện tại
            topic_str = self.cb_topic.get()
            topic_id = int(topic_str.split(" - ")[0])
            diff_str = self.cb_diff.get()
            difficulty = int(diff_str.split(" - ")[0])

            # Gọi Nhà máy sinh hàm
            expr, latex_str = math_engine.generate_random_function(topic_id, difficulty)

            # Xóa ô cũ, điền hàm mới dạng chuỗi vào TextBox
            self.ent_func.delete(0, 'end')
            self.ent_func.insert(0, str(expr))
            
            # Tự động gán tick "Có tham số k" nếu hàm sinh ra có chứa biến k
            if 'k' in str(expr):
                self.chk_param_var.set(True)
            else:
                self.chk_param_var.set(False)

            # Khung Preview sẽ tự động render do đã được bind sự kiện
        except Exception as e:
            messagebox.showerror("Lỗi Logic", f"Lỗi khi sinh hàm tự động: {e}")
    
    # --- HÀM XỬ LÝ ĐƯỜNG DẪN & XUẤT PDF ---
    def set_path(self, mode):
        p = filedialog.askdirectory()
        if p:
            if mode == 'de': self.path_de.set(p)
            else: self.path_da.set(p)
            save_config('Paths', mode, p)

    def export_pdf(self, folder, fname, content, title, keep_tex=False):
        prev_dir = os.getcwd()
        try:
            os.chdir(folder)
            tex_file = f"{fname}.tex"
            
            latex_template = r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[utf8]{vietnam}
\usepackage{amsmath, amssymb, geometry}
\geometry{margin=1in}

\begin{document}
\begin{center} 
    \Large \textbf{""" + title + r"""} 
\end{center}
\vspace{10pt}
""" + content + r"""
\end{document}
"""
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(latex_template)
            
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_file], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            # Quản lý dọn dẹp file rác
            exts_to_remove = [".aux", ".log"]
            if not keep_tex:
                exts_to_remove.append(".tex") # Nếu user KHÔNG chọn giữ tex, thì xóa nó đi
                
            for ext in exts_to_remove:
                temp_file = fname + ext
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
        except Exception as e:
            print(f"Lỗi tại export_pdf: {e}")
        finally:
            os.chdir(prev_dir)

if __name__ == "__main__":
    app = HustMathApp()
    app.mainloop()