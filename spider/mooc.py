import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import execjs,requests
import json
from requests import utils
import time
from pymongo import MongoClient
import tensorflow as tf
import re
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
    'Content-Type': 'application/json',
}

def rsaencrypt(e,rsaPublicKey):      #e是要加密的内容，后面是公钥
    e = e.encode("utf-8")
    public_key = """-----BEGIN PUBLIC KEY-----
    {rsaPublicKey}
    -----END PUBLIC KEY-----""".format(rsaPublicKey=rsaPublicKey)
    rsakey = RSA.importKey(public_key)
    cipher = PKCS1_v1_5.new(rsakey)
    cipher_text =base64.b64encode(cipher.encrypt(e)).decode("utf-8")
    return cipher_text

def get_cookie_jar(rtid,session):
    headers_c = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
    }
    nocache = execjs.eval('new Date().getTime()')
    url_cookie = 'https://reg.icourse163.org/dl/yd/ini?pd=imooc&pkid=cjJVGQM&pkht=www.icourse163.org&channel=1&topURL=https%3A%2F%2Fwww.icourse163.org%2F&rtid='+rtid+'&nocache=' + str(nocache)
    cookie_jar = session.get(url_cookie,headers=headers_c).cookies
    #必须停顿一会等待服务器更新session
    time.sleep(2)
    return cookie_jar

def generate_rtid():
    jscmd = '''
        var a = function() {
            var e = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
              , t = 32
              , i = [];
            for (; t-- > 0; )
                i[t] = e.charAt(Math.random() * e.length);
            return i.join("")
        };
    '''
    rtid = execjs.compile(jscmd).call('a')
    return rtid

def login_with_phone(un,pw):
    rtid = generate_rtid()
    session = requests.session()

    cookies = get_cookie_jar(rtid,session)

    h = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5gsH+AA4XWONB5TDcUd+xCz7ejOFHZKlcZDx+pF1i7Gsvi1vjyJoQhRtRSn950x498VUkx7rUxg1/ScBVfrRxQOZ8xFBye3pjAzfb22+RCuYApSVpJ3OO3KsEuKExftz9oFBv3ejxPlYc5yq7YiBO8XlTnQN0Sa4R4qhPO3I2MQIDAQAB"

    t = execjs.eval('new Date().getTime()')
    url_tk = 'https://reg.icourse163.org/dl/yd/gt?un=' + un + '&channel=1&pd=imooc&pkid=cjJVGQM&topURL=https%3A%2F%2Fwww.icourse163.org%2F&rtid=' + rtid + '&nocache=' + str(t)

    res_tk = session.get(url_tk, headers=headers, cookies=cookies)
    jsondata = json.loads(res_tk.text)
    tk = jsondata['tk']

    pwd = rsaencrypt(pw, h)
    url = 'https://reg.icourse163.org/dl/yd/lpwd'

    data = {
        'l': 1,
        'd': 10,
        'un': un,
        'pw': pwd,
        'pd': "imooc",
        'pkid': "cjJVGQM",
        'tk': tk,
        'domains': "",
        'channel': 1,
        'topURL': "https://www.icourse163.org/",
        'rtid': rtid,
    }

    res = session.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
    if json.loads(res.text)['ret'] == '201':
        new_cookies = utils.dict_from_cookiejar(res.cookies)
        new_cookies.update(utils.dict_from_cookiejar(cookies))
        headersa = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
        }
        user_id = get_userid(new_cookies,headersa)

        #不能用session来获取cookie，按照之前的会话将无法获取NTESSTUDYSI，因为之前在get_userid中的重定向时已经获取过一次NTESSTUDYSI，服务器认为获取过了NTESSTUDYSI，则不再返回NTESSTUDYSI
        res_ = requests.get(f'https://www.icourse163.org/home.htm?userId={user_id}',headers=headersa)

        cookie_csrf = utils.dict_from_cookiejar(res_.cookies)

        new_cookies['NTESSTUDYSI'] = cookie_csrf['NTESSTUDYSI']

        #以下为test
        user_url = 'https://www.icourse163.org/web/j/memberBean.getMocMemberPersonalDtoById.rpc?csrfKey=' + new_cookies['NTESSTUDYSI']
        user_data = {
            'memberId': user_id
        }
        res_user_info = session.post(user_url,headers=headersa,data=user_data,cookies=new_cookies)
        print(res_user_info.text)
        # new_cookies['uname'] = un
        # collection.insert(new_cookies)

