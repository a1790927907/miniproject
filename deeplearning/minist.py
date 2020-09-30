'''
minist手写数字数据集，训练100个，过多个人电脑内存会溢出
'''

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import os
os.environ['TP_CPP_MIN_LOG_LEVEL'] = '2'

#n为卷积次数
#x为需要进行卷积的样本(传入shape为[batch,height,width,channels]，可为None)
#filter_num为基础卷积次数
#F为卷积核的shape，填入长或宽其中一个即可，一般都是1或3或5
#multi参数为每次迭代卷积核的个数乘数的基数
#y_num参数为目标值类别的个数
#此函数不适用
def CNN_y_predict(x,n=2,filter_num=32,F=3,multi=2,y_num=10):
    #定义卷积核权重系数,需要梯度下降训练，用变量表示
    #由于多次卷积，这里用字典表示
    w_filters = {}
    b_filter = {}
    features = {}
    relu_features = {}
    max_pool_features = {}
    x_copy = x
    base_channel = list(x_copy.shape)
    for i in range(len(base_channel)):
        try:
            base_channel[i] = int(base_channel[i])
        except:
            pass

    for i in range(n):
        b_filter[i] = tf.Variable(initial_value=tf.random_normal(shape=[filter_num], dtype=tf.float32))
        w_filters[i] = tf.Variable(initial_value=tf.random_normal(shape=[F,F,base_channel[-1],filter_num],dtype=tf.float32)) + b_filter[i]
        #卷积
        features[i] = tf.nn.conv2d(x_copy,w_filters[i],[1,1,1,1],'SAME')
        #relu激活函数
        relu_features[i] = tf.nn.relu(features[i])
        #最大值池化
        max_pool_features[i] = tf.nn.max_pool(relu_features[i],[1,2,2,1],[1,2,2,1],'SAME')

        #计算池化后出来的shape,更新shape信息
        if base_channel[1] % 2 == 0:
            base_channel = (base_channel[0],int(base_channel[1] / 2),int(base_channel[2] / 2),filter_num)
        else:
            base_channel = (base_channel[0],int(base_channel[1] / 2)+1,int(base_channel[2] / 2)+1,filter_num)
        filter_num = filter_num * multi
        x_copy = max_pool_features[i]

    if str(base_channel[0]) == '?':
        base_channel = list(base_channel)
        base_channel[0] = -1

    x_copy = tf.reshape(x_copy,(base_channel[0],base_channel[1]*base_channel[2]*base_channel[3]))
    #计算出最后的w权重系数
    w = tf.Variable(initial_value=tf.random_normal(shape=(base_channel[1]*base_channel[2]*base_channel[3],y_num)))
    b = tf.Variable(initial_value=tf.random_normal(shape=[y_num]))
    y_predict = tf.matmul(x_copy,w) + b
    return (y_predict,w_filters,b_filter,features,relu_features,max_pool_features)

#卷积操作函数，传入图片进行两次卷积 - 激活 - 池化
def CNN_num_two(images_):
    with tf.variable_scope('create_convolution_ratio'):
        # 第一次大卷积层
        # 创建3*3卷积核,32个卷积核
        fil1 = tf.Variable(initial_value=tf.random_normal(shape=[3, 3, 1, 32]))
        # 卷积操作
        # 卷积结束后输出形状为[-1,28,28,32]
        # 卷积需要加上偏置
        features1 = tf.nn.conv2d(images_, fil1, [1, 1, 1, 1], 'SAME') + tf.Variable(initial_value=tf.random_normal(shape=[32]))
        # Relu激活函数
        # 激活函数不变shape
        relu_features1 = tf.nn.relu(features1)
        # 池化
        # 池化之后输出形状为[-1,14,14,32]
        max_pool_features1 = tf.nn.max_pool(relu_features1, [1, 2, 2, 1], [1, 2, 2, 1], 'SAME')
        # print(max_pool_features1)
        # 第二次大卷积层
        # 使用第一次池化完毕的输出作为输入
        # 增加到64个卷积核
        fil2 = tf.Variable(initial_value=tf.random_normal(shape=[3, 3, 32, 64]))
        # 输出结束后shape为[-1,14,14,64]
        features2 = tf.nn.conv2d(max_pool_features1, fil2, [1, 1, 1, 1], 'SAME') + tf.Variable(initial_value=tf.random_normal(shape=[64]))

        # Relu第二次激活
        relu_features2 = tf.nn.relu(features2)

        # 第二次池化
        # 最终输出为[-1,7,7,64]
        max_pool_features2 = tf.nn.max_pool(relu_features2, [1, 2, 2, 1], [1, 2, 2, 1], 'SAME')

        # 将最后输出形状改变成符合softmax函数的形状，一般是二维
        # 最后输出形状即为通过神经网络隐藏层后的特征值
        x = tf.reshape(max_pool_features2, [-1, 7 * 7 * 64])

        return x,fil1,fil2

