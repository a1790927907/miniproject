import cv2
import numpy as np

class AnswerRec(object):

    def cv_show(self,imglist,waitkey=0,winname='default'):
        for img in imglist:
            cv2.imshow(f'{winname}{imglist.index(img)}',img)
        cv2.waitKey(waitkey)
        cv2.destroyAllWindows()

    def ptorder(self,pts):
        sum_res = np.sum(pts,axis=1)
        tl = pts[np.argmin(sum_res)]
        br = pts[np.argmax(sum_res)]
        ran = list(range(pts.shape[0]))
        ran.remove(np.argmin(sum_res))
        ran.remove(np.argmax(sum_res))
        new_pts = pts[ran]
        new_pts = new_pts[new_pts[:,0].argsort()]
        tr = new_pts[1]
        bl = new_pts[0]
        return (tl,tr,br,bl)

    #需要传入二维的pts(坐标点)
    def mcalc(self,pts,img):
        tl,tr,br,bl = self.ptorder(pts)
        w_1 = np.sqrt(np.array([pow((tl[0]-tr[0]),2) + pow((tl[1]-tr[1]),2)]))[0]
        w_2 = np.sqrt(np.array([pow((bl[0]-br[0]),2) + pow((bl[1]-br[1]),2)]))[0]
        w = max(w_1,w_2)
        h_1 = np.sqrt(np.array([pow((tl[0] - bl[0]), 2) + pow((tl[1] - bl[1]), 2)]))[0]
        h_2 = np.sqrt(np.array([pow((tr[0] - br[0]), 2) + pow((tr[1] - br[1]), 2)]))[0]
        h = max(h_1,h_2)
        axis_change = np.float32([tl,tr,br,bl])
        target_axis = np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])
        M = cv2.getPerspectiveTransform(axis_change,target_axis)
        wraped = cv2.warpPerspective(img,M,(int(w),int(h)))
        return wraped

    def approxcal(self,img_canny,flags=True,ep=0.1):
        contours = cv2.findContours(img_canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[1]
        contours_axis_list = [cv2.boundingRect(cnt) for cnt in contours]
        contours_axis_list_s = sorted(contours_axis_list, key=lambda x: x[2], reverse=True)
        max_contours = contours[contours_axis_list.index(contours_axis_list_s[0])]
        epsilon = ep * cv2.arcLength(max_contours, True)
        # 四个轮廓点的坐标
        approx = cv2.approxPolyDP(max_contours, epsilon, True)
        if flags:
            approx = approx.reshape(4, 2)
        return approx

    def findandgroupaxis(self,img_two):
        contours = cv2.findContours(img_two, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[1]
        circle_out_rect = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            judge = (1 <= w / h <= 1.2 or 1 <= h / w <= 1.2) and (w >= 32 and h >= 32)
            if judge:
                circle_out_rect.append((x, y, w, h))

        circle_out_rect = sorted(circle_out_rect, key=lambda x: x[1])
        grouped_axis = []
        for i in range(int(len(circle_out_rect) / 5) + 1):
            if circle_out_rect[i * 5:((i + 1) * 5 - 1)] == []:
                break
            grouped_axis.append(circle_out_rect[i * 5:((i + 1) * 5)])
        return grouped_axis

    def fetchallanswer(self,grouped_axis):
        all_choice = []
        for axis in grouped_axis:
            judgelist = []
            axis = sorted(axis)
            for x, y, w, h in axis:
                judge_img = img_two[y:y + h, x:x + w]
                zero_num = np.count_nonzero(judge_img)
                judgelist.append(zero_num)

            #如果没有选择的话，直接判错
            if max(judgelist) < 650:
                choice = 'no choice'
            else:
                choice = judgelist.index(max(judgelist))
            all_choice.append(choice)
        return all_choice

if __name__ == '__main__':
    true_answer = [3,0,1,2,4]
    img_card = cv2.imread('images_answer_sheet/test_02.png',0)
    img_card_origin = cv2.imread('images_answer_sheet/test_02.png')

    img_canny = cv2.Canny(img_card,150,220)

    #创建answer实例
    answer = AnswerRec()

    #传入对应canny边缘检测后的图，返回对应的答题纸的四个坐标点
    approx_test = answer.approxcal(img_canny)

    #根据答题纸对应的四个坐标点，将答题纸区域矫正并且筛选出来
    img_strech = answer.mcalc(approx_test,img_card_origin)

    # 将矫正后的图片二值化
    img_two = cv2.threshold(cv2.cvtColor(img_strech, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    #传入对应二值图，找出所有选项坐标，并且按照每个题目顺序进行分组
    grouped_axis = answer.findandgroupaxis(img_two)
    true_answer_num = 0

    #传入对应所有选项按题目顺序分组后的坐标点，返回每题对应的选项，A,B,C,D..按照0,1,2,3..对应
    all_choice = answer.fetchallanswer(grouped_axis)

    #将所有正确选项用绿框框起，错误选项用红框
    for your_choice,right_choice,choice_axis in zip(all_choice,true_answer,grouped_axis):
        choice_axis = sorted(choice_axis)
        if your_choice == 'no choice':
            right_choice_axis = choice_axis[right_choice]
            cv2.rectangle(img_strech, (right_choice_axis[0], right_choice_axis[1]),(right_choice_axis[0] + right_choice_axis[2], right_choice_axis[1] + right_choice_axis[3]),(0, 255, 0), thickness=2)
            cv2.putText(img_strech, 'true', (right_choice_axis[0], right_choice_axis[1] - 10), cv2.FONT_HERSHEY_DUPLEX,0.5, (0, 255, 0), thickness=1)
            continue
        if your_choice != right_choice:
            your_choice_axis = choice_axis[your_choice]
            right_choice_axis = choice_axis[right_choice]
            cv2.rectangle(img_strech,(right_choice_axis[0],right_choice_axis[1]),(right_choice_axis[0]+right_choice_axis[2],right_choice_axis[1]+right_choice_axis[3]),(0,255,0),thickness=2)
            cv2.rectangle(img_strech,(your_choice_axis[0],your_choice_axis[1]),(your_choice_axis[0]+your_choice_axis[2],your_choice_axis[1]+your_choice_axis[3]),(0,0,255),thickness=2)
            cv2.putText(img_strech, 'true', (right_choice_axis[0], right_choice_axis[1] - 10), cv2.FONT_HERSHEY_DUPLEX,0.5, (0, 255, 0), thickness=1)
            cv2.putText(img_strech, 'false', (your_choice_axis[0], your_choice_axis[1] - 10),cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 255), thickness=1)

        else:
            right_choice_axis = choice_axis[right_choice]
            cv2.rectangle(img_strech, (right_choice_axis[0], right_choice_axis[1]),(right_choice_axis[0] + right_choice_axis[2], right_choice_axis[1] + right_choice_axis[3]),(0, 255, 0), thickness=2)
            cv2.putText(img_strech,'true',(right_choice_axis[0], right_choice_axis[1]-10),cv2.FONT_HERSHEY_DUPLEX,0.5,(0,255,0),thickness=1)
            true_answer_num += 1

    #计算最后得分
    cv2.putText(img_strech,f'Score:{round((true_answer_num/len(true_answer))*100)}',(0,40),cv2.FONT_HERSHEY_DUPLEX,1.5,(0,0,0),thickness=2)

    #展示所有图片
    answer.cv_show([img_two,img_strech])
















