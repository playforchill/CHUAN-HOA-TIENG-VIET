# ỨNG DỤNG CHUẨN HÓA VĂN BẢN TIẾNG VIỆT

## 📌 Tổng quan dự án

Ứng dụng **Chuẩn hóa Văn bản Tiếng Việt** là một công cụ desktop được xây dựng bằng Python, có chức năng tự động chuyển đổi văn bản tiếng Việt không dấu, viết tắt (teencode), ký tự lặp... thành văn bản chuẩn có dấu đầy đủ.

**Ví dụ:**
| Đầu vào (Input) | Đầu ra (Output) |
|---|---|
| `anhhh iu em nhiu lm` | `Anh yêu em nhiều lắm` |
| `t cx k bt nma t nghi la dc` | `Tôi cũng không biết nhưng mà tôi nghĩ là được` |
| `bjo m di dau z` | `Bây giờ mày đi đâu vậy` |
| `vui ve nhe nhang xinh xan` | `Vui vẻ nhẹ nhàng xinh xắn` |
| `btvn nhiu wa lm k xog` | `Bài tập về nhà nhiều quá làm không xong` |

---

## 🛠️ Công nghệ sử dụng

### 1. Ngôn ngữ lập trình: Python 3

| Thông tin | Chi tiết |
|---|---|
| **Ngôn ngữ** | Python 3.14+ |
| **Lý do chọn** | Cú pháp đơn giản, hỗ trợ Unicode tốt (rất quan trọng cho tiếng Việt), thư viện phong phú |
| **Lệnh chạy** | `py app.py` |

### 2. Giao diện: Tkinter

| Thông tin | Chi tiết |
|---|---|
| **Thư viện** | Tkinter (có sẵn trong Python) |
| **Loại ứng dụng** | Desktop GUI (không cần web browser) |
| **Thành phần** | Ô nhập văn bản, bảng phân tích từng từ, hiển thị code xử lý, thống kê |

Tkinter là thư viện GUI mặc định của Python, không cần cài thêm. Giao diện được thiết kế với bảng màu hiện đại, bao gồm:
- **Ô nhập liệu (Input):** Người dùng nhập văn bản cần chuẩn hóa
- **Ô kết quả (Output):** Hiển thị văn bản đã được chuẩn hóa
- **Bảng phân tích:** Hiển thị chi tiết từng từ: từ gốc → kết quả → loại xử lý
- **Code nghiệp vụ:** Hiển thị các bước code đã chạy để xử lý
- **Thống kê:** Số từ thay đổi, thời gian xử lý

### 3. Cơ sở dữ liệu: MySQL (XAMPP)

| Thông tin | Chi tiết |
|---|---|
| **DBMS** | MySQL 8.0+ (qua XAMPP) |
| **Port** | 3307 |
| **Database** | `vietnamese_normalizer` |
| **Thư viện kết nối** | `mysql-connector-python` |
| **Charset** | UTF-8 MB4 (hỗ trợ đầy đủ tiếng Việt) |

#### Cấu trúc Database (6 bảng):

```
vietnamese_normalizer
├── vietnamese_words        (1142 bản ghi) - Từ điển tiếng Việt
├── abbreviations           (317 bản ghi)  - Từ viết tắt / teencode  
├── bigrams                 (458 bản ghi)  - Cặp từ đi cùng nhau
├── reduplicative_words     (200 bản ghi)  - Từ láy
├── trigrams                (102 bản ghi)  - Bộ ba từ ngữ cảnh
└── common_misspellings     (44 bản ghi)   - Lỗi chính tả phổ biến
    Tổng: ~2263 bản ghi
```

**Chi tiết các bảng:**

| Bảng | Mục đích | Ví dụ |
|---|---|---|
| `vietnamese_words` | Lưu từ không dấu → có dấu | `dep` → `đẹp`, `hoc` → `học` |
| `abbreviations` | Lưu từ viết tắt → đầy đủ | `k` → `không`, `dc` → `được`, `btvn` → `bài tập về nhà` |
| `bigrams` | Lưu cặp từ hay đi cùng | (`anh`, `yeu`) freq=95, (`di`, `hoc`) freq=85 |
| `reduplicative_words` | Lưu từ láy tiếng Việt | `xinh xan` → `xinh xắn`, `vui ve` → `vui vẻ` |
| `trigrams` | Lưu bộ 3 từ ngữ cảnh | (`anh`, `yeu`, `em`) freq=95 |
| `common_misspellings` | Lưu mẫu lỗi chính tả | `trien` → `triển` (lỗi phonetic) |

---

## ⚙️ Thuật toán xử lý

### Phương pháp: Dictionary-based + N-gram Scoring

Ứng dụng **KHÔNG sử dụng API bên ngoài** hay Machine Learning/AI. Toàn bộ xử lý dựa trên:
- **Tra cứu từ điển** (Dictionary Lookup)
- **Phân tích ngữ cảnh** bằng N-gram (Bigram + Trigram)

### Quy trình xử lý (Pipeline):

