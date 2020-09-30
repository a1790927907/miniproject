'''
数据集：https://wws.lanzous.com/ijlcmh29pmf
电脑原因，仅训练100个数据，数据过多内存溢出了。
需要迭代420次以上-
'''

import string
import tensorflow as tf
import pandas as pd
import os

#数据预处理，将数据中的验证码的四个字母转换成在所有数字，小写字母，大写字母中的索引
def data_proceeding(data):
    upper_letter = string.ascii_uppercase

    all_list = list(upper_letter)
    # all_dict = {i: j for i, j in enumerate(all_list)}
    data_str = data[1]
    index_str_list = []
    for i in data_str.tolist():
        sp = []
        for j in i:
            sp.append(all_list.index(j))
        index_str_list.append(sp)
    return (index_str_list,all_list)

#获取文件名队列
def get_file_queue(path,num,train=True):
    file_name = os.listdir(path)
    remove_list = []
    for i in file_name:
        #去除不需要的文件
        try:
            int(i.split('.')[0])
        except:
            remove_list.append(i)
    for j in remove_list:
        file_name.remove(j)

    #排序，确保读取后的特征值和目标值一一对应
    file_name.sort(key=lambda x:int(x.split('.')[0]))
    #为训练集则直接从第一个文件开始取
    if train:
        file_queue = [os.path.join(path,name) for name in file_name if int(name.split('.')[0]) <= (num-1)]
    #为测试集则从训练集之后的一个文件取
    else:
        file_queue = [os.path.join(path, name) for name in file_name if (train_num <= int(name.split('.')[0]) <= (num + train_num - 1))]
    return file_queue

#图片卷积(两层卷积)
#传入图片格式遵从[batch,height,weight,channel]
def convolute(image):
    with tf.variable_scope('convolute'):
        #第一次卷积
        #卷积核使用32个,3*3
        fil1 = tf.Variable(initial_value=tf.random_normal(shape=[3,3,3,32]))
        fil1_bias = tf.Variable(initial_value=tf.random_normal(shape=[32]))
        feature1 = tf.nn.conv2d(image,fil1,[1,1,1,1],'SAME') + fil1_bias
        #relu激活函数
        relu_feature1 = tf.nn.relu(feature1)
        #池化
        max_pool_feature1 = tf.nn.max_pool(relu_feature1,[1,2,2,1],[1,2,2,1],'SAME')

        #第二次卷积
        #卷积核使用64个，3*3
        fil2 = tf.Variable(initial_value=tf.random_normal(shape=[3,3,32,64]))
        fil2_bias = tf.Variable(initial_value=tf.random_normal(shape=[64]))
        feature2 = tf.nn.conv2d(max_pool_feature1,fil2,[1,1,1,1],'SAME') + fil2_bias
        #relu激活函数
        relu_feature2 = tf.nn.relu(feature2)
        #池化
        #最终图像变为[train_num,20,20,64]
        max_pool_feature2 = tf.nn.max_pool(relu_feature2,[1,2,2,1],[1,2,2,1],'SAME')

    with tf.variable_scope('create_w_b_full_connection'):
        # 将最终结果转换成二维的作为特征值
        x = tf.reshape(max_pool_feature2, [train_num, 5 * 20 * 64])
        #定义权重系数
        w = tf.Variable(initial_value=tf.random_normal(shape=[5*20*64,all_labels_num*4]))
        b = tf.Variable(initial_value=tf.random_normal(shape=[all_labels_num*4]))
        # 全连接
        y_predict = tf.matmul(x,w) + b

    return (y_predict,fil1,fil2,fil1_bias,fil2_bias,w,b)

