"""
wow_detect.py
world of warcraft auto fishing system

author: jahyun koo (jhkoo77@gmail.com)
date: 2026
license: MIT License
copyright: (c) 2026 jhkoo77@gmail.com
"""



# title of the wow window
WOW_WINDOW_TITLE = "월드 오브 워크래프트"
# delay time for pull force
PULL_DELAY = 5
# delay time for capture image
CAPTURE_DELAY = .02

# minimum number of distance ratios to check if something happened
MININUM_DISTANCE_COUNT = 5

# delay time for casting
CASTING_DELAY = 1

# casting slot number
CASTING_SLOT_NUMBER = '1'

# model path
MODEL_PATH = './Data/Model_Weights/trained_weights_final.h5'
# anchors path
ANCHORS_PATH = './Data/Model_Weights/yolo_anchors.txt'
# classes path
CLASSES_PATH = './Data/Model_Weights/data_classes.txt'



import sys

sys.path.append('E:\\wowbot\\TrainYourOwnYOLO2\\2_Training\\src\\keras_yolo3')
sys.path.append('E:\\wowbot\\TrainYourOwnYOLO2\\2_Training\\src\\keras_yolo3\\')


from yolo import YOLO
import pyautogui



import time
from datetime import datetime
import cv2
import numpy as np
import win32con
import win32gui
import win32ui
import win32api
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

from util import Point, Rect

yolo_modelo = None


class BobberInfo:
    """
    Information class for fishing bobber (낚시찌).
    
    Attributes:
        at (datetime): Detection timestamp
        box (Rect): Bounding box of the bobber
    """
    at = datetime.now();
    box = Rect(0, 0, 0, 0);

    def __init__(self):
        """Initialize bobber info with default values."""
        pass

    def init(self, box):
        """
        Initialize bobber info with detection box.
        
        Args:
            box: Bounding box rectangle of the detected bobber
        """
        self.at = datetime.now()
        self.box = box


def captureTargetWindow(title):
    """
    Capture the target window and return the image and window handle.
    
    Args:
        title: Title of the target window
        
    Returns:
        Image and window handle
    """
    hwnd = findTargetWindow(title);
    if hwnd == None:
        print(f'>> ERROR :: not found target window {title}')
        exit(1)

    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bot - top


    hdesktop = win32gui.GetDesktopWindow()
    hwndDC = win32gui.GetWindowDC(hdesktop)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    result = saveDC.BitBlt((0, 0), (w, h), mfcDC, (left, top), win32con.SRCCOPY)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hdesktop, hwndDC)

    return im, hwnd;


def sendKey(hwnd, ch):
    win32gui.SetForegroundWindow(hwnd)
    win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, ord(ch), 0)
    time.sleep(.1)
    win32api.SendMessage(hwnd, win32con.WM_KEYUP, ord(ch), 0)


def init_yolo():
    global yolo_modelo;
    yolo_modelo = YOLO(model_path=MODEL_PATH,
                       anchors_path=ANCHORS_PATH,
                       classes_path=CLASSES_PATH)


def detect_bobber(img):
    """
    Detect fishing bobber (낚시찌) in the image using YOLO model.
    
    Args:
        img: Image to detect bobber in
        
    Returns:
        Detection results or None if no bobber detected
    """
    detected_info = yolo_modelo.detect_image(img, show_stats=False)
    dim = detected_info[0]
    if len(dim) == 0:
        return None;

    return dim;



def findTargetWindow(title):
    """
    Find the target window by title.
    
    Args:
        title: Title of the target window
        
    Returns:
        Window handle or None if not found
    """
    def callback(hwnd, hwnd_list: list):
        """
        Callback function to find the target window.
        
        Args:
            hwnd: Window handle
            hwnd_list: List of window handles
        """
        target_title = win32gui.GetWindowText(hwnd)
        if target_title.find(title) != -1:
            hwnd_list.append((title, hwnd))
        return True;

    # initialize window handle list
    hwnd_list = []

    # enumerate all windows and find the target window
    win32gui.EnumWindows(callback, hwnd_list)
    if len(hwnd_list) == 0:
        return None;

    # return the first window handle
    hwnd = hwnd_list[0][1]
    return hwnd;


