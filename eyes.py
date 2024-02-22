import cv2
import time
import mediapipe as mp
import RPi.GPIO as gp
import picamera2
import math
import socket
import threading
import json



display_lock = threading.Lock()

last_update_time = 0
MIN_UPDATE_DELAY = 0.01
row = [0b10000000,0b01000000,0b00100000,0b00010000,0b00001000,0b00000100,0b00000010,0b00000001]
#col = [0b0101011100010111,0b0101000100010001,0b0101000100010001,0b0101000100010001,0b0101010100010101,0b0101010100010101,0b0101010100010101,0b0111011101110111]
#col = [0x00,0x00,0b0010000000000000,0x00,0x00,0x00,0x00,0x00]
col = [0b0101011100010111,0b0101000100010001,0b0101000100010001,0b0101000100010001,0x00,0x00,0x00,0x00]
class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def normalize(self):
        norm = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
        return Point(self.x / norm, self.y / norm, self.z / norm)

left_eye_point = Point(0, 0, 0)
right_eye_point = Point(0, 0, 0)

def defalut_mode():
    '''
     # either coords of eyes or light source is not detected
    col = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
    refresh_display(col)
'''
    pass
def line_3d(point_light, point_left_eye):
    x1, y1, z1 = point_light.x, point_light.y, point_light.z
    x2, y2, z2 = point_left_eye.x, point_left_eye.y, point_left_eye.z
    def point_on_line(t):
        x = x1+t*(x2-x1)
        y = y1+t*(y2-y1)
        z = z1+t*(z2-z1)
        
        return (x,y,z)
        
    return point_on_line
    
def socket_server():
    point_on_plane_left = None
    point_on_plane_right = None
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '192.168.0.107'
    port = 5000
    server_socket.bind((host, port))
    server_socket.listen(1)
    print("Server is waiting for a connection...")
    global col ###

    client_socket, address = server_socket.accept()
    print(f"Connected to {address}")

    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            # Parse the JSON string
            point = json.loads(data)
            print(f"Received 3D point from client: {point}")
            
            # Process the 3D point here
            point_light = Point(point['x'], point['y'], point['z'])
            if point_light.x == 0 and point_light.y == 0 and point_light.z == 0:
                defalut_mode()
                continue
            point_left_eye = left_eye_point
            point_right_eye = right_eye_point

            #  connect two points 2 times
            line_function_left = line_3d(point_light, point_left_eye)
            line_function_right = line_3d(point_light, point_right_eye)
            if point_light.y != point_left_eye.y and point_light.y != point_right_eye.y:
                t_left = point_light.y / (point_light.y - point_left_eye.y)
                t_right = point_light.y / (point_light.y - point_right_eye.y)
            else:
                defalut_mode()
                continue
                


            point_on_plane_left = line_function_left(t_left)
            point_on_plane_right = line_function_right(t_right)

            
            print(point_on_plane_left)
            print(point_on_plane_right)
            

        except ConnectionResetError:
            print("Connection was lost")
            break

    client_socket.close()
    server_socket.close()
    if point_on_plane_left == None or point_on_plane_right == None:
        return
    
    metric_x_left = round(point_on_plane_left[0] * 100 / 2.54 * (-1), 0)
    metric_z_left = round(point_on_plane_left[2] * 100 / 2.54 *(-1), 0)
    metric_x_right = round(point_on_plane_right[0] * 100 / 2.54 * (-1), 0)
    metric_z_right = round(point_on_plane_right[2] * 100 / 2.54 *(-1), 0)

    col = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
    
    for i in range(0, 16):
        for j in range(0,8):
            if(i == metric_x_left + 8 and j == metric_z_left + 4):
                col[j] = 0b1111111111111111 & (1 << (15-i))
                break

    for i in range(0, 16):
        for j in range(0,8):
            if(i == metric_x_right + 8 and j == metric_z_right + 4):
                col[j] = col[j]|(0b1111111111111111 & (1 << (15-i)))
                break
    
    
    refresh_display(col)
    
    print("----------------------------------------------------------")
    print(metric_x_left, metric_z_left)
    print(metric_x_right, metric_z_right)
    print("----------------------------------------------------------")                
                
    

#threading.Thread(target=socket_server).start()


chan_list = [7, 11, 12]

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
REF_DISTANCE = 2.80
REF_WIDTH = 2.87 
DISTANCE = -0.6


dataPin = 16
latchPin = 6
clockPin = 5

gp.setmode(gp.BCM)
gp.setup((dataPin,latchPin,clockPin),gp.OUT)


MSBFIRST = 1
LSBFIRST = 2

def shiftOut(dataPin, clockPin, bitOrder, val, bits):
	for i in range(bits):
		if bitOrder == MSBFIRST:
			bit = (val & (1 << (bits -1 -i))) >> (bits -1 -i)
		else:
			bit = (val & (1 <<i)) >>i
			
		gp.output(dataPin,bit)
		gp.output(clockPin, gp.HIGH)
		time.sleep(0.00001)
		gp.output(clockPin, gp.LOW)
		

