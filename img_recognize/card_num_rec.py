import cv2

def is_axis_right(num,axis,error):
    if (axis - error) <= num <= (axis + error):
        return True
    else:
        return False

card_img_gray = cv2.imread('images/credit_card_05.png',0)
card_img_ = cv2.imread('images/credit_card_05.png')
num_img = cv2.imread('images/ocr_a_reference.png',0)

# card_canny = cv2.Canny(card_img_gray,150,220)
card_img_gray[card_img_gray<=150] = 50
_,card_canny = cv2.threshold(card_img_gray,0,255,cv2.THRESH_BINARY|cv2.THRESH_OTSU)
card_canny = card_canny[:int((card_canny.shape[0])*0.7)]
# kernel = np.ones((2,2),dtype=np.uint8)
# card_canny = cv2.dilate(card_canny,kernel,iterations=1)
binary,contours,_ = cv2.findContours(card_canny,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
num_in_card = []
count_dict = {}
import pandas as pd
for index,cnt in enumerate(contours):
    x,y,w,h = cv2.boundingRect(cnt)
    num_in_card.append((x, y, w, h))
    count_dict[index] = h
num_in_card = sorted(num_in_card,key=lambda x:x[1],reverse=True)
print(num_in_card)
count = 0
error_num_h = 3
error_num_y = 10
series = pd.Series(list(count_dict.values()))

num_h_list = []
for val in series.unique():
    if series[series == val].count() >= 10:
        for item in num_in_card:
            if item[3] == val:
                for item_s in num_in_card:
                    if is_axis_right(item_s[1],item[1],error_num_y):
                        count += 1
                if count >= 13:
                    num_h_list.append(val)
                    break

all_num_in_card = []
for num_h in num_h_list:
    for index,axis in enumerate(num_in_card):
        if axis[3] == num_h:
            axis_y = axis[1]
            break

    for index,axis in enumerate(num_in_card):
        if ((num_h-error_num_h) <= axis[3] <= (num_h+error_num_h)) and ((axis_y-error_num_y) <= axis[1] <= (axis_y+error_num_y)):
            all_num_in_card.append(num_in_card[index:(16 + index)])
            break

all_num_img_in_card = []
for num_in_card in all_num_in_card:
    num_in_card = sorted(num_in_card)
    num_img_in_card = []
    for axis_num in num_in_card:
        num_img_in_card.append(card_canny[axis_num[1]:axis_num[1]+axis_num[3],axis_num[0]:axis_num[0]+axis_num[2]])
    all_num_img_in_card.append(num_img_in_card)


# num_canny = cv2.Canny(num_img,200,250)
#cv2.THRESH_BINARY_INV|cv2.THRESH_OTSU
#在原有的阈值处理方法上加上cv2.THRESH_OTSU可以帮助自动判断阈值，适用于像素值是双峰图的图
#就是说所有像素点基本都集中在某两个值之间，某两个值最多，形成一个双峰
#cv2.THRESH_OTSU会自动帮助判断阈值，即在这双峰之间取个最优的，之后的操作就是看你|号前面填的是什么
_,num_canny = cv2.threshold(num_img,0,255,cv2.THRESH_BINARY_INV|cv2.THRESH_OTSU)
binary,contours,_ = cv2.findContours(num_canny,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

num_axis_list = []
all_num_img = []
for cnt in contours:
    x,y,w,h = cv2.boundingRect(cnt)
    num_axis_list.insert(0,(x,y,w,h))

for num_axis in num_axis_list:
    num_img_per = num_canny[num_axis[1]:(num_axis[1]+num_axis[3]),num_axis[0]:(num_axis[0]+num_axis[2])]
    # num_img_per = cv2.Canny(num_img_per,150,220)
    # kernel1 = np.ones((3,3),dtype=np.uint8)
    # num_img_per = cv2.morphologyEx(num_img_per,cv2.MORPH_CLOSE,kernel1,iterations=1)
    all_num_img.append(num_img_per)

all_res_num_list = []
for num_img_in_card in all_num_img_in_card:
    res_num_list = []
    for num in num_img_in_card:
        compared_list = []
        num = cv2.resize(num,(30,30))
        for index,tem_num in enumerate(all_num_img):
            tem_num = cv2.resize(tem_num,(30,30))
            res = cv2.matchTemplate(num,tem_num,cv2.TM_SQDIFF_NORMED)
            compared_list.append(res[0,0])
        num_find_index = compared_list.index(min(compared_list))
        res_num_list.append(num_find_index)

    all_res_num_list.append(res_num_list)

print(num_in_card)
print(all_res_num_list)
cv2.imshow('a',all_num_img[4])
cv2.imshow('b',num_img_in_card[0])
cv2.imshow('cardcanny',card_canny)
cv2.waitKey(0)
cv2.destroyAllWindows()












