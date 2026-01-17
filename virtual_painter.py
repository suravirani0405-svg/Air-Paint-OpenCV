import cv2
import numpy as np

# --- Camera setup ---
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# --- Canvas setup ---
canvas = np.zeros((720, 1280, 3), dtype=np.uint8)

# --- Default settings ---
brush_color = (0, 0, 255)  # Red drawing color
brush_size = 8
mode = "brush"  # brush | line | rect | circle | eraser
drawing = False
start_point = None
end_point = None

# --- HSV range for BLUE pen cap ---
lower_color = np.array([100, 150, 50])
upper_color = np.array([140, 255, 255])

x_prev, y_prev = 0, 0
kernel = np.ones((5, 5), np.uint8)

# --- Smooth point movement ---
def smooth_point(prev, new, alpha=0.3):
    if prev == 0:
        return new
    return int(prev * (1 - alpha) + new * alpha)

print("🎨 Air Painter Pro (Blue Pen Cap Edition)")
print("F=Brush | E=Eraser | L=Line | T=Rect | O=Circle | C=Clear | S=Save | Q=Quit")

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # --- Detect blue object ---
    mask = cv2.inRange(hsv, lower_color, upper_color)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (7, 7), 0)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    object_found = False

    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if 1500 < area < 25000:
            object_found = True
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w // 2, y + h // 2
            cx = smooth_point(x_prev, cx)
            cy = smooth_point(y_prev, cy)

            cv2.circle(frame, (cx, cy), 8, brush_color, -1)

            if mode == "brush":
                if x_prev == 0 and y_prev == 0:
                    x_prev, y_prev = cx, cy
                else:
                    cv2.line(canvas, (x_prev, y_prev), (cx, cy), brush_color, brush_size)
                    x_prev, y_prev = cx, cy

            elif mode == "eraser":
                if x_prev == 0 and y_prev == 0:
                    x_prev, y_prev = cx, cy
                else:
                    cv2.line(canvas, (x_prev, y_prev), (cx, cy), (0, 0, 0), brush_size * 3)
                    x_prev, y_prev = cx, cy

            elif mode in ["line", "rect", "circle"]:
                if not drawing:
                    start_point = (cx, cy)
                    drawing = True
                end_point = (cx, cy)

    # --- If object lost, finalize shape ---
    if not object_found:
        if drawing and start_point and end_point:
            if mode == "line":
                cv2.line(canvas, start_point, end_point, brush_color, brush_size)
            elif mode == "rect":
                cv2.rectangle(canvas, start_point, end_point, brush_color, brush_size)
            elif mode == "circle":
                radius = int(np.hypot(end_point[0] - start_point[0], end_point[1] - start_point[1]))
                cv2.circle(canvas, start_point, radius, brush_color, brush_size)
        drawing = False
        start_point = None
        end_point = None
        x_prev, y_prev = 0, 0

    # --- Live preview ---
    preview = canvas.copy()
    if drawing and start_point and end_point and mode in ["line", "rect", "circle"]:
        if mode == "line":
            cv2.line(preview, start_point, end_point, brush_color, brush_size)
        elif mode == "rect":
            cv2.rectangle(preview, start_point, end_point, brush_color, brush_size)
        elif mode == "circle":
            radius = int(np.hypot(end_point[0] - start_point[0], end_point[1] - start_point[1]))
            cv2.circle(preview, start_point, radius, brush_color, brush_size)

    combined = cv2.addWeighted(frame, 0.7, preview, 0.5, 0)

    # --- Display info ---
    mode_text = f"Mode: {mode.upper()} | Brush Size: {brush_size}"
    cv2.putText(combined, mode_text, (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.putText(combined,
        'R G B Y P = Colors | + - = Size | E = Eraser | C = Clear | L = Line | T = Rect | O = Circle | F = Brush | S = Save | Q = Quit',
        (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 255, 180), 2)

    cv2.imshow("🎨 Air Paint Pro - Blue Cap", combined)

    # --- Key Controls ---
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('c'):
        canvas[:] = 0
        print("🧹 Canvas cleared!")
    elif key == ord('s'):
        cv2.imwrite('My_Air_Paint_Art.png', canvas)
        print("✅ Drawing saved as My_Air_Paint_Art.png")

    # --- Colors ---
    elif key == ord('r'):
        brush_color = (0, 0, 255)
    elif key == ord('g'):
        brush_color = (0, 255, 0)
    elif key == ord('b'):
        brush_color = (255, 0, 0)
    elif key == ord('y'):
        brush_color = (0, 255, 255)
    elif key == ord('p'):
        brush_color = (255, 0, 255)

    # --- Brush size ---
    elif key in [ord('+'), ord('=')]:
        brush_size = min(brush_size + 2, 50)
    elif key in [ord('-'), ord('_')]:
        brush_size = max(2, brush_size - 2)

    # --- Modes ---
    elif key == ord('f'):
        mode = "brush"
    elif key == ord('e'):
        mode = "eraser"
    elif key == ord('l'):
        mode = "line"
    elif key == ord('t'):
        mode = "rect"
    elif key == ord('o'):
        mode = "circle"

cap.release()
cv2.destroyAllWindows()