def  refresh_display(col):
    
    global last_update_time
    current_time = time.time()
    if current_time - last_update_time < MIN_UPDATE_DELAY:
        threading.join_thread()
        return
        
    with display_lock:
        for i in range(8):
            gp.output(latchPin,gp.LOW)
            shiftOut(dataPin,clockPin,LSBFIRST,col[i],16)
            shiftOut(dataPin,clockPin,LSBFIRST,row[i],8)
            gp.output(latchPin,gp.HIGH)
            time.sleep(0.001)
            
            
            '''
    for i in range(8):
        gp.output(latchPin,gp.LOW)
        shiftOut(dataPin,clockPin,LSBFIRST,col[i],16)
        shiftOut(dataPin,clockPin,LSBFIRST,row[i],8)
        gp.output(latchPin,gp.HIGH)
        time.sleep(0.00001)
        '''
    
    
    last_update_time = current_time
    
    '''
    gp.output(latchPin,gp.LOW)
    shiftOut(dataPin,clockPin,LSBFIRST,0x00,8)
    shiftOut(dataPin,clockPin,LSBFIRST,0x00,16)
    gp.output(latchPin,gp.HIGH)
    '''
    time.sleep(0.00001)
    

def cal_Point(image_width, image_height, ref_width, ref_distance, img_x, img_y):
    ratio = image_width / image_height
    c_x = image_width / 2.0
    c_y = image_height / 2.0
    x_norm = img_x - c_x
    y_norm = c_y - img_y
    factor = ref_width / image_width / ref_distance
    x_ref = x_norm * factor * DISTANCE
    y_ref = y_norm * factor * DISTANCE
    return Point(x_ref, DISTANCE-0.1, -y_ref-0.12)


left_eye = (0, 0)
right_eye = (0, 0)


picam2 = picamera2.Picamera2()
picam2.start()

mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)

def get_face_mesh(image):
    results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not results.multi_face_landmarks:
        return image, (0,0), (0,0)

    annotated_image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)  # Fix: Convert image channel from RGBA to RGB

    # for face_landmarks in results.multi_face_landmarks:
    #     mp_drawing.draw_landmarks(annotated_image, face_landmarks, mp_face_mesh.FACEMESH_LEFT_EYE, landmark_drawing_spec=drawing_spec, connection_drawing_spec=drawing_spec)
    # return annotated_image
    for face_landmarks in results.multi_face_landmarks:
        left_eye_coord_1 = face_landmarks.landmark[159]
        left_eye_coord_2 = face_landmarks.landmark[145]
        right_eye_coord_1 = face_landmarks.landmark[386]    
        right_eye_coord_2 = face_landmarks.landmark[374]

        left_eye_x = (left_eye_coord_1.x + left_eye_coord_2.x) / 2
        left_eye_y = (left_eye_coord_1.y + left_eye_coord_2.y) / 2
        right_eye_x = (right_eye_coord_1.x + right_eye_coord_2.x) / 2
        right_eye_y = (right_eye_coord_1.y + right_eye_coord_2.y) / 2

        left_eye_x = int(left_eye_x * image.shape[1])
        left_eye_y = int(left_eye_y * image.shape[0])
        right_eye_x = int(right_eye_x * image.shape[1])
        right_eye_y = int(right_eye_y * image.shape[0])

        cv2.circle(annotated_image, (left_eye_x, left_eye_y), 5, (0, 255, 0), -1)
        cv2.circle(annotated_image, (right_eye_x, right_eye_y), 5, (0, 255, 0), -1)
        cv2.line(annotated_image, (left_eye_x, left_eye_y), (right_eye_x, right_eye_y), (0, 255, 0), 2)

        

    return annotated_image, (left_eye_x, left_eye_y), (right_eye_x, right_eye_y)

font = cv2.FONT_HERSHEY_SIMPLEX

def refresh_display_for_threading(col):
	while True:
		refresh_display(col=col)
	
'''
display_thread = threading.Thread(target=refresh_display_for_threading)
display_thread.start()
'''
while True:
    
    threading.Thread(target=socket_server).start()
    s = time.time()
    start = time.perf_counter()
    image = picam2.capture_array()
    #image = cv2.flip(image, 0)
    #image = cv2.flip(image, 1)
    #image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    image = cv2.resize(image, (IMAGE_WIDTH, IMAGE_HEIGHT))


    image, left_eye, right_eye = get_face_mesh(image)
    e = time.time()
    fps = 1/(e-s)
    cv2.putText(image, f"FPS: {fps:.2f}", (10, 30), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(image, f"Left Eye: {left_eye}", (10, 60), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(image, f"Right Eye: {right_eye}", (10, 90), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow('frame', image)

    
    if left_eye == (0, 0) and right_eye == (0, 0):
        defalut_mode()
        continue
    left_eye_point = cal_Point(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, left_eye[0], left_eye[1])
    right_eye_point = cal_Point(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, right_eye[0], right_eye[1])
    

    #print((left_eye_point.x, left_eye_point.y, left_eye_point.z), (right_eye_point.x, right_eye_point.y, right_eye_point.z))


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    
