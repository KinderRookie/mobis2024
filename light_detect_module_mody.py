from picamera2 import Picamera2
# import stereo_cam
import RPi.GPIO as gp
import time
import cv2
import math
import socket
import json

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
REF_DISTANCE = 2.80
REF_WIDTH = 2.87

CAM_POINT_A = (-0.13, 0.115, -0.14)
CAM_POINT_B = (0.13, 0.115, -0.14)

host='192.168.0.102'
port = 5000



def send_3d_point(host, port, point):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))

        # Convert the point to a JSON string
        data = json.dumps(point)
        client_socket.sendall(data.encode('utf-8'))
        
    except Exception as e:
        print(e)
    finally:
        client_socket.close()

class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def normalize(self):
        norm = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
        return Point(self.x / norm, self.y / norm, self.z / norm)

class Line:
    def __init__(self, point, dir):
        self.point = point
        self.dir = dir

def cross_product(a, b):
    return Point(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x)

def dot_product(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z

def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)

def find_closest_points(l1, l2):
    n = cross_product(l1.dir, l2.dir)
    norm = dot_product(n, n)
    if abs(norm) < 1e-8:
        return False, None, None
    diff = Point(l2.point.x - l1.point.x, l2.point.y - l1.point.y, l2.point.z - l1.point.z)
    t1 = dot_product(cross_product(diff, l2.dir), n) / norm
    t2 = dot_product(cross_product(diff, l1.dir), n) / norm
    p1 = Point(l1.point.x + l1.dir.x * t1, l1.point.y + l1.dir.y * t1, l1.point.z + l1.dir.z * t1)
    p2 = Point(l2.point.x + l2.dir.x * t2, l2.point.y + l2.dir.y * t2, l2.point.z + l2.dir.z * t2)
    return True, p1, p2


def cal_vector(image_width, image_height, ref_width, ref_distance, img_x, img_y, theta_x, theta_y):
    ratio = image_width / image_height
    c_x = image_width / 2.0
    c_y = image_height / 2.0
    x_norm = img_x - c_x
    y_norm = c_y - img_y
    factor = ref_width / image_width
    x_ref = x_norm * factor
    y_ref = y_norm * factor
    #code for calibration. applying yaw, pitch angle
    
    x = x_ref
    y = ref_distance
    z = y_ref
    
    # x 축 회전
    rotated_x = x * math.cos(theta_x) - z * math.sin(theta_x)
    rotated_z = x * math.sin(theta_x) + z * math.cos(theta_x)
    
    # y 축 회전
    rotated_y = y * math.cos(theta_y) + rotated_z * math.sin(theta_y)
    rotated_z = -y * math.sin(theta_y) + rotated_z * math.cos(theta_y)
    
    return Point(rotated_x , rotated_y, rotated_z).normalize()


chan_list = [7, 11, 12]

SETTING = {
    "A": (False, False, True),
    "B": (True, False, True),
    "C": (False, True, False),
    "D": (True, True, False),
    "DISABLE": (False, True, True)
}

def init_camera(): 
        gp.setwarnings(False)
        gp.setmode(gp.BOARD)
        chan_list = [7, 11, 12]
        # Setup the stack layer 1 board
        gp.setup(chan_list, gp.OUT)
        gp.output(chan_list, True)
        gp.output(chan_list, False)
        set_camera("DISABLE")

def set_camera(CAM) :
    gp.output(chan_list, SETTING[CAM])

height, width = 240, 320


middle_point_A = None
middle_point_B = None


init_camera()
set_camera("A")
picam2 = Picamera2()

time.sleep(1)
middle_point_A = (0, 0)
middle_point_B = (0, 0)
time.sleep(1)
picam2.configure(picam2.create_still_configuration(main={"size": (width, height),"format": "BGR888"},buffer_count=2))
time.sleep(1)
picam2.start()
picam2.set_controls({"ExposureValue": -5.0, "AnalogueGain": 1})
time.sleep(2)
i = 1
while True:
    
    x, y, w, h = None, None, None, None
    start = time.perf_counter()
    if(i%2==0):
       set_camera("C")
    else:
       set_camera("A")
    i = i+1

    time.sleep(0.04)
    
    # 이미지 캡처
    image = picam2.capture_array()
    image = picam2.capture_array()

    print("capture")
    # flip the image
    #image = cv2.flip(image, 0)
    image = cv2.flip(image, 1)
    #if(i%2==0):
    #    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    #else:
    #    image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    
    # 그레이스케일 이미지로 변환
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 이진화 임계값을 설정하여 밝은 영역 검출
    _, threshold_image = cv2.threshold(gray_image, 225, 255, cv2.THRESH_BINARY)
    
    # 이진화된 이미지에서 윤곽선 찾기
    contours, _ = cv2.findContours(threshold_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # 윤곽선을 둘러싸는 최소 크기 사각형 계산
        x, y, w, h = cv2.boundingRect(contour)
        
        # 검출된 영역의 크기에 대한 임계값 설정
        if w*h > 100:  # 조건을 만족하는 영역만 표시
            # 원본 이미지에 밝은 영역 표시
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            


            if i % 2 == 0:
                middle_point_B = (x + (w / 2), y + (h / 2))
                middle_point_B = int(middle_point_B[0]), int(middle_point_B[1])
            else:
                middle_point_A = ((x + w / 2), y + (h / 2))
                middle_point_A = int(middle_point_A[0]), int(middle_point_A[1])
            
            break
            




    # 결과 이미지 표시
    if(i%2==0):
         cv2.imshow("Bright Sources Detection"+"B", image)
    else:
         cv2.imshow("Bright Sources Detection", image)

    #if middle_point_A is not None and middle_point_B is not None:
        #print(get_mid_point(middle_point_A, middle_point_B, 0.157, 0.0036))
    print(w, h)
    if w == None or h == None:
        print("fail")
        send_3d_point(host, port, {"x": 0, "y": 0, "z": 0})
        continue     
    

    print(middle_point_A, middle_point_B)
    end = time.perf_counter()
    #print(f"{end - start:0.5f}")
    print(1/(end - start))

    print("start find_closest_points")
    l1 = Line(Point(*CAM_POINT_A), cal_vector(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, middle_point_A[0], middle_point_A[1],0.0512,0.0735))
    l2 = Line(Point(*CAM_POINT_B), cal_vector(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, middle_point_B[0], middle_point_B[1],0.0256,0.0128))
  #  l1 = Line(Point(*CAM_POINT_A), cal_vector(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, middle_point_A[0], middle_point_A[1],0,0))
   # l2 = Line(Point(*CAM_POINT_B), cal_vector(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, middle_point_B[0], middle_point_B[1],0,0))
    success, p1, p2 = find_closest_points(l1, l2)

    if success:
        print("success")
        print(-(p1.x+p2.x)/2, (p1.y+p2.y)/2, (p1.z+p2.z)/2)
        send_3d_point(host, port, {"x": -(p1.x+p2.x)/2, "y": (p1.y+p2.y)/2, "z": (p1.z+p2.z)/2})
    else:
        print("fail")
        send_3d_point(host, port, {"x": 0, "y": 0, "z": 0})
        

    time.sleep(0.01)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



# 작업 완료 후 자원 해제
cv2.destroyAllWindows()
picam2.stop()
