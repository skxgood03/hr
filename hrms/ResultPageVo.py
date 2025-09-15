
class ResultPageVo:
    #code:2000  请求成功  code：20001  请求失败


    def __init__(self,code=2000,message='success',total=0,data=None):
        self.code = code
        self.message = message
        self.total = total
        self.data = data


    def success(message,total,data=None):
        return {
            'code':2000,
            'message':message,
            'total':total,
            'data':data
        }

    def fail(message):
        return {
            'code':2001,
            'message':message,
            'data':None
        }