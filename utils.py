
from requests.cookies import RequestsCookieJar, create_cookie
from threading import Thread


def split_name_version(script_name):
    """ 返回分割的脚本名称，版本。"""
    name_version = script_name.rsplit('-', 1)
    if len(name_version) == 1:
        name, version = name_version[0], None
    else:
        name, version = name_version
        try:
            version = float(version)
        except ValueError:
            # 若无法转为浮点，那么将判定为其后的-是非版本号
            name = script_name
            version = None
    return name, version


def forever_run(function, *args, name=None, **kwargs):
    """ 进程周期内的运行线程。"""
    Thread(target=function, args=args, kwargs=kwargs, name=name, daemon=True).start()


def extract_cookies_str_to_jar(cookies_str, cookiejar=None, overwrite=True, cookies_specified_kw=None):
    """ cookies字符串提取成CookieJar。
    :param
        cookies_str:    cookie字符串文本
        cookiejar:      (可选)指定cookie添加到的cookiejar对象
        overwrite:      (可选)指定是否覆盖已经存在的cookie键
        cookie_kwargs:  (可选)指定Cookie的参数，参见 cookielib.Cookie 对象
                        - domain: 指定所在域
                        - path: 指定所在路径
    """
    # 分割cookies文本并提取到字典对象。
    cookie_dict = {}
    for cookie in cookies_str.split(';'):
        try:
            key, value = cookie.split('=', 1)
        except ValueError:
            continue
        else:
            cookie_dict[key] = value

    if not cookies_specified_kw:
        cookies_specified_kw = {}

    return cookiejar_from_dict(cookie_dict, cookiejar, overwrite, cookies_specified_kw)


def cookiejar_from_dict(cookie_dict, cookiejar=None, overwrite=True, cookies_specified_kw=None):
    """ 以下代码引用自requests库
    具体参数说明参考：requests.cookies.cookiejar_from_dict。
    """
    if not cookies_specified_kw:
        cookies_specified_kw = {}

    if cookiejar is None:
        cookiejar = RequestsCookieJar()

    if cookie_dict is not None:
        names_from_jar = [cookie.name for cookie in cookiejar]
        for name in cookie_dict:
            if overwrite or (name not in names_from_jar):
                # 添加参数 cookies_specified_kw
                cookiejar.set_cookie(create_cookie(name, cookie_dict[name], **cookies_specified_kw))

    return cookiejar


utility_package = {
    'extract_cookies_str_to_jar': extract_cookies_str_to_jar,

}


# import requests
# c = extract_cookies_str_to_jar('BAIDUID=3AE5238BCBA19F20AD4D50B310247F10:FG=1; BIDUPSID=3AE5238BCBA19F20AD4D50B310247F10; PSTM=1561781886; H_WISE_SIDS=129998_126124_128698_135585_136242_128064_135948_120133_134721_136238_132910_131247_132378_131517_118882_118866_118844_118826_118791_107313_135950_133352_135483_129654_136193_132250_127025_128968_135308_135813_132552_135432_135873_134047_134752_131423_135860_136165_135524_110085_134152_127969_131953_135839_135459_128195_135868_136303_132468_134353_135835_136261_136078; MCITY=-%3A; BD_UPN=19314753; BDORZ=FFFB88E999055A3F8A630C64834BD6D0; delPer=0; BD_CK_SAM=1; PSINO=7; BDRCVFR[x4e6higC8W6]=mk3SLVN4HKm; ZD_ENTRY=baidu; session_name=www.baidu.com; session_id=1583129312409; H_PS_645EC=caaf6M4C6elCBzN%2BqYdw1SJfLdG3VZUTDftyvQOnH368Q%2FhMlZaFqw5uDAlONQwxu44; BD_HOME=1; H_PS_PSSID=1464_21082_30840_30904_30824_26350_22157; sug=3; sugstore=0; ORIGIN=2; bdime=0')
# res = requests.get('http://www.baidu.com', cookies=c)
# print(res)