```
Văn bản đầu vào
    │
    ▼
┌─────────────────────────────┐
│ Bước 1: Tách từ (Tokenize)  │  "anhhh iu em" → ["anhhh", "iu", "em"]
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Bước 1.5: Phát hiện từ láy  │  "vui ve" → "vui vẻ" (từ láy âm đầu)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│ Bước 2: Xử lý từng từ (theo thứ tự ưu tiên)               │
│                                                             │
│   2.0 Từ đã có dấu? → Giữ nguyên                          │
│       "đẹp" → "đẹp" ✅                                     │
│                                                             │
│   2.1 Từ viết tắt? → Tra bảng abbreviations                │
│       "k" → "không", "dc" → "được"                         │
│       Nếu nhiều nghĩa → Dùng ngữ cảnh (Bigram/Trigram)    │
│                                                             │
│   2.2 Ký tự lặp? → Giảm lặp + Tra từ điển                 │
│       "anhhh" → "anh" → "anh" ✅                            │
│       "thieeuuuu" → "thieu" → "thiếu" ✅                    │
│                                                             │
│   2.3 Từ bình thường? → Tra bảng vietnamese_words           │
│       "dep" → "đẹp", "hoc" → "học"                         │
│       Nếu đồng âm → Dùng ngữ cảnh chọn nghĩa phù hợp    │
│                                                             │
│   2.4 Lỗi chính tả? → Tra bảng common_misspellings         │
│       "trien" → "triển"                                     │
│                                                             │
│   2.5 Không tìm thấy → Giữ nguyên                          │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Bước 3: Ghép kết quả        │  ["anh", "yêu", "em"] → "anh yêu em"
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Bước 4: Viết hoa đầu câu    │  "anh yêu em" → "Anh yêu em"
└─────────────┬───────────────┘
              │
              ▼
        Văn bản chuẩn hóa
```

### Chi tiết thuật toán phân tích ngữ cảnh (N-gram Scoring):

Khi một từ có **nhiều nghĩa** (đồng âm), hệ thống sử dụng ngữ cảnh xung quanh để chọn nghĩa phù hợp nhất.

**Ví dụ:** Từ `di` có thể là `đi`, `dì`, `di`,...

```
Câu: "toi di hoc"

Bước 1: Lấy ngữ cảnh (context window = 2 từ trước + 2 từ sau)
         trước: ["toi"] | hiện tại: "di" | sau: ["hoc"]

Bước 2: Tính điểm Bigram cho mỗi ứng viên:
         - "đi": bigram("toi", "di") = 0, bigram("di", "hoc") = 85 → score = 85
         - "dì": bigram("toi", "di") = 0, bigram("di", "hoc") = 0  → score = 0

Bước 3: Tính điểm Trigram (nếu có):
         - trigram("toi", "di", "hoc") → cộng thêm điểm

Bước 4: Chọn ứng viên có score cao nhất → "đi" ✅
```

**Công thức tính điểm:**
```
Score = Frequency_word + Σ(Bigram_freq × weight) + Σ(Trigram_freq × 0.7)

Trong đó:
- Frequency_word: Tần suất sử dụng của từ
- Bigram_freq: Tần suất cặp từ đi cùng
- Trigram_freq: Tần suất bộ 3 từ
- weight: Từ càng gần → trọng số càng cao (1.0 cho từ liền kề, 0.5 cho từ cách 1)
```

---

## 📁 Cấu trúc dự án

```
dự án python/
│
├── app.py                  # Giao diện chính (Tkinter GUI)
│                           # - Ô nhập/xuất văn bản
│                           # - Bảng phân tích chi tiết
│                           # - Hiển thị code xử lý
│                           # - Thống kê kết quả
│
├── normalizer.py           # Engine chuẩn hóa (lõi xử lý)
│                           # - Class VietnameseNormalizer
│                           # - Xử lý ký tự lặp
│                           # - Tra từ điển + viết tắt
│                           # - Bigram/Trigram scoring
│                           # - Phát hiện từ láy
│                           # - Viết hoa đầu câu
│
├── database.sql            # File SQL seed dữ liệu
│                           # - 6 bảng, ~2263 bản ghi
│                           # - Import trực tiếp vào phpMyAdmin
│
├── setup_database.py       # Script tạo database tự động
│                           # - Đọc file database.sql
│                           # - Thực thi vào MySQL
│
├── requirements.txt        # Thư viện Python cần cài
│                           # - mysql-connector-python
│
└── test_gaps.py           # Script test tự động
                            # - Phát hiện từ thiếu trong database
```

---

## 🔗 Luồng hoạt động (Flow)

