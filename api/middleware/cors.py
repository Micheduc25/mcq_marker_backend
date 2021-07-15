class CorsMiddleware(object):

    def process_response(self, req, res):
        res["Access-Control-Allow-Origin"] = "*"
        return res
