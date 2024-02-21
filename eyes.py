import cv2
import time
import mediapipe as mp
import RPi.GPIO as gp
import picamera2
import math

class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def normalize(self):
        norm = math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
        return Point(self.x / norm, self.y / norm, self.z / norm)

chan_list = [7, 11, 12]

IMAGE_WIDTH = 240
IMAGE_HEIGHT = 320
REF_DISTANCE = 2.80
REF_WIDTH = 2.87 
DISTANCE = -0.44

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


def cal_Point(image_width, image_height, ref_width, ref_distance, img_x, img_y):
    ratio = image_width / image_height
    c_x = image_width / 2.0
    c_y = image_height / 2.0
    x_norm = img_x - c_x
    y_norm = c_y - img_y
    factor = ref_width / image_width / ref_distance
    x_ref = x_norm * factor * DISTANCE
    y_ref = y_norm * factor * DISTANCE
    return Point(x_ref, DISTANCE, -y_ref)

def set_camera(CAM) :
    gp.output(chan_list, SETTING[CAM])

init_camera()
left_eye = (0, 0)
right_eye = (0, 0)

set_camera("A")
picam2 = picamera2.Picamera2()
picam2.start()

mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)

def get_face_mesh(image):
    results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not results.multi_face_landmarks:
        return image, (0, 0), (0, 0)

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

left_eye_point = Point(0, 0, 0)
right_eye_point = Point(0, 0, 0)

while True:
    s = time.time()
    start = time.perf_counter()
    image = picam2.capture_array()
    image = cv2.flip(image, 0)
    image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    image = cv2.resize(image, (240, 320))


    image, left_eye, right_eye = get_face_mesh(image)
    e = time.time()
    fps = 1/(e-s)
    cv2.putText(image, f"FPS: {fps:.2f}", (10, 30), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(image, f"Left Eye: {left_eye}", (10, 60), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(image, f"Right Eye: {right_eye}", (10, 90), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow('frame', image)

    

    left_eye_point = cal_Point(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, left_eye[0], left_eye[1])
    right_eye_point = cal_Point(IMAGE_WIDTH, IMAGE_HEIGHT, REF_WIDTH, REF_DISTANCE, right_eye[0], right_eye[1])

    print((left_eye_point.x, left_eye_point.y, left_eye_point.z), (right_eye_point.x, right_eye_point.y, right_eye_point.z))


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    