```
                    ┌─────────────────────┐
                    │   XAMPP (MySQL)      │
                    │   Port: 3307        │
                    │   DB: vietnamese_   │
                    │       normalizer    │
                    └─────────┬───────────┘
                              │ mysql-connector-python
                              │
 ┌────────────────────────────┼────────────────────────────┐
 │                            │                            │
 │  setup_database.py    normalizer.py              app.py │
 │  (Import database.sql)    │                        │    │
 │         │            ┌────┴────┐               ┌───┴──┐ │
 │         │            │ _load   │               │Tkinter│ │
 │         └───────────►│ _cache()│◄──────────────│  GUI  │ │
 │                      │         │  gọi class    │       │ │
 │                      └────┬────┘               └───┬──┘ │
 │                           │                        │    │
 │                     normalize_text()          Hiển thị   │
 │                           │                   kết quả   │
 │                           ▼                        │    │
 │                    Văn bản chuẩn hóa ──────────────┘    │
 │                                                         │
 └─────────────────── PYTHON APPLICATION ──────────────────┘
```

**Luồng chi tiết:**

1. **Khởi động:** `py app.py` → Tkinter hiển thị giao diện
2. **Kết nối:** `VietnameseNormalizer.__init__()` → Kết nối MySQL → Load toàn bộ dữ liệu vào RAM (cache)
3. **Xử lý:** Người dùng nhập text → Nhấn "Chuẩn hóa" → `normalize_text()` xử lý → Hiển thị kết quả
4. **Phân tích:** Bảng chi tiết hiển thị quá trình xử lý từng từ

---

## 🗄️ Chiến lược lưu trữ dữ liệu

### Caching (Bộ nhớ đệm):

Ứng dụng sử dụng chiến lược **Load All at Startup** — toàn bộ dữ liệu từ MySQL được load vào RAM khi khởi động:

```python
# Khi VietnameseNormalizer được tạo:
self.word_dict = {}       # {word: [{accent, freq}, ...]}
self.abbr_dict = {}       # {abbreviation: [{full, accent, priority}, ...]}
self.bigram_dict = {}     # {word1: [{word2, freq}, ...]}
self.redup_dict = {}      # {word_pair: {accent, type, freq}}
self.trigram_dict = {}    # {(word1, word2): [{word3, freq}, ...]}
self.misspell_dict = {}   # {misspelling: {correct, accent, type}}
```

**Ưu điểm:**
- Tốc độ tra cứu cực nhanh (O(1) với dictionary)
- Không cần truy vấn SQL khi xử lý
- Thời gian xử lý mỗi câu: ~0.0002 giây

**Nhược điểm:**
- Tốn RAM khi dữ liệu lớn (hiện tại ~2263 records ≈ rất nhỏ)
- Phải restart app khi cập nhật database

---

## 📊 Hiệu năng

| Chỉ số | Giá trị |
|---|---|
| Thời gian load database | ~0.5 giây |
| Thời gian xử lý 1 câu | ~0.0002 giây |
| Tỷ lệ xử lý đúng | ~86.5% |
| Tổng dữ liệu | 2263 bản ghi |
| RAM sử dụng | < 10 MB |

---

## 📦 Cài đặt và chạy

### Yêu cầu hệ thống:
- Python 3.10+
- XAMPP (MySQL chạy trên port 3307)

### Các bước:

```bash
# 1. Cài thư viện
pip install mysql-connector-python

# 2. Bật XAMPP → Start MySQL

# 3. Import database (chọn 1 trong 2 cách):
#    Cách A: Chạy script Python
py setup_database.py

#    Cách B: Import qua phpMyAdmin
#    Mở http://localhost/phpmyadmin → Import → Chọn database.sql

# 4. Chạy ứng dụng
py app.py
```

---

## 🔬 Các kỹ thuật NLP sử dụng

| STT | Kỹ thuật | Mô tả | Ứng dụng trong project |
|---|---|---|---|
| 1 | **Tokenization** | Tách câu thành danh sách từ | `text.split(' ')` |
| 2 | **Dictionary Lookup** | Tra cứu từ trong từ điển | Thêm dấu: `dep` → `đẹp` |
| 3 | **N-gram Language Model** | Mô hình ngôn ngữ dựa trên cặp/bộ từ | Bigram + Trigram scoring |
| 4 | **Pattern Matching** | Nhận diện mẫu bằng Regex | Xử lý ký tự lặp: `anhhh` → `anh` |
| 5 | **Context Window** | Phân tích ngữ cảnh xung quanh | Window = 2 từ trước + 2 từ sau |
| 6 | **Frequency-based Ranking** | Xếp hạng theo tần suất | Chọn từ phổ biến nhất khi đồng âm |
| 7 | **Reduplication Detection** | Phát hiện từ láy tiếng Việt | `xinh xan` → `xinh xắn` |
| 8 | **Text Normalization** | Chuẩn hóa viết hoa, dấu câu | Viết hoa đầu câu tự động |

---

## 📝 Tóm tắt công nghệ

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3 |
| Giao diện | Tkinter (Desktop GUI) |
| Cơ sở dữ liệu | MySQL (XAMPP, port 3307) |
| Kết nối DB | mysql-connector-python |
| Thuật toán chính | Dictionary Lookup + N-gram Scoring |
| Phương pháp NLP | Tokenization, Pattern Matching, Context Analysis |
| Kiểu xử lý | Offline (không dùng API/Internet) |
| Chiến lược dữ liệu | Load All + In-Memory Cache |
