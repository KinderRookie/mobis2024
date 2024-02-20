from picamera2 import Picamera2
# import stereo_cam
import RPi.GPIO as gp
import time

import cv2


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

def get_mid_point(point_A, point_B, baseline, focal_length):
    if point_A is None or point_B is None:
        return None

    x1, y1 = point_A
    x2, y2 = point_B

    # calculate the distance from the image plane to the object plane
    Z = baseline * focal_length / (x1 - x2)

    # calculate the x, y coordinate of the object
    X = Z * (x1 - focal_length) / focal_length
    Y = Z * (y1 - baseline / 2) / focal_length

    return  (X, Y, Z)




def set_camera(CAM) :
    gp.output(chan_list, SETTING[CAM])

height, width = 240, 320
center_x = width // 2
center_y = height // 2

middle_point_A = None
middle_point_B = None


init_camera()
set_camera("A")
picam2 = Picamera2()

time.sleep(1)

time.sleep(1)
picam2.configure(picam2.create_still_configuration(main={"size": (320, 240),"format": "BGR888"},buffer_count=2))
time.sleep(1)
picam2.start()
picam2.set_controls({"ExposureValue": -2.0, "AnalogueGain": 1})
time.sleep(5)

i = 1

while True:
    

    print("*"+str(i)+"*")
    start = time.perf_counter()
    if(i%2==0):
       set_camera("C")
       print("C")
    else:
       set_camera("A")
       print("A")
    i = i+1

    time.sleep(0.03)
    
    # 이미지 캡처
    image = picam2.capture_array()
    image = picam2.capture_array()

    print("capture")
    # flip the image
    image = cv2.flip(image, 0)
    image = cv2.flip(image, 1)
    
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
        if w*h > 500:  # 조건을 만족하는 영역만 표시
            # 원본 이미지에 밝은 영역 표시
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            middle_x = x + w // 2
            middle_y = y + h // 2

            relative_x = middle_x - center_x
            relative_y = middle_y - center_y

            if i % 2 == 0:
                middle_point_B = (relative_x, relative_y)
            else:
                middle_point_A = (relative_x, relative_y)
            
            
            break
    print("opencv")
    # 결과 이미지 표시
    if(i%2==0):
        cv2.imshow("Bright Sources Detection"+"B", image)
    else:
        cv2.imshow("Bright Sources Detection", image)

    #if middle_point_A is not None and middle_point_B is not None:
        #print(get_mid_point(middle_point_A, middle_point_B, 0.157, 0.0036))


    end = time.perf_counter()
    #print(f"{end - start:0.5f}")
    print(1/(end - start))
    
    print("**")
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



# 작업 완료 후 자원 해제
cv2.destroyAllWindows()
picam2.stop()