class ResultVo:
    def success(message,data=None):
        return {
            'code':2000,
            'message':message,
            'data':data
        }

    def fail(message):
        return {
            'code':2001,
            'message':message,
            'data':None
        }