#测试集图片在最优卷积核下卷积
def convolute_test(image_test,fil1,fil2,fil1_bias,fil2_bias):
    feature1 = tf.nn.conv2d(image_test,fil1,[1,1,1,1],'SAME') + fil1_bias
    #relu激活函数
    relu_feature1 = tf.nn.relu(feature1)
    #池化
    max_pool_feature1 = tf.nn.max_pool(relu_feature1,[1,2,2,1],[1,2,2,1],'SAME')

    feature2 = tf.nn.conv2d(max_pool_feature1,fil2,[1,1,1,1],'SAME') + fil2_bias
    #relu激活函数
    relu_feature2 = tf.nn.relu(feature2)
    #池化
    #最终图像变为[train_num,20,20,64]
    max_pool_feature2 = tf.nn.max_pool(relu_feature2,[1,2,2,1],[1,2,2,1],'SAME')

    #将最终结果转换成二维的作为特征值
    x = tf.reshape(max_pool_feature2,[test_num,5*20*64])
    return x


#定义训练集数据个数
tf.flags.DEFINE_integer('train_num',100,'训练集数据个数')
#定义测试集数据个数
tf.flags.DEFINE_integer('test_num',100,'测试集数据个数')

FLAGS = tf.flags.FLAGS
train_num = FLAGS.train_num
test_num = FLAGS.test_num


#目标值预处理(全部改为one-hot编码表示)
data = pd.read_csv('./image/02-代码/GenPics/labels.csv',header=None,iterator=True).get_chunk(train_num)
new_column,all_list = data_proceeding(data)

#所有类别的个数
all_labels_num = len(all_list)

#将目标值进行one-hot编码
tf_target = tf.constant(new_column)
one_hot_target = tf.one_hot(tf_target,all_labels_num)
one_hot_target = tf.cast(one_hot_target,tf.float32)

#文件读取+批处理
file_name_list = get_file_queue('./image/02-代码/GenPics',train_num)
#取消shuffle打乱队列顺序，确保特征值与目标值一一对应
file_queue = tf.train.string_input_producer(file_name_list,shuffle=False)
reader = tf.WholeFileReader()
key,value = reader.read(file_queue)
img_decoded = tf.image.decode_jpeg(value)
img_resized = tf.image.resize_images(img_decoded,(80,20))
img_reshaped = tf.reshape(img_resized,shape=(20,80,3))
img_batch = tf.train.batch([img_reshaped],train_num,2,train_num)
img_batch = tf.cast(img_batch,tf.float32)


#先将one-hot编码的目标值变为二维的
#三维保留，之后验证正确率时需要使用
one_hot_target_two_dim = tf.reshape(one_hot_target,shape=[train_num,-1])

#获取预测值
#最终返回的y_predict的形状为[train_num,62*4]
y_predict,fil1,fil2,fil1_bias,fil2_bias,w,b = convolute(img_batch)

#验证正确率，只有四个全为True时才返回True
#用reduce_all
with tf.variable_scope('calc_accruacy'):
    y_predict_used_to_calc_accuarcy = tf.reshape(y_predict,shape=[train_num,4,all_labels_num])
    y_predict_max_loc = tf.argmax(y_predict_used_to_calc_accuarcy,axis=-1)
    target_max_loc = tf.argmax(one_hot_target,axis=-1)
    boll_judge = tf.equal(y_predict_max_loc,target_max_loc)
    all_judge = tf.reduce_all(boll_judge,axis=1)
    accuracy = tf.reduce_mean(tf.cast(all_judge,tf.float32))

#使用sigmoid+交叉熵来计算损失
#从公式上看，softmax适合一个样本对应一个目标值，而sigmoid适合一个样本对应多个目标值
with tf.variable_scope('calc_loss'):
    loss = tf.nn.sigmoid_cross_entropy_with_logits(labels=one_hot_target_two_dim,logits=y_predict)
    loss = tf.reduce_mean(loss)

#创建亚当优化器
with tf.variable_scope('create_optimizer'):
    optimizer = tf.train.AdamOptimizer(learning_rate=0.001)
    optimizer_min = optimizer.minimize(loss)

saver = tf.train.Saver()
init = tf.global_variables_initializer()
with tf.Session() as sess:
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess,coord)
    sess.run(init)
    for i in range(1000):
        sess.run(optimizer_min)
        print(sess.run(loss),end='')
        print(f'准确率为{accuracy.eval()}')
        # saver.save(sess,'captcha.ckpt')
    # saver.restore(sess,'captcha.ckpt')
    coord.request_stop()
    coord.join(threads)





