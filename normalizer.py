"""
Vietnamese Normalizer Engine - Phiên bản nâng cấp Pro
Xử lý chuẩn hóa văn bản tiếng Việt:
- Xử lý từ lặp ký tự (anhhh → anh)
- Xử lý từ viết tắt (k → không)
- Phân tích ngữ cảnh bằng bigram + trigram + expanded context
- Nhận diện từ đã có dấu
- Xử lý từ láy
- Phát hiện lỗi chính tả phổ biến
- Chuẩn hóa viết hoa đầu câu + dấu câu
"""

import re
import time
import mysql.connector
from mysql.connector import Error


# ============================================================
# CẤU HÌNH
# ============================================================
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': '',
    'database': 'vietnamese_normalizer'
}

# Các ký tự có dấu tiếng Việt
VIETNAMESE_DIACRITICS = set('àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ'
                           'ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ')

# Dấu câu kết thúc
SENTENCE_ENDINGS = {'.', '!', '?'}


def has_vietnamese_diacritics(word):
    """Kiểm tra từ đã có dấu tiếng Việt chưa"""
    return any(c in VIETNAMESE_DIACRITICS for c in word)


class VietnameseNormalizer:
    """Engine chuẩn hóa tiếng Việt - Phiên bản Pro"""

    def __init__(self):
        self.conn = None
        self.cursor = None
        self.analysis_log = []       # Log quá trình phân tích
        self.code_steps = []         # Code xử lý nghiệp vụ
        self.stats = {
            'total_words': 0,
            'changed_words': 0,
            'time_elapsed': 0
        }
        self._connect()
        self._load_cache()

    def _connect(self):
        """Kết nối database"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
        except Error as e:
            raise ConnectionError(f"Không thể kết nối MySQL: {e}")

    def _load_cache(self):
        """Load dữ liệu từ database vào bộ nhớ để xử lý nhanh"""
        # Cache từ điển
        self.cursor.execute("SELECT word, word_with_accent, frequency FROM vietnamese_words")
        rows = self.cursor.fetchall()
        self.word_dict = {}
        for row in rows:
            word = row['word']
            if word not in self.word_dict:
                self.word_dict[word] = []
            self.word_dict[word].append({
                'accent': row['word_with_accent'],
                'freq': row['frequency']
            })

        # Cache từ viết tắt
        self.cursor.execute("SELECT abbreviation, full_word, full_word_accent, priority FROM abbreviations")
        rows = self.cursor.fetchall()
        self.abbr_dict = {}
        for row in rows:
            abbr = row['abbreviation']
            if abbr not in self.abbr_dict:
                self.abbr_dict[abbr] = []
            self.abbr_dict[abbr].append({
                'full': row['full_word'],
                'accent': row['full_word_accent'],
                'priority': row['priority']
            })

        # Cache bigrams
        self.cursor.execute("SELECT word1, word2, frequency FROM bigrams")
        rows = self.cursor.fetchall()
        self.bigram_dict = {}
        for row in rows:
            key = row['word1']
            if key not in self.bigram_dict:
                self.bigram_dict[key] = []
            self.bigram_dict[key].append({
                'word2': row['word2'],
                'freq': row['frequency']
            })

        # Cache từ láy
        try:
            self.cursor.execute("SELECT word_no_accent, word_with_accent, type, frequency FROM reduplicative_words")
            rows = self.cursor.fetchall()
            self.redup_dict = {}
            for row in rows:
                key = row['word_no_accent']
                self.redup_dict[key] = {
                    'accent': row['word_with_accent'],
                    'type': row['type'],
                    'freq': row['frequency']
                }
        except Exception:
            self.redup_dict = {}

        # Cache trigrams (MỚI)
        try:
            self.cursor.execute("SELECT word1, word2, word3, frequency FROM trigrams")
            rows = self.cursor.fetchall()
            self.trigram_dict = {}
            for row in rows:
                key = (row['word1'], row['word2'])
                if key not in self.trigram_dict:
                    self.trigram_dict[key] = []
                self.trigram_dict[key].append({
                    'word3': row['word3'],
                    'freq': row['frequency']
                })
        except Exception:
            self.trigram_dict = {}

        # Cache lỗi chính tả (MỚI)
        try:
            self.cursor.execute("SELECT misspelling, correct_word, correct_accent, error_type FROM common_misspellings")
            rows = self.cursor.fetchall()
            self.misspell_dict = {}
            for row in rows:
                key = row['misspelling']
                self.misspell_dict[key] = {
                    'correct': row['correct_word'],
                    'accent': row['correct_accent'],
                    'type': row['error_type']
                }
        except Exception:
            self.misspell_dict = {}

    def normalize_text(self, text):
        """
        Hàm chính: Chuẩn hóa đoạn văn bản
        Input: "anhhh iu em k biet dc"
        Output: "Anh yêu em không biết được."
        """
        start_time = time.perf_counter()

        # Reset logs
        self.analysis_log = []
        self.code_steps = []
        self.stats = {'total_words': 0, 'changed_words': 0, 'time_elapsed': 0}

        self.code_steps.append("# Bước 1: Tách từ trong câu")
        self.code_steps.append(f'text = "{text}"')

        # Tách từ (giữ lại dấu câu)
        # Chuẩn hóa khoảng trắng
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)

        words = text.split(' ')
        self.code_steps.append(f'words = text.split(" ")  # → {words}')
        self.code_steps.append("")

        self.stats['total_words'] = len(words)

        # Bước 1.5: Xử lý từ láy (2 từ liền nhau)
        self.code_steps.append("# Bước 1.5: Kiểm tra từ láy")
        redup_marks = self._detect_reduplicative(words)

        # Xử lý từng từ
        result_words = []
        self.code_steps.append("\n# Bước 2: Xử lý từng từ")

        i = 0
        while i < len(words):
            word = words[i]
            if not word.strip():
                i += 1
                continue

            word_lower = word.lower().strip()
            self.code_steps.append(f'\n# --- Xử lý từ [{i}]: "{word_lower}" ---')

            # Kiểm tra từ láy (2 từ đi cùng)
            if i in redup_marks:
                redup_result = redup_marks[i]
                result_words.append(redup_result['word1'])
                result_words.append(redup_result['word2'])
                self.analysis_log.append({
                    'original': f"{words[i]} {words[i+1]}",
                    'result': redup_result['accent'],
                    'type': 'từ láy',
                    'candidates': [redup_result['accent']],
                    'reason': f'"{words[i]} {words[i+1]}" → "{redup_result["accent"]}" (từ láy {redup_result["type"]})'
                })
                self.code_steps.append(f'  # Từ láy: "{words[i]} {words[i+1]}" → "{redup_result["accent"]}"')
                self.stats['changed_words'] += 1
                i += 2
                continue

            # Xử lý từ đơn
            new_word, log_entry = self._process_word(word_lower, i, words)

            if new_word != word_lower:
                self.stats['changed_words'] += 1

            result_words.append(new_word)
            self.analysis_log.append(log_entry)
            i += 1

        # Bước 3: Ghép lại
        result = ' '.join(result_words)
        
        # Bước 4: Chuẩn hóa viết hoa đầu câu
        result = self._capitalize_sentences(result)
        
        self.code_steps.append(f"\n# Bước 3: Ghép kết quả")
        self.code_steps.append(f'result = " ".join(result_words)')
        self.code_steps.append(f"\n# Bước 4: Viết hoa đầu câu")
        self.code_steps.append(f'# → "{result}"')

        self.stats['time_elapsed'] = time.perf_counter() - start_time

        return result

    def _capitalize_sentences(self, text):
        """Viết hoa chữ cái đầu câu"""
        if not text:
            return text
        
        # Viết hoa chữ đầu tiên
        result = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Viết hoa sau dấu câu (. ! ?)
        for ending in SENTENCE_ENDINGS:
            parts = result.split(ending + ' ')
            result = (ending + ' ').join(
                part[0].upper() + part[1:] if len(part) > 1 else part.upper() if part else part
                for part in parts
            )
        
        return result

    def _detect_reduplicative(self, words):
        """Phát hiện từ láy trong danh sách từ"""
        marks = {}
        for i in range(len(words) - 1):
            w1 = words[i].lower().strip()
            w2 = words[i + 1].lower().strip()

            # Bỏ dấu để tìm
            w1_no = self._remove_accents(w1)
            w2_no = self._remove_accents(w2)

            combo = f"{w1_no} {w2_no}"
            if combo in self.redup_dict:
                entry = self.redup_dict[combo]
                accent_parts = entry['accent'].split(' ')
                marks[i] = {
                    'word1': accent_parts[0] if len(accent_parts) > 0 else w1,
                    'word2': accent_parts[1] if len(accent_parts) > 1 else w2,
                    'accent': entry['accent'],
                    'type': entry['type']
                }
        return marks

    def _remove_accents(self, text):
        """Loại bỏ dấu tiếng Việt (đơn giản)"""
        accents_map = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'đ': 'd',
        }
        result = ''
        for c in text:
            result += accents_map.get(c, c)
        return result

    def _process_word(self, word, index, all_words):
        """Xử lý một từ đơn lẻ - Phiên bản Pro"""

        log = {
            'original': word,
            'result': word,
            'type': 'giữ nguyên',
            'candidates': [],
            'reason': ''
        }

        # --- Kiểm tra 0: Từ đã có dấu tiếng Việt → giữ nguyên ---
        if has_vietnamese_diacritics(word):
            log['type'] = 'đã có dấu'
            log['reason'] = f'"{word}" → giữ nguyên (đã có dấu tiếng Việt)'
            self.code_steps.append(f'  # "{word}" đã có dấu → giữ nguyên ✅')
            return word, log

        # --- Kiểm tra 1: Từ viết tắt ---
        if word in self.abbr_dict:
            candidates = self.abbr_dict[word]
            log['candidates'] = [c['accent'] for c in candidates]

            self.code_steps.append(f'  # Tìm thấy từ viết tắt: "{word}"')
            self.code_steps.append(f'  # Candidates: {log["candidates"]}')

            if len(candidates) == 1:
                chosen = candidates[0]
                log['result'] = chosen['accent']
                log['type'] = 'viết tắt'
                log['reason'] = f'"{word}" → "{chosen["accent"]}" (từ viết tắt)'
                self.code_steps.append(f'  result = "{chosen["accent"]}"  # chỉ 1 lựa chọn')
                return chosen['accent'], log
            else:
                # Nhiều lựa chọn → dùng ngữ cảnh mở rộng
                chosen = self._choose_by_context(word, candidates, index, all_words)
                log['result'] = chosen['accent']
                log['type'] = 'viết tắt + ngữ cảnh'
                log['reason'] = f'"{word}" → "{chosen["accent"]}" (chọn theo ngữ cảnh)'
                self.code_steps.append(f'  # Chọn theo ngữ cảnh → "{chosen["accent"]}"')
                return chosen['accent'], log

        # --- Kiểm tra 2: Ký tự lặp ---
        fixed, was_duplicate = self._fix_duplicate_chars(word)
        if was_duplicate:
            log['result'] = fixed
            log['type'] = 'ký tự lặp'
            log['reason'] = f'"{word}" → "{fixed}" (bỏ ký tự lặp)'
            log['candidates'] = [fixed]
            self.code_steps.append(f'  # Phát hiện ký tự lặp: "{word}" → "{fixed}"')

            # Thử tra từ đã sửa trong dictionary
            if fixed in self.word_dict:
                entries = self.word_dict[fixed]
                # Dùng context để chọn từ tốt nhất
                best = self._choose_best_word(fixed, entries, index, all_words)
                log['result'] = best['accent']
                log['candidates'] = [e['accent'] for e in entries]
                log['reason'] = f'"{word}" → "{best["accent"]}" (bỏ lặp + thêm dấu)'
                log['type'] = 'ký tự lặp + thêm dấu'
                self.code_steps.append(f'  # Tra từ điển: "{fixed}" → "{best["accent"]}"')
                return best['accent'], log

            # Thử tra trong abbreviation sau khi fix duplicate
            if fixed in self.abbr_dict:
                candidates = self.abbr_dict[fixed]
                chosen = candidates[0] if len(candidates) == 1 else \
                    self._choose_by_context(fixed, candidates, index, all_words)
                log['result'] = chosen['accent']
                log['type'] = 'ký tự lặp + viết tắt'
                log['reason'] = f'"{word}" → "{chosen["accent"]}" (bỏ lặp + viết tắt)'
                self.code_steps.append(f'  # Bỏ lặp + viết tắt: "{fixed}" → "{chosen["accent"]}"')
                return chosen['accent'], log

            # KHÔNG return ở đây! Cập nhật word = fixed
            # và tiếp tục xuống bước 3 để tra từ điển thêm dấu
            self.code_steps.append(f'  # Chưa tìm thấy "{fixed}" trực tiếp, tiếp tục tra dấu...')
            word = fixed  # Dùng từ đã bỏ lặp để tiếp tục xử lý

        # --- Kiểm tra 3: Từ bình thường → tra từ điển ---
        if word in self.word_dict:
            entries = self.word_dict[word]
            # Dùng context để chọn từ tốt nhất (xử lý từ đồng âm)
            best = self._choose_best_word(word, entries, index, all_words)

            # Nếu từ có dấu khác từ gốc
            if best['accent'] != word:
                log['result'] = best['accent']
                log['type'] = 'thêm dấu'
                log['candidates'] = [e['accent'] for e in entries]
                log['reason'] = f'"{word}" → "{best["accent"]}" (thêm dấu)'
                self.code_steps.append(f'  # Tra từ điển: "{word}" → "{best["accent"]}"')
            else:
                log['reason'] = f'"{word}" → giữ nguyên (đã đúng)'
                self.code_steps.append(f'  # "{word}" → giữ nguyên')

            return best['accent'], log

        # --- Kiểm tra 4: Lỗi chính tả phổ biến (MỚI) ---
        if word in self.misspell_dict:
            entry = self.misspell_dict[word]
            log['result'] = entry['accent']
            log['type'] = f'lỗi chính tả ({entry["type"]})'
            log['candidates'] = [entry['accent']]
            log['reason'] = f'"{word}" → "{entry["accent"]}" (sửa lỗi chính tả: {entry["type"]})'
            self.code_steps.append(f'  # Lỗi chính tả: "{word}" → "{entry["accent"]}"')
            return entry['accent'], log

        # --- Không tìm thấy → giữ nguyên ---
        log['reason'] = f'"{word}" → giữ nguyên (không có trong từ điển)'
        self.code_steps.append(f'  # "{word}" → giữ nguyên (không tìm thấy)')
        return word, log

    def _fix_duplicate_chars(self, word):
        """
        Xử lý ký tự lặp: anhhh → anh, yeuuuu → yeu
        Thuật toán: Thử giảm dần ký tự lặp, kiểm tra từ điển
        """
        # Tìm ký tự lặp >= 2 lần liên tiếp
        has_dup = re.search(r'(.)\1{1,}', word)
        if not has_dup:
            return word, False

        self.code_steps.append(f'  # Phát hiện ký tự lặp trong "{word}"')

        # Tạo các biến thể bằng cách giảm ký tự lặp
        candidates = self._generate_reduce_variants(word)
        self.code_steps.append(f'  # Các biến thể: {candidates[:5]}...')

        # Kiểm tra từng biến thể trong từ điển
        for variant in candidates:
            if variant in self.word_dict:
                self.code_steps.append(f'  # Tìm thấy trong từ điển: "{variant}" ✅')
                return variant, True

        # Kiểm tra trong abbreviation dict
        for variant in candidates:
            if variant in self.abbr_dict:
                self.code_steps.append(f'  # Tìm thấy trong viết tắt: "{variant}" ✅')
                return variant, True

        # Nếu không tìm thấy, trả về dạng giảm tối đa
        reduced = re.sub(r'(.)\1+', r'\1', word)
        return reduced, True

    def _generate_reduce_variants(self, word):
        """Tạo các biến thể bằng cách giảm ký tự lặp"""
        variants = []

        # Đơn giản: tạo biến thể giảm dần
        current = word
        while re.search(r'(.)\1{1,}', current):
            # Giảm 1 ký tự lặp mỗi lần
            new = re.sub(r'(.)\1{1,}', lambda m: m.group(1) * max(1, len(m.group()) - 1), current)
            if new == current:
                break
            if new not in variants:
                variants.append(new)
            current = new

        # Thêm dạng giảm tối đa (mỗi ký tự lặp chỉ giữ 1)
        minimal = re.sub(r'(.)\1+', r'\1', word)
        if minimal not in variants:
            variants.append(minimal)

        return variants

    def _choose_best_word(self, word, entries, index, all_words):
        """
        Chọn từ có dấu phù hợp nhất dựa trên ngữ cảnh
        Xử lý từ đồng âm (VD: 'ma' → 'mà/mã/ma')
        Sử dụng cả bigram và trigram scoring
        """
        if len(entries) == 1:
            return entries[0]

        best_entry = entries[0]
        best_score = entries[0]['freq']

        # Lấy context mở rộng (2 từ trước + 2 từ sau)
        context_words = self._get_context_words(index, all_words, window=2)

        for entry in entries:
            score = entry['freq']

            # Tìm unaccented form của entry
            entry_no_accent = self._remove_accents(entry['accent'])

            # --- Bigram scoring ---
            for ctx_word in context_words:
                ctx_no_accent = self._remove_accents(ctx_word.lower().strip())

                # Bigram: context_word + this_word
                if ctx_no_accent in self.bigram_dict:
                    for bg in self.bigram_dict[ctx_no_accent]:
                        if bg['word2'] == entry_no_accent or bg['word2'] == word:
                            score += bg['freq'] * 0.5

                # Bigram: this_word + context_word
                if entry_no_accent in self.bigram_dict:
                    for bg in self.bigram_dict[entry_no_accent]:
                        if bg['word2'] == ctx_no_accent:
                            score += bg['freq'] * 0.5

            # --- Trigram scoring (MỚI) ---
            score += self._trigram_score(word, entry_no_accent, index, all_words)

            if score > best_score:
                best_score = score
                best_entry = entry

        return best_entry

    def _trigram_score(self, word, word_no_accent, index, all_words):
        """Tính điểm trigram cho một từ tại vị trí index"""
        score = 0
        
        # Lấy 2 từ trước
        if index >= 2:
            w1 = self._remove_accents(all_words[index - 2].lower().strip())
            w2 = self._remove_accents(all_words[index - 1].lower().strip())
            key = (w1, w2)
            if key in self.trigram_dict:
                for tri in self.trigram_dict[key]:
                    if tri['word3'] == word_no_accent or tri['word3'] == word:
                        score += tri['freq'] * 0.7

        # Từ trước + từ hiện tại + từ sau
        if index >= 1 and index < len(all_words) - 1:
            w1 = self._remove_accents(all_words[index - 1].lower().strip())
            w3 = self._remove_accents(all_words[index + 1].lower().strip())
            key = (w1, word_no_accent)
            if key in self.trigram_dict:
                for tri in self.trigram_dict[key]:
                    if tri['word3'] == w3:
                        score += tri['freq'] * 0.7

        return score

    def _choose_by_context(self, word, candidates, index, all_words):
        """
        Chọn từ phù hợp nhất dựa trên ngữ cảnh - Phiên bản Pro
        Sử dụng expanded context window (2 từ trước + 2 từ sau)
        + Trigram scoring
        """
        if len(candidates) == 1:
            return candidates[0]

        best_candidate = candidates[0]
        best_score = candidates[0]['priority']

        # Lấy context mở rộng
        context = self._get_context_words(index, all_words, window=2)
        prev_words = []
        next_words = []

        for j in range(max(0, index - 2), index):
            prev_words.append(all_words[j].lower().strip())
        for j in range(index + 1, min(len(all_words), index + 3)):
            next_words.append(all_words[j].lower().strip())

        self.code_steps.append(f'  # Ngữ cảnh mở rộng: trước={prev_words}, sau={next_words}')

        for candidate in candidates:
            score = candidate['priority']
            full_no_accent = candidate['full']
            accent = candidate['accent']

            # --- Bigram scoring ---
            # Kiểm tra bigram với tất cả từ trước
            for prev_word in prev_words:
                prev_no_accent = self._remove_accents(prev_word)

                if prev_no_accent in self.bigram_dict:
                    for bg in self.bigram_dict[prev_no_accent]:
                        if bg['word2'] == full_no_accent:
                            # Từ gần hơn có trọng số cao hơn
                            weight = 1.0 if prev_word == prev_words[-1] else 0.5
                            score += bg['freq'] * weight
                            self.code_steps.append(
                                f'  # Bigram "{prev_no_accent} {full_no_accent}" '
                                f'freq={bg["freq"]} × {weight} → score={score}'
                            )

                # Cũng check với từ đã viết tắt (prev_word có thể là teencode)
                if prev_word in self.abbr_dict:
                    for abbr_entry in self.abbr_dict[prev_word]:
                        abbr_full = abbr_entry['full']
                        if abbr_full in self.bigram_dict:
                            for bg in self.bigram_dict[abbr_full]:
                                if bg['word2'] == full_no_accent:
                                    score += bg['freq'] * 0.3

            # Kiểm tra bigram với tất cả từ sau
            for next_word in next_words:
                next_no_accent = self._remove_accents(next_word)

                if full_no_accent in self.bigram_dict:
                    for bg in self.bigram_dict[full_no_accent]:
                        if bg['word2'] == next_no_accent:
                            weight = 1.0 if next_word == next_words[0] else 0.5
                            score += bg['freq'] * weight

                # Check bigram với từ đã viết tắt
                if next_word in self.abbr_dict:
                    for abbr_entry in self.abbr_dict[next_word]:
                        abbr_full = abbr_entry['full']
                        if full_no_accent in self.bigram_dict:
                            for bg in self.bigram_dict[full_no_accent]:
                                if bg['word2'] == abbr_full:
                                    score += bg['freq'] * 0.3

            # --- Trigram scoring (MỚI) ---
            score += self._trigram_score(word, full_no_accent, index, all_words)

            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate

    def _get_context_words(self, index, all_words, window=2):
        """Lấy các từ xung quanh (context window mở rộng)"""
        context = []
        for j in range(max(0, index - window), index):
            context.append(all_words[j])
        for j in range(index + 1, min(len(all_words), index + window + 1)):
            context.append(all_words[j])
        return context

    def get_analysis_log(self):
        """Trả về bảng phân tích"""
        return self.analysis_log

    def get_code_steps(self):
        """Trả về code xử lý nghiệp vụ"""
        return '\n'.join(self.code_steps)

    def get_stats(self):
        """Trả về thống kê"""
        return self.stats

    def close(self):
        """Đóng kết nối"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# ============================================================