def login_with_email(un,pw):
    rtid = generate_rtid()
    session = requests.session()

    cookies = get_cookie_jar(rtid,session)

    h = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5gsH+AA4XWONB5TDcUd+xCz7ejOFHZKlcZDx+pF1i7Gsvi1vjyJoQhRtRSn950x498VUkx7rUxg1/ScBVfrRxQOZ8xFBye3pjAzfb22+RCuYApSVpJ3OO3KsEuKExftz9oFBv3ejxPlYc5yq7YiBO8XlTnQN0Sa4R4qhPO3I2MQIDAQAB"

    t = execjs.eval('new Date().getTime()')
    url_tk = 'https://reg.icourse163.org/dl/yd/gt?un=' + un + '&channel=1&pd=imooc&pkid=cjJVGQM&topURL=https%3A%2F%2Fwww.icourse163.org%2F&rtid=' + rtid + '&nocache=' + str(t)

    res_tk = session.get(url_tk, headers=headers, cookies=cookies)
    jsondata = json.loads(res_tk.text)
    tk = jsondata['tk']

    pwd = rsaencrypt(pw, h)
    url = 'https://reg.icourse163.org/dl/yd/lpwd'
    t = execjs.eval('new Date().getTime()')
    data = {
        'un': un,
        'pw': pwd,
        'pd': "imooc",
        'l': 1,
        'd': 10,
        't': t,
        'pkid': "cjJVGQM",
        'domains': "",
        'tk': tk,
        'pwdKeyUp': 1,
        'channel': 0,
        'topURL': "https://www.icourse163.org/",
        'rtid': rtid
    }

    res = session.post(url, data=json.dumps(data), headers=headers, cookies=cookies)
    if json.loads(res.text)['ret'] == '201':
        new_cookies = utils.dict_from_cookiejar(res.cookies)
        new_cookies.update(utils.dict_from_cookiejar(cookies))
        new_cookies['uname'] = un
        collection.insert(new_cookies)
        # with open('cookie.json','a') as f:
        #     f.write(json.dumps(new_cookies))

def fetch_user_info(collection):
    key = {'_id':0}
    all_user = collection.find({},key)
    l = [i for i in all_user]
    return l

def get_userid(cookies,headersa):
    rurl = base64.b64encode('https://www.icourse163.org/'.encode()).decode()
    url = 'https://www.icourse163.org/member/login.htm?returnUrl=' + rurl
    res = requests.get(url,headers=headersa,cookies=cookies)

    c = utils.dict_from_cookiejar(res.cookies)
    user_id = c['STUDY_INFO'].split('|')[-2]

    return user_id

if __name__ == '__main__':
    tf.flags.DEFINE_integer('is_store',1,'是否批量登陆，默认为1代表是，若为0，则开始读取cookie数据')
    tf.flags.DEFINE_string('uname','','用户名')
    tf.flags.DEFINE_string('pwd','','密码')
    #json文件内容类似如下
    #[{'uname':'','pwd':''},{'uname':'','pwd':''},{'uname':'','pwd':''}]
    tf.flags.DEFINE_string('all_account','','批量登陆可以传入存有用户名和密码的json文件路径')
    FLAGS = tf.flags.FLAGS

    #所有数据存入mongodb
    mongo = MongoClient('localhost', 27017)
    collection = mongo.mooc.account
    if FLAGS.is_store == 1:

        if FLAGS.all_account:
            with open(FLAGS.all_account,'r') as f:
                all_account_data = json.loads(f.read())
            for data in all_account_data:
                if '@' in data['uname']:
                    login_with_email(data['uname'],data['pwd'])
                else:
                    login_with_phone(data['uname'],data['pwd'])
        else:
            if FLAGS.uname != '' and FLAGS.pwd != '':
                if '@' in FLAGS.uname:
                    login_with_email(FLAGS.uname,FLAGS.pwd)
                else:
                    login_with_phone(FLAGS.uname,FLAGS.pwd)
            else:
                exit(-1)
    else:
        all_data = fetch_user_info(collection)

















