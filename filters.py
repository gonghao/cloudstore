# -*- coding: utf-8 -*-

import time

def datetimeformat(value, format='%Y年%m月%d日%H:%M'):
    return time.strftime(format, time.localtime(value)).decode('utf-8')
