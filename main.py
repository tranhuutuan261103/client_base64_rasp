import cv2
import socketio
import base64
from io import BytesIO
from PIL import Image
import signal
import sys

# Khởi tạo client
sio = socketio.Client()

# Sự kiện khi kết nối thành công
@sio.event
def connect():
    print("Connected to the server")
    sio.emit('start_recording', {'message': 'Start recording video', 'system_id': 'iot_01'})

# Sự kiện khi kết nối thất bại
@sio.event
def connect_error(data):
    print(f"Error connecting to the server: {data}")

# Sự kiện khi nhận được phản hồi từ server
@sio.event
def response(data):
    print("Received response from server:", data)

@sio.on('detection_result')
def detection_result(data):
    print("\nReceived detection result:", data)

@sio.on('error')
def error(data):
    print("\nReceived error:", data)

# Mở webcam và truyền video
cap = cv2.VideoCapture(0)  # Mở webcam mặc định
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Kiểm tra nếu webcam mở thành công
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

# Hàm để gọi stop_recording và thoát chương trình
def stop_recording_and_exit(signal, frame):
    print("\nStop recording and exiting...")
    sio.emit('stop_recording', {'message': 'Stop recording video', 'system_id': 'iot_01'})
    cap.release()
    cv2.destroyAllWindows()
    sio.disconnect()  # Disconnect WebSocket client
    sys.exit(0)

# Bắt tín hiệu Ctrl+C để gọi stop_recording và thoát
signal.signal(signal.SIGINT, stop_recording_and_exit)

# Kết nối tới server WebSocket
try:
    print("Connecting to server...")
    sio.connect('http://127.0.0.1:5123')
    print("Successfully connected to the server")
except Exception as e:
    print(f"Failed to connect to the server: {e}")
    sys.exit(1)

# Truyền video qua WebSocket
print("Streaming video...")
while True:
    # Đọc một khung hình từ webcam
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture image")
        break
    
    # Chuyển đổi khung hình từ BGR (OpenCV) sang RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Chuyển frame thành ảnh PIL để xử lý base64
    pil_image = Image.fromarray(rgb_frame)
    
    # Chuyển đổi hình ảnh thành base64
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    # Thêm tiền tố 'data:image/jpeg;base64,' vào chuỗi base64
    img_base64_with_prefix = f"data:image/jpeg;base64,{img_base64}"
    print(".", end="", flush=True)  # In dấu chấm mỗi khi gửi hình ảnh
    
    # Gửi hình ảnh qua WebSocket mỗi khi có khung hình
    sio.emit('video', {'image': img_base64_with_prefix, 'system_id': 'iot_01'})
