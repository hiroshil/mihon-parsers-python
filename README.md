# LxHentai Manga Viewer & Downloader

Ứng dụng Python với giao diện Tkinter để xem và tải manga từ LxHentai/LXManga.

## Tính năng

- **Duyệt Manga**: Xem danh sách manga phổ biến và mới cập nhật
- **Tìm kiếm**: Tìm kiếm manga theo tên với các tùy chọn sắp xếp
- **Xem chi tiết**: Xem thông tin chi tiết về manga (tác giả, thể loại, mô tả, trạng thái)
- **Đọc trực tuyến**: Đọc manga trực tiếp trong ứng dụng với trình xem ảnh tích hợp
- **Tải xuống**: Tải các chapter về máy để đọc offline
- **Quản lý tải xuống**: Theo dõi tiến trình tải xuống với hàng đợi tải

## Cài đặt

### Yêu cầu
- Python 3.7 trở lên
- Tkinter (thường đã có sẵn với Python)

### Cài đặt các thư viện cần thiết

```bash
pip install -r requirements.txt
```

## Sử dụng

### Chạy ứng dụng

```bash
python lxhentai_viewer.py
```

### Hướng dẫn sử dụng

#### Tab Browse (Duyệt)
1. **Xem manga phổ biến**: Click nút "Popular"
2. **Xem manga mới nhất**: Click nút "Latest"
3. **Tìm kiếm**: Nhập từ khóa vào ô tìm kiếm và nhấn Enter hoặc click "Search"
4. **Sắp xếp**: Chọn cách sắp xếp từ dropdown menu
5. **Xem chi tiết**: Double-click vào manga trong danh sách

#### Tab Manga Details (Chi tiết)
1. **Xem thông tin**: Tác giả, thể loại, trạng thái, mô tả
2. **Danh sách chapter**: Hiển thị tất cả các chapter
3. **Đọc chapter**: Double-click vào chapter hoặc chọn và click "Read Selected"
4. **Tải chapter**: 
   - "Download Selected": Tải các chapter đã chọn
   - "Download All Chapters": Tải tất cả các chapter

#### Tab Reader (Đọc truyện)
1. **Điều hướng**: 
   - Click "Previous"/"Next" hoặc dùng phím mũi tên trái/phải
   - Xem số trang hiện tại ở giữa
2. **Tải chapter đang đọc**: Click "Download Chapter"
3. **Cuộn ảnh**: Sử dụng thanh cuộn nếu ảnh lớn

#### Tab Downloads (Tải xuống)
1. **Theo dõi tiến trình**: Xem trạng thái tải xuống
2. **Thư mục tải về**: Mặc định là ~/Downloads/LxHentai
3. **Đổi thư mục**: Click "Browse" để chọn thư mục khác
4. **Mở thư mục tải về**: Click "Open Download Folder"
5. **Xóa đã hoàn thành**: Click "Clear Completed"

### Phím tắt

- **Mũi tên trái**: Trang trước (trong Reader)
- **Mũi tên phải**: Trang sau (trong Reader)
- **Enter**: Tìm kiếm (trong ô tìm kiếm)
- **Double-click**: Xem chi tiết/Đọc chapter

## Cấu trúc thư mục tải về

```
~/Downloads/LxHentai/
├── [Tên Manga]/
│   ├── [Tên Chapter 1]/
│   │   ├── page_001.jpg
│   │   ├── page_002.jpg
│   │   └── ...
│   ├── [Tên Chapter 2]/
│   │   └── ...
│   └── ...
└── ...
```

## Lưu ý

1. **Kết nối Internet**: Cần có kết nối internet để tải manga
2. **Tốc độ tải**: Phụ thuộc vào kết nối mạng và server
3. **Dung lượng**: Mỗi chapter có thể chiếm 10-50MB tùy số trang
4. **Server**: Nếu không kết nối được, có thể server đã thay đổi địa chỉ

## Tính năng nâng cao

### Thay đổi server
Trong code, bạn có thể thay đổi base_url nếu server chính không hoạt động:

```python
# Trong file lxhentai_viewer.py
self.api = LxHentaiAPI(base_url="https://lxmanga.help")  # Thay đổi URL ở đây
```

### Tùy chỉnh giao diện
- Thay đổi kích thước cửa sổ trong `__init__`
- Điều chỉnh số lượng manga hiển thị mỗi trang
- Thay đổi thư mục tải về mặc định

## Xử lý lỗi

### Lỗi kết nối
- Kiểm tra kết nối internet
- Thử lại sau vài giây
- Kiểm tra xem server có hoạt động không

### Lỗi tải ảnh
- Một số ảnh có thể bị lỗi do server
- Thử tải lại chapter
- Kiểm tra dung lượng ổ cứng

### Lỗi hiển thị
- Cài đặt lại Pillow: `pip install --upgrade Pillow`
- Kiểm tra tkinter: `python -m tkinter`

## Miễn trừ trách nhiệm

Ứng dụng này chỉ dành cho mục đích học tập và nghiên cứu. Người dùng tự chịu trách nhiệm về việc sử dụng và tuân thủ luật bản quyền.

## Đóng góp

Mọi đóng góp và báo lỗi xin gửi về Issues trên GitHub.

## License

MIT License