def pull_force(bobber_info, hwnd):
    """
    Pull the fishing line when bobber (낚시찌) movement is detected.
    
    Args:
        bobber_info: BobberInfo object containing bobber position
        hwnd: Window handle
    """
    print(bobber_info)
    print(f'pull force------------------------')
    
    # get the window rectangle
    w_rc = win32gui.GetWindowRect(hwnd)
    # get the client point of the bobber
    # subtract 32 pixels from the y coordinate to get the click point
    pt_x, pt_y = win32gui.ClientToScreen(hwnd, (int(bobber_info.box.center().x), int(bobber_info.box.center().y) - 32))

    print(f'window rc = {w_rc}, bobber center = {bobber_info.box.center()}, click point = {(pt_x, pt_y)}')

    #pyautogui.click(x=pt_x, y=pt_y, button='right')
    # move to the bobber and pull the fishing line
    pyautogui.moveTo(pt_x, pt_y)
    pyautogui.rightClick()
    time.sleep(PULL_DELAY)


def casting():
    """
    Cast the fishing line.
    """
    hwnd = findTargetWindow(WOW_WINDOW_TITLE)
    # send the key to the window to cast the fishing line
    sendKey(hwnd, CASTING_SLOT_NUMBER)
    # wait for the casting to complete
    time.sleep(CASTING_DELAY)


def showDetectStatus(img, info):
    draw = ImageDraw.Draw(img);
    if info != None:
        draw.rectangle(info.box.list(), outline=(255, 128, 128))
        draw.rectangle(Rect.from_point(info.box.center(), 2).list(), fill=(0, 255, 0),
                       outline=(255, 0, 0))

    numpy_image = np.array(img)
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    cv2.imshow("PIL2OpenCV", opencv_image)
    cv2.waitKeyEx(1)


def is_something_happend(cur_dist_ratio, dists):
    """
    Check if something happened based on the current distance ratio and previous distance ratios.
    
    Args:
        cur_dist_ratio: Current distance ratio
        dists: List of previous distance ratios
        
    Returns:
        True if something happened, False otherwise
    """

    # if the number of previous distance ratios is less than 5, return False
    if len(dists) < MININUM_DISTANCE_COUNT:
        return False

    # calculate the average of the previous distance ratios
    avrage = .0
    
    for dist in dists:
        avrage = avrage + dist
    avrage = avrage / (len(dists))

    # if the current distance ratio is greater than the average of the previous distance ratios * 6, return True
    print(f'>> check dist info = {cur_dist_ratio}, avr = {avrage}')

    if cur_dist_ratio > (avrage * 6):
        print(f'>> something happened !! dist = {cur_dist_ratio}, avr = {avrage}')
        return True;

    return False


def run_fishing_cycle():
    capture_img, hwnd = captureTargetWindow(WOW_WINDOW_TITLE)
    detected_result = detect_bobber(capture_img.copy());

    if detected_result is None:
        print(f'>> ERROR :: bobber not detect !! casting...........')
        casting();

    # initialize previous bobber information
    prev_bobber_info = BobberInfo();

    # initialize distance log
    dist_log = []
    while True:

        time.sleep(CAPTURE_DELAY)

        # initialize current bobber information
        cur_bobber_info = BobberInfo()

        capture_img, hwnd = captureTargetWindow(WOW_WINDOW_TITLE)
        detected_result = detect_bobber(capture_img.copy());

        if detected_result is None:

            showDetectStatus(capture_img, None)
            last_found_bobber_before = (datetime.now() - prev_bobber_info.at).total_seconds()
            if last_found_bobber_before >= 3:
                break
            continue

        cur_box = Rect(detected_result[0][0], detected_result[0][1], detected_result[0][2], detected_result[0][3])
        cur_bobber_info.init(cur_box)
        
        # calculate distance ratio
        showDetectStatus(capture_img, cur_bobber_info);
        
        prev_box = prev_bobber_info.box
        cur_box = cur_bobber_info.box

        union_box = prev_box.union(cur_box)
        dist_pt = prev_box.center().dist(cur_box.center())

        hor_dist_ratio = dist_pt / union_box.width() * 100.0
        ver_dist_ratio = dist_pt / union_box.height() * 100.0

        #vertical distance ratio is more important than horizontal distance ratio
        dist_ratio = ver_dist_ratio #(hor_dist_ratio ** 2 + ver_dist_ratio **2) ** .5;


        if is_something_happend(dist_ratio, dist_log) is True:
            time.sleep(.5)
            pull_force(cur_bobber_info, hwnd)
            break;

        dist_log.append(dist_ratio)
        prev_bobber_info = cur_bobber_info;


def test():
    hwnd = findTargetWindow(WOW_WINDOW_TITLE)
    wrc = win32gui.GetWindowRect(hwnd)
    print(wrc)
    client_pt = win32gui.ClientToScreen(hwnd, (10, 10))
    print(client_pt)
    exit(1)


def start():
    init_yolo();

    while True:
        run_fishing_cycle();
        time.sleep(1)



if __name__ == "__main__":
    start();
