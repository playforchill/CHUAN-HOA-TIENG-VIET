"""
Setup Database - Tạo database và seed dữ liệu cho ứng dụng Chuẩn hóa Tiếng Việt
Sử dụng XAMPP MySQL trên port 3307
Có 2 cách:
  1. Import file database.sql vào phpMyAdmin
  2. Chạy file này: py setup_database.py
"""

import mysql.connector
from mysql.connector import Error
import os

# ============================================================
# CẤU HÌNH KẾT NỐI
# ============================================================
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': ''
}

DB_NAME = 'vietnamese_normalizer'


def create_connection(with_db=False):
    """Tạo kết nối đến MySQL"""
    config = DB_CONFIG.copy()
    if with_db:
        config['database'] = DB_NAME
    return mysql.connector.connect(**config)


def execute_sql_file(cursor, filepath):
    """Đọc và thực thi file SQL"""
    print(f"📄 Đang đọc file: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Tách các câu lệnh SQL
    statements = []
    current_statement = ''
    
    for line in sql_content.split('\n'):
        # Bỏ qua comment và dòng trống
        stripped = line.strip()
        if stripped.startswith('--') or stripped == '':
            continue
        
        current_statement += line + '\n'
        
        if stripped.endswith(';'):
            statements.append(current_statement.strip())
            current_statement = ''
    
    # Thực thi từng câu lệnh
    success_count = 0
    error_count = 0
    
    for i, stmt in enumerate(statements):
        try:
            # Bỏ qua SET statements đã xử lý ở đầu
            if stmt.upper().startswith('SET '):
                cursor.execute(stmt)
                continue
            
            cursor.execute(stmt)
            
            # Đếm các INSERT
            if stmt.upper().startswith('INSERT'):
                success_count += cursor.rowcount
            elif stmt.upper().startswith('CREATE'):
                table_name = ''
                parts = stmt.split('`')
                if len(parts) >= 2:
                    table_name = parts[1]
                print(f"  ✅ Tạo bảng: {table_name}")
            elif stmt.upper().startswith('DROP'):
                pass  # Im lặng cho DROP
            elif stmt.upper().startswith('USE'):
                print(f"  ✅ Sử dụng database: {DB_NAME}")
            elif stmt.upper().startswith('SELECT'):
                result = cursor.fetchone()
                if result:
                    values = list(result.values()) if isinstance(result, dict) else list(result)
                    print(f"  📊 {values[0]}")
                    
        except Exception as e:
            error_count += 1
            # Chỉ hiện lỗi quan trọng
            if 'Duplicate' not in str(e) and 'already exists' not in str(e):
                print(f"  ⚠️ Cảnh báo ở statement {i+1}: {str(e)[:100]}")
    
    print(f"\n✅ Đã thực thi {len(statements)} câu lệnh SQL")
    print(f"📊 Tổng records được thêm: {success_count}")
    if error_count > 0:
        print(f"⚠️ Có {error_count} cảnh báo (có thể do dữ liệu đã tồn tại)")


def main():
    """Chạy setup database"""
    print("=" * 50)
    print("🚀 BẮT ĐẦU SETUP DATABASE")
    print("=" * 50)

    try:
        # Tìm file database.sql
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(script_dir, 'database.sql')
        
        if not os.path.exists(sql_file):
            print(f"❌ Không tìm thấy file: {sql_file}")
            print("💡 Hãy đảm bảo file database.sql nằm cùng thư mục với setup_database.py")
            return
        
        # Bước 1: Kết nối MySQL
        print("\n📌 Bước 1: Kết nối MySQL (port 3307)...")
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Set charset
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        
        # Bước 2: Thực thi file SQL
        print("\n📌 Bước 2: Thực thi file database.sql...")
        execute_sql_file(cursor, sql_file)
        conn.commit()
        
        cursor.close()
        conn.close()

        print("\n" + "=" * 50)
        print("🎉 SETUP HOÀN TẤT!")
        print("=" * 50)
        print(f"📦 Database: {DB_NAME}")
        print(f"🔗 Host: localhost:{DB_CONFIG['port']}")
        print(f"👤 User: {DB_CONFIG['user']}")
        print("=" * 50)
        print("\n💡 Bạn cũng có thể import file database.sql trực tiếp vào phpMyAdmin!")

    except Error as e:
        print(f"\n❌ Lỗi MySQL: {e}")
        print("\n💡 Hãy kiểm tra:")
        print("   1. XAMPP đã bật MySQL service chưa?")
        print("   2. MySQL chạy trên port 3307?")
        print("   3. User 'root' không password?")
        raise


if __name__ == '__main__':
    main()
