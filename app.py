"""
Vietnamese Text Normalizer - Giao diện Desktop
Ứng dụng chuẩn hóa văn bản tiếng Việt với Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time

from normalizer import VietnameseNormalizer
import mysql.connector


# ============================================================
# BẢNG MÀU & STYLE
# ============================================================
COLORS = {
    'bg_dark': '#f0f2f5',
    'bg_panel': '#ffffff',
    'bg_input': '#ffffff',
    'bg_output': '#ffffff',
    'bg_code': '#f8f9fb',
    'bg_table_header': '#4361ee',
    'bg_table_row1': '#ffffff',
    'bg_table_row2': '#f0f4ff',
    'fg_primary': '#1a1a2e',
    'fg_secondary': '#5a6178',
    'fg_accent': '#4361ee',
    'fg_success': '#0fa958',
    'fg_code': '#2d3748',
    'fg_highlight': '#e94560',
    'btn_primary': '#4361ee',
    'btn_hover': '#3a56d4',
    'btn_text': '#ffffff',
    'border': '#d0d7e3',
    'gradient_start': '#4361ee',
    'gradient_end': '#e94560',
}

FONTS = {
    'title': ('Segoe UI', 18, 'bold'),
    'subtitle': ('Segoe UI', 12),
    'body': ('Segoe UI', 11),
    'code': ('Consolas', 10),
    'small': ('Segoe UI', 9),
    'stats': ('Segoe UI', 11, 'bold'),
    'button': ('Segoe UI', 13, 'bold'),
    'table_header': ('Segoe UI', 10, 'bold'),
    'table_body': ('Consolas', 10),
}


class NormalizerApp:
    """Giao diện chính của ứng dụng"""

    def __init__(self, root):
        self.root = root
        self.normalizer = None
        self.setup_window()
        self.create_widgets()
        self.connect_db()

    def setup_window(self):
        """Cấu hình cửa sổ chính"""
        self.root.title("🇻🇳 Chuẩn hóa Tiếng Việt")
        self.root.configure(bg=COLORS['bg_dark'])
        self.root.state('zoomed')  # Fullscreen trên Windows
        self.root.minsize(1100, 700)

        # Style cho Treeview
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("Custom.Treeview",
                        background=COLORS['bg_panel'],
                        foreground=COLORS['fg_primary'],
                        fieldbackground=COLORS['bg_panel'],
                        font=FONTS['table_body'],
                        rowheight=30,
                        borderwidth=0)

        style.configure("Custom.Treeview.Heading",
                        background=COLORS['bg_table_header'],
                        foreground=COLORS['fg_primary'],
                        font=FONTS['table_header'],
                        borderwidth=0,
                        relief='flat')

        style.map("Custom.Treeview.Heading",
                  background=[('active', COLORS['btn_hover'])])

        style.map("Custom.Treeview",
                  background=[('selected', COLORS['gradient_start'])],
                  foreground=[('selected', COLORS['fg_primary'])])

    def create_widgets(self):
        """Tạo giao diện"""
        # ===== HEADER =====
        header_frame = tk.Frame(self.root, bg=COLORS['bg_dark'], pady=10)
        header_frame.pack(fill='x', padx=20)

        title_label = tk.Label(header_frame,
                               text="✨ ỨNG DỤNG CHUẨN HÓA TIẾNG VIỆT ✨",
                               font=FONTS['title'],
                               fg=COLORS['fg_accent'],
                               bg=COLORS['bg_dark'])
        title_label.pack()

        subtitle_label = tk.Label(header_frame,
                                  text="Xử lý từ lặp ký tự • Giải mã từ viết tắt • Phân tích ngữ cảnh",
                                  font=FONTS['subtitle'],
                                  fg=COLORS['fg_secondary'],
                                  bg=COLORS['bg_dark'])
        subtitle_label.pack()

        # ===== MAIN CONTENT =====
        main_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        # ----- INPUT ROW -----
        input_row = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        input_row.pack(fill='x', pady=(0, 10))

        input_label = tk.Label(input_row,
                               text="📝 NHẬP ĐOẠN VĂN (dưới 50 từ):",
                               font=FONTS['body'],
                               fg=COLORS['fg_highlight'],
                               bg=COLORS['bg_dark'])
        input_label.pack(anchor='w')

        self.input_text = tk.Text(input_row,
                                  height=3,
                                  font=FONTS['body'],
                                  bg=COLORS['bg_input'],
                                  fg=COLORS['fg_primary'],
                                  insertbackground=COLORS['fg_primary'],
                                  selectbackground=COLORS['gradient_start'],
                                  relief='flat',
                                  padx=15, pady=10,
                                  wrap='word',
                                  borderwidth=2,
                                  highlightthickness=1,
                                  highlightcolor=COLORS['fg_accent'],
                                  highlightbackground=COLORS['border'])
        self.input_text.pack(fill='x', pady=(5, 0))
        self.input_text.insert('1.0', 'anhhh y em k biet dc')

        # ----- BUTTON -----
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        btn_frame.pack(fill='x', pady=10)

        self.normalize_btn = tk.Button(
            btn_frame,
            text="⚡ CHUẨN HÓA",
            font=FONTS['button'],
            bg=COLORS['btn_primary'],
            fg=COLORS['btn_text'],
            activebackground=COLORS['btn_hover'],
            activeforeground=COLORS['btn_text'],
            relief='flat',
            cursor='hand2',
            padx=30, pady=8,
            command=self.on_normalize
        )
        self.normalize_btn.pack()

        # Hiệu ứng hover
        self.normalize_btn.bind('<Enter>',
                                lambda e: self.normalize_btn.configure(bg=COLORS['btn_hover']))
        self.normalize_btn.bind('<Leave>',
                                lambda e: self.normalize_btn.configure(bg=COLORS['btn_primary']))

        # ----- RESULT ROW (2 cột: trước / sau) -----
        result_row = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        result_row.pack(fill='x', pady=(0, 10))
        result_row.columnconfigure(0, weight=1)
        result_row.columnconfigure(1, weight=1)

        # Cột trái: Trước khi chuẩn hóa
        before_frame = tk.Frame(result_row, bg=COLORS['bg_panel'],
                                highlightthickness=1,
                                highlightbackground=COLORS['border'])
        before_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))

        tk.Label(before_frame,
                 text="📄 TRƯỚC KHI CHUẨN HÓA",
                 font=FONTS['table_header'],
                 fg=COLORS['fg_accent'],
                 bg=COLORS['bg_panel'],
                 pady=5).pack(anchor='w', padx=10)

        self.before_text = tk.Text(before_frame,
                                   height=4,
                                   font=FONTS['body'],
                                   bg=COLORS['bg_panel'],
                                   fg=COLORS['fg_secondary'],
                                   relief='flat',
                                   padx=15, pady=5,
                                   wrap='word',
                                   state='disabled',
                                   borderwidth=0)
        self.before_text.pack(fill='both', expand=True)

        # Cột phải: Sau khi chuẩn hóa
        after_frame = tk.Frame(result_row, bg=COLORS['bg_panel'],
                               highlightthickness=1,
                               highlightbackground=COLORS['border'])
        after_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))

        tk.Label(after_frame,
                 text="✅ SAU KHI CHUẨN HÓA",
                 font=FONTS['table_header'],
                 fg=COLORS['fg_success'],
                 bg=COLORS['bg_panel'],
                 pady=5).pack(anchor='w', padx=10)

        self.after_text = tk.Text(after_frame,
                                  height=4,
                                  font=FONTS['body'],
                                  bg=COLORS['bg_panel'],
                                  fg=COLORS['fg_success'],
                                  relief='flat',
                                  padx=15, pady=5,
                                  wrap='word',
                                  state='disabled',
                                  borderwidth=0)
        self.after_text.pack(fill='both', expand=True)

        # ----- ANALYSIS ROW (2 cột: Code + Bảng) -----
        analysis_row = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        analysis_row.pack(fill='both', expand=True)
        analysis_row.columnconfigure(0, weight=1)
        analysis_row.columnconfigure(1, weight=1)

        # Cột trái: Code xử lý
        code_frame = tk.Frame(analysis_row, bg=COLORS['bg_code'],
                              highlightthickness=1,
                              highlightbackground=COLORS['border'])
        code_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))

        tk.Label(code_frame,
                 text="💻 CODE XỬ LÝ NGHIỆP VỤ",
                 font=FONTS['table_header'],
                 fg=COLORS['fg_code'],
                 bg=COLORS['bg_code'],
                 pady=5).pack(anchor='w', padx=10)

        self.code_text = scrolledtext.ScrolledText(
            code_frame,
            font=FONTS['code'],
            bg=COLORS['bg_code'],
            fg=COLORS['fg_code'],
            insertbackground=COLORS['fg_primary'],
            selectbackground=COLORS['gradient_start'],
            relief='flat',
            padx=10, pady=5,
            wrap='word',
            state='disabled',
            borderwidth=0
        )
        self.code_text.pack(fill='both', expand=True)

        # Cột phải: Bảng phân tích
        table_frame = tk.Frame(analysis_row, bg=COLORS['bg_panel'],
                               highlightthickness=1,
                               highlightbackground=COLORS['border'])
        table_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))

        tk.Label(table_frame,
                 text="📊 BẢNG PHÂN TÍCH TỪ",
                 font=FONTS['table_header'],
                 fg=COLORS['fg_highlight'],
                 bg=COLORS['bg_panel'],
                 pady=5).pack(anchor='w', padx=10)

        # Treeview
        columns = ('original', 'result', 'type', 'candidates', 'reason')
        self.tree = ttk.Treeview(table_frame,
                                 columns=columns,
                                 show='headings',
                                 style='Custom.Treeview')

        self.tree.heading('original', text='Từ gốc')
        self.tree.heading('result', text='Kết quả')
        self.tree.heading('type', text='Loại xử lý')
        self.tree.heading('candidates', text='Ứng viên')
        self.tree.heading('reason', text='Lý do')

        self.tree.column('original', width=80, minwidth=60)
        self.tree.column('result', width=80, minwidth=60)
        self.tree.column('type', width=100, minwidth=80)
        self.tree.column('candidates', width=120, minwidth=80)
        self.tree.column('reason', width=200, minwidth=120)

        # Scrollbar cho table
        tree_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(fill='both', expand=True, padx=5, pady=(0, 5), side='left')
        tree_scroll.pack(fill='y', side='right', pady=(0, 5))

        # Tag for alternating row colors
        self.tree.tag_configure('odd', background=COLORS['bg_table_row1'])
        self.tree.tag_configure('even', background=COLORS['bg_table_row2'])
        self.tree.tag_configure('changed', foreground=COLORS['fg_success'])

        # ===== FOOTER (STATS) =====
        footer_frame = tk.Frame(self.root, bg=COLORS['bg_panel'], pady=8)
        footer_frame.pack(fill='x', padx=20, pady=(0, 10))

        self.stats_label = tk.Label(footer_frame,
                                    text="📊 Tổng số từ: 0  |  Từ thay đổi: 0  |  ⏱ Thời gian: 0.000000s",
                                    font=FONTS['stats'],
                                    fg=COLORS['fg_secondary'],
                                    bg=COLORS['bg_panel'])
        self.stats_label.pack()

        # Connection status
        self.status_label = tk.Label(footer_frame,
                                     text="🔌 Đang kết nối MySQL...",
                                     font=FONTS['small'],
                                     fg=COLORS['fg_secondary'],
                                     bg=COLORS['bg_panel'])
        self.status_label.pack()

    def connect_db(self):
        """Kết nối database trong background thread, tự động setup nếu chưa có"""
        def _connect():
            try:
                # Kiểm tra database đã tồn tại chưa
                self.root.after(0, lambda: self.status_label.configure(
                    text="🔌 Đang kiểm tra database...",
                    fg=COLORS['fg_secondary']
                ))

                # Thử kết nối MySQL trước
                conn = mysql.connector.connect(
                    host='localhost', port=3307, user='root', password=''
                )
                cursor = conn.cursor()
                cursor.execute("SHOW DATABASES LIKE 'vietnamese_normalizer'")
                db_exists = cursor.fetchone() is not None

                if not db_exists:
                    # Database chưa có → tự động setup
                    self.root.after(0, lambda: self.status_label.configure(
                        text="⏳ Đang tự động tạo database...",
                        fg=COLORS['fg_accent']
                    ))
                    cursor.close()
                    conn.close()

                    # Chạy setup_database
                    import setup_database
                    setup_database.main()
                else:
                    cursor.close()
                    conn.close()

                # Kết nối normalizer
                self.normalizer = VietnameseNormalizer()
                self.root.after(0, lambda: self.status_label.configure(
                    text="✅ Đã kết nối MySQL (port 3307) | Database: vietnamese_normalizer",
                    fg=COLORS['fg_success']
                ))
            except Exception as e:
                self.root.after(0, lambda: self.status_label.configure(
                    text=f"❌ Lỗi kết nối: {e}",
                    fg=COLORS['fg_accent']
                ))
                self.root.after(0, lambda: messagebox.showerror(
                    "Lỗi kết nối",
                    f"Không thể kết nối MySQL!\n\n"
                    f"Hãy kiểm tra:\n"
                    f"1. XAMPP đã bật MySQL?\n"
                    f"2. MySQL chạy trên port 3307?\n\n"
                    f"Chi tiết: {e}"
                ))

        thread = threading.Thread(target=_connect, daemon=True)
        thread.start()

    def on_normalize(self):
        """Xử lý khi nhấn nút Chuẩn hóa"""
        if not self.normalizer:
            messagebox.showwarning("Chưa kết nối",
                                   "Chưa kết nối được database!\nHãy kiểm tra XAMPP MySQL.")
            return

        text = self.input_text.get('1.0', 'end-1c').strip()
        if not text:
            messagebox.showwarning("Trống", "Vui lòng nhập đoạn văn cần chuẩn hóa!")
            return

        # Giới hạn 50 từ
        words = text.split()
        if len(words) > 50:
            messagebox.showwarning("Quá dài",
                                   f"Đoạn văn có {len(words)} từ, vui lòng nhập dưới 50 từ!")
            return

        # Disable button
        self.normalize_btn.configure(state='disabled', text='⏳ Đang xử lý...')

        def _process():
            try:
                result = self.normalizer.normalize_text(text)
                stats = self.normalizer.get_stats()
                analysis = self.normalizer.get_analysis_log()
                code = self.normalizer.get_code_steps()

                self.root.after(0, lambda: self._update_ui(text, result, stats, analysis, code))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Lỗi xử lý: {e}"))
            finally:
                self.root.after(0, lambda: self.normalize_btn.configure(
                    state='normal', text='⚡ CHUẨN HÓA'))

        thread = threading.Thread(target=_process, daemon=True)
        thread.start()

    def _update_ui(self, original, result, stats, analysis, code):
        """Cập nhật giao diện sau khi xử lý"""
        # Cập nhật text trước
        self.before_text.configure(state='normal')
        self.before_text.delete('1.0', 'end')
        self.before_text.insert('1.0', original)
        self.before_text.configure(state='disabled')

        # Cập nhật text sau
        self.after_text.configure(state='normal')
        self.after_text.delete('1.0', 'end')
        self.after_text.insert('1.0', result)
        self.after_text.configure(state='disabled')

        # Cập nhật code
        self.code_text.configure(state='normal')
        self.code_text.delete('1.0', 'end')
        self.code_text.insert('1.0', code)
        self.code_text.configure(state='disabled')

        # Cập nhật bảng phân tích
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, log in enumerate(analysis):
            tag = 'even' if i % 2 == 0 else 'odd'
            if log['original'] != log['result']:
                tag = 'changed'

            candidates_str = ', '.join(log.get('candidates', []))
            self.tree.insert('', 'end', values=(
                log['original'],
                log['result'],
                log['type'],
                candidates_str,
                log.get('reason', '')
            ), tags=(tag,))

        # Cập nhật stats
        self.stats_label.configure(
            text=f"📊 Tổng số từ: {stats['total_words']}  |  "
                 f"Từ thay đổi: {stats['changed_words']}  |  "
                 f"⏱ Thời gian: {stats['time_elapsed']:.6f}s",
            fg=COLORS['fg_highlight']
        )

    def on_close(self):
        """Đóng ứng dụng"""
        if self.normalizer:
            self.normalizer.close()
        self.root.destroy()


# ============================================================
# MAIN
# ============================================================
def main():
    root = tk.Tk()
    app = NormalizerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == '__main__':
    main()