# TEST
# ============================================================
if __name__ == '__main__':
    print("🧪 Test Vietnamese Normalizer - Phiên bản Pro")
    print("=" * 60)

    try:
        normalizer = VietnameseNormalizer()

        test_cases = [
            "anhhh iu em",
            "anh iu em nhất mà",
            "toi k biet dc",
            "bn oi di hoc chuaaa",
            "mk thuongggg bn lam",
            "hn di an k",
            "thik qua lun",
            "e oi a nho e nhiu",
            "bjo m di dau z",
            "t cx k bt nma t nghi la dc",
            "troi dep qua di choi thoi",
            "vui ve nhe nhang xinh xan",
            "btvn nhiu wa lm k xog",
            "e oi mai di an pho vs a k",
        ]

        for test in test_cases:
            result = normalizer.normalize_text(test)
            stats = normalizer.get_stats()
            print(f'\n📝 Input:  "{test}"')
            print(f'✅ Output: "{result}"')
            print(f'📊 Từ thay đổi: {stats["changed_words"]}/{stats["total_words"]} '
                  f'| Thời gian: {stats["time_elapsed"]:.6f}s')

            # In bảng phân tích
            print("   ┌────────────────┬────────────────┬──────────────────┐")
            print("   │  Từ gốc        │  Kết quả       │  Loại            │")
            print("   ├────────────────┼────────────────┼──────────────────┤")
            for log in normalizer.get_analysis_log():
                orig = log['original'][:14]
                res = log['result'][:14]
                typ = log['type'][:16]
                print(f"   │ {orig:<14} │ {res:<14} │ {typ:<16} │")
            print("   └────────────────┴────────────────┴──────────────────┘")

        normalizer.close()
        print("\n✅ Test hoàn tất!")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
