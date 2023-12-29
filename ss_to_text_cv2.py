import cv2,mss,os,pyperclip
from pytesseract import pytesseract,Output
import pandas as pd
pytesseract.tesseract_cmd = r"tesseract-ocr\tesseract.exe"

with mss.mss() as sct:
    sct.shot()

key=ord('a')
img=cv2.imread('monitor-1.png')
img2=img.copy()
drawing = False
x1,y1,x2,y2=0,0,0,0

def draw_rect(event, x, y, flags, param):
    global x1,y1,x2,y2,drawing,img,img2
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        x1, y1 = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            a, b = x, y
            if a != x & b != y:
                img = img2.copy()
                cv2.rectangle(img, (x1,y1),(x,y), (0, 0, 255), 2)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x2, y2 = x, y

cv2.namedWindow("main", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("main", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback("main", draw_rect)

while key not in (ord('w'),ord('W')):
    cv2.imshow("main",img)
    key = cv2.waitKey(1)&0xFF 

cv2.imwrite('snap.png',img2[y1:y2,x1:x2])
cv2.destroyAllWindows()
os.remove('monitor-1.png')
# pyperclip.copy(pytesseract.image_to_string('snap.png',timeout=5,lang='eng+ukr+rus').strip())


def extract_text(img):
    custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ukr+rus'
    df = pd.DataFrame(pytesseract.image_to_data(img, timeout=5, config=custom_config, output_type=Output.DICT))
    df1 = df[(df.conf!='-1')&(df.text!=' ')&(df.text!='')]
    for block in df1.groupby('block_num').first().sort_values('top').index.tolist():
        curr = df1[df1['block_num']==block]
        sel = curr[curr.text.str.len()>3]
        char_w = (sel.width/sel.text.str.len()).mean()
        prev_par, prev_line, prev_left = 0, 0, 0
        text = ''
        for ix, ln in curr.iterrows():
            if prev_par != ln['par_num']:
                text += '\n'
                prev_par = ln['par_num']
                prev_line = ln['line_num']
                prev_left = 0
            elif prev_line != ln['line_num']:
                text += '\n'
                prev_line = ln['line_num']
                prev_left = 0

            added = 0
            if ln['left']/char_w > prev_left + 1:
                added = int((ln['left'])/char_w) - prev_left
                text += ' ' * added 
            text += ln['text'] + ' '
            prev_left += len(ln['text']) + added + 1
        return text + '\n'

result = extract_text(img2[y1:y2,x1:x2]).strip()
pyperclip.copy(result)
print('Copied: \n' + result)
