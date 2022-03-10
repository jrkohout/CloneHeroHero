# colorpicking.py - small app to find best ranges for color segmentation

import cv2


callback_img = None


def color_mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # bgr - [0-255, 0-255, 0-255]
        # hsv - [0-179, 0-255, 0-255]
        bgr = callback_img[y, x, :]
        hsv = cv2.cvtColor(callback_img[y, x, :].reshape((1, 1, 3)), cv2.COLOR_BGR2HSV)
        print("BGR:", bgr, "  HSV:", hsv[0, 0, :])


def main():
    global callback_img
    cv2.namedWindow("amalg")
    cv2.setMouseCallback("amalg", color_mouse_callback)

    while True:
        callback_img = cv2.imread("screenshots/amalgamation.png")
        cv2.imshow("amalg", callback_img)

        if cv2.waitKey() == ord('q'):
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":
    main()
