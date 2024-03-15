# mobis2024
Hyundai MOBIS 2024 SW Hackerton Team GLGU's Github Repository
# Topic: Adaptive Wind Shield: Controlling modulized PNLC panel on vehicle's windshield for protecting driver's eye from hard light.


### GLGU.py
Code for controlling LED Matrix on prototype

### eyes.py
Code for detecting eyes and calculating 3d coordinate of real world.
1. Get 3d coordinate point of light source from **light_detect.py** via socket
2. Estimate 3d coordinate point of driver's eye using MediaPipe *face landmark detection* model.
3. Calculate vector expression of those two points(eye and light source) and get corresponding point on LED Matrix plane.

### light_detect.py
Code for detecting lights and calculating 3d coordinate of real world.
1. Using stereo camera for estimating depth of light source
2. Draw contours of light source in each camera using OpenCV and get mid_point of bounding box.
3. Calculate real world's coordinate and sent to eyes.py via socket
