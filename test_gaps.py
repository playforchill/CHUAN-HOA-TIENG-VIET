"""
Script test tự động - Tìm từ thiếu trong database
"""
from normalizer import VietnameseNormalizer

n = VietnameseNormalizer()

# Tổng hợp các câu test đa dạng
test_cases = [
    # Teencode cơ bản
    "t k bt lm sao",
    "bn oi di dau vay",
    "mk thik bn nhiu lm",
    "e oi a nho e wa troi",
    "bjo m di dau z",
    "t cx k bt nma t nghi la dc",
    
    # Ký tự lặp
    "yeuuuu em nhiuuuu lammm",
    "thuongggg anh lammm",
    "vui qua troiiii oiiii",
    "buonnn wa troi oiii",
    "deppp qua luonnnn",
    "ngonnnn qua diiii",
    "nhoooo emmmm lammmm",
    "cuoiii qua diiii",
    "khocc maiii",
    "sooo qua diiii",
    "thieeuuu roi neee",
    "cham qua troiii",
    "nhanhhh len diii",
    
    # Câu đời thường
    "hom nay troi dep qua di choi thoi",
    "toi di hoc ve roi an com xong roi ngu",
    "ngay mai di thi mon toan kho lam",
    "tuan nay ban qua khong co thoi gian",
    "em dang lam bai tap ve nha",
    "anh dang o dau vay cho em di voi",
    "sang nay em di hoc muon roi",
    "chieu nay minh di uong ca phe nhe",
    "toi nay an gi day",
    "cuoi tuan minh di bien choi",
    
    # Câu tình cảm
    "anh yeu em nhieu lam",
    "em nho anh qua troi",
    "minh thuong ban nhieu lam",
    "hanh phuc qua di",
    "buon qua khong biet lam gi",
    "that vong qua troi oi",
    "vui ve hanh phuc moi ngay",
    
    # Câu hỏi
    "ban co khoe khong",
    "ban da an com chua",
    "may gio roi vay",
    "ai biet cho toi hoi",
    "tai sao ban khong di hoc",
    "bao gio ban ve",
    "lam sao de giai quyet van de nay",
    "ban muon an gi",
    
    # Teencode nâng cao
    "hn t di hoc r bn oi",
    "dc r t biet r",
    "cx dc thoi k sao dau",
    "chx bt lm j ca",
    "tks bn nhiu nhe",
    "xl bn t sai r",
    "bff oi di choi vs t k",
    "ny t dep lm",
    
    # Câu dài
    "hom nay la ngay dep troi toi muon di dao quanh ho tay voi ban be",
    "em da lam xong bai tap roi nhung chua hieu bai hoc hom nay lam",
    "toi can mua mot cai dien thoai moi vi cai cu da hong roi",
    "gia dinh toi co bon nguoi bo me anh trai va toi",
    
    # Câu có từ ghép
    "cong nghe thong tin rat phat trien",
    "suc khoe la quan trong nhat",
    "giao duc la quoc sach hang dau",
    "kinh te xa hoi ngay cang phat trien",
    
    # Từ láy
    "xinh xan nhe nhang vui ve",
    "lung linh lap lanh dep de",
    "lo lang hoi hop bon chon",
    "im lang yen tinh thanh binh",
    "lon xon nao nhiet soi dong",
    "dam da nong nan than thiet",
    "nho nhan xinh dep de thuong",
]

print("=" * 70)
print("🧪 TEST TỰ ĐỘNG - TÌM TỪ THIẾU TRONG DATABASE")
print("=" * 70)

missing_words = set()
total_words = 0
changed_words = 0

for test in test_cases:
    result = n.normalize_text(test)
    stats = n.get_stats()
    total_words += stats['total_words']
    changed_words += stats['changed_words']
    
    # Tìm từ "giữ nguyên" nhưng nên được xử lý
    for log in n.get_analysis_log():
        if log['type'] == 'giữ nguyên' and log['original'] == log['result']:
            word = log['original']
            # Bỏ qua từ đã đúng hoặc quá ngắn
            if len(word) >= 2 and word.isalpha():
                missing_words.add(word)
    
    # In kết quả
    unchanged = [l['original'] for l in n.get_analysis_log() if l['type'] == 'giữ nguyên' and l['original'] == l['result'] and len(l['original']) >= 2]
    if unchanged:
        print(f"\n📝 IN:  {test}")
        print(f"✅ OUT: {result}")
        print(f"⚠️  Từ chưa xử lý: {unchanged}")

print(f"\n{'=' * 70}")
print(f"📊 THỐNG KÊ:")
print(f"   Tổng từ đã xử lý: {total_words}")
print(f"   Từ đã thay đổi: {changed_words}")
print(f"   Tỷ lệ xử lý: {changed_words/total_words*100:.1f}%")
print(f"\n⚠️  DANH SÁCH TỪ BỊ THIẾU ({len(missing_words)} từ):")
for w in sorted(missing_words):
    print(f"   - {w}")

n.close()