#输出测试集卷积-激活-池化后的输出
def CNN_test_img(img_test_CNN,fil1,fil2):
    # 卷积操作
    # 卷积结束后输出形状为[-1,28,28,32]
    features1 = tf.nn.conv2d(img_test_CNN, fil1, [1, 1, 1, 1], 'SAME')
    # Relu激活函数
    # 激活函数不变shape
    relu_features1 = tf.nn.relu(features1)
    # 池化
    # 池化之后输出形状为[-1,14,14,32]
    max_pool_features1 = tf.nn.max_pool(relu_features1, [1, 2, 2, 1], [1, 2, 2, 1], 'SAME')

    # 输出结束后shape为[-1,14,14,64]
    features2 = tf.nn.conv2d(max_pool_features1, fil2, [1, 1, 1, 1], 'SAME')

    # Relu第二次激活
    relu_features2 = tf.nn.relu(features2)

    # 第二次池化
    # 最终输出为[-1,7,7,64]
    max_pool_features2 = tf.nn.max_pool(relu_features2, [1, 2, 2, 1], [1, 2, 2, 1], 'SAME')

    # 将最后输出形状改变成符合softmax函数的形状，一般是二维
    # 最后输出形状即为通过神经网络隐藏层后的特征值
    x = tf.reshape(max_pool_features2, [-1, 7 * 7 * 64])

    return x



minist_data = input_data.read_data_sets('02-代码/mnist_data',one_hot=True)

images = tf.placeholder(dtype=tf.float32,shape=(None,784))
labels = tf.placeholder(dtype=tf.float32,shape=(None,10))
images_ = tf.reshape(images,[-1,28,28,1])

x,fil1,fil2 = CNN_num_two(images_)

with tf.variable_scope('create_w_b'):
    # 构建w系数
    w = tf.Variable(initial_value=tf.random_normal(shape=[7 * 7 * 64, 10]))
    b = tf.Variable(initial_value=tf.random_normal(shape=[10]))
    y_predict = tf.matmul(x, w) + b

#构建测试集
img_test = tf.placeholder(tf.float32,shape=(None,784))
label_test = tf.placeholder(tf.float32,shape=(None,10))
img_test_CNN = tf.reshape(img_test,[-1,28,28,1])
img_test_ = CNN_test_img(img_test_CNN,fil1,fil2)

#计算测试集结果
y_test = tf.matmul(img_test_,w) + b

#求出测试集结果中的最大值所在位置即为对应类别
#横向求，求每一排的最大值，因为上面是x*w，所以特征是横着的
test_loc = tf.argmax(y_test,axis=1)

#求出真实值的对应类别位置
true_loc = tf.argmax(label_test,axis=1)

#比对两者是否相同，相同返回True，不同返回False
bool_j = tf.equal(true_loc,test_loc)

#最后需要求出准确率，bool型无法求，所以需要转换类型
accuracy = tf.reduce_mean(tf.cast(bool_j,tf.float32))


# y_predict,w_filters,b_filter,features,relu_features,max_pool_features = CNN_y_predict(images_)
with tf.variable_scope('calc_loss'):
    #构建全连接层，计算损失
    loss = tf.nn.softmax_cross_entropy_with_logits(labels=labels,logits=y_predict)
    loss = tf.reduce_mean(loss)

with tf.variable_scope('create_optimizer'):
    optimizer = tf.train.AdamOptimizer(learning_rate=0.001)
    optimizer_min = optimizer.minimize(loss)


tf.summary.scalar('loss',loss)
tf.summary.histogram('w',w)
tf.summary.histogram('b',b)
tf.summary.histogram('filter_1',fil1)
tf.summary.histogram('filter_2',fil2)
merged = tf.summary.merge_all()


init = tf.global_variables_initializer()
saver = tf.train.Saver()
with tf.Session() as sess:
    sess.run(init)
    images_all,labels_all = minist_data.train.next_batch(300)
    img_test_all,label_test_all = minist_data.test.next_batch(100)
    # file_writer = tf.summary.FileWriter('./temp/',graph=sess.graph)
    # for i in range(500):
    #     sess.run(optimizer_min,feed_dict={labels:labels_all,images:images_all})
    #     print(sess.run(loss,feed_dict={labels:labels_all,images:images_all}))
    #
    #     summary = sess.run(merged,feed_dict={labels:labels_all,images:images_all})
    #     file_writer.add_summary(summary)
    #     saver.save(sess,'./temp/minist.ckpt')

    saver.restore(sess,'./temp/minist.ckpt')
    print(sess.run(accuracy,feed_dict={img_test:img_test_all,label_test:label_test_all}))
















