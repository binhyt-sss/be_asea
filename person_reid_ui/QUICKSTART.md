# Person ReID UI - Quick Start

## 🚀 Chạy nhanh (3 bước)

### 1. Di chuyển vào thư mục UI
```powershell
cd person_reid_ui
```

### 2. Chạy script khởi động
```powershell
# Windows
.\start.ps1

# Linux/Mac
./start.sh
```

### 3. Mở trình duyệt
```
http://localhost:8501
```

---

## ⚙️ Cấu hình (tùy chọn)

### Cách 1: Sửa file config.yaml
```yaml
api:
  base_url: "http://your-api:8000"
```

### Cách 2: Dùng biến môi trường
```powershell
# Windows PowerShell
$env:PERSON_REID_API_URL = "http://your-api:8000"
.\start.ps1

# Linux/Mac
export PERSON_REID_API_URL="http://your-api:8000"
./start.sh
```

### Cách 3: Dùng file .env
```bash
# Copy template
cp .env.example .env

# Chỉnh sửa .env
PERSON_REID_API_URL=http://your-api:8000
```

---

## 🐳 Chạy với Docker

```bash
# Chỉnh sửa docker-compose.yml nếu cần
docker-compose up -d
```

---

## 📦 Cài đặt thủ công

```powershell
# 1. Tạo virtual environment
python -m venv venv

# 2. Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Chạy
streamlit run app.py
```

---

## ✅ Kiểm tra

### Test API connection
```powershell
# Check backend is running
curl http://localhost:8000/health
```

### Test UI
```
http://localhost:8501
```

---

## 🎯 Tính năng

- **👥 Users**: Quản lý người dùng
- **🗺️ Zones**: Quản lý khu vực  
- **🚨 Alerts**: Cảnh báo real-time
- **📈 Statistics**: Thống kê phân tích

---

## 🔧 Troubleshooting

### UI không kết nối được API?
```powershell
# Kiểm tra backend
curl http://localhost:8000/health

# Kiểm tra config
cat config.yaml
```

### Lỗi import?
```powershell
# Reinstall dependencies
pip install -r requirements.txt
```

### Port 8501 đã được dùng?
```powershell
# Đổi port
streamlit run app.py --server.port 8502
```

---

## 📚 Tài liệu đầy đủ

- `README.md` - Hướng dẫn chi tiết
- `MIGRATION.md` - Hướng dẫn migration
- `config.yaml` - Tất cả cấu hình

---

## 🎨 Độc lập hoàn toàn

Module UI này:
- ✅ Không phụ thuộc backend code
- ✅ Chỉ cần API URL
- ✅ Có thể chạy ở repo riêng
- ✅ Deploy độc lập
- ✅ Docker ready

---

**Chúc bạn sử dụng thành công! 🎉**
