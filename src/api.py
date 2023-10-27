import requests


class Type4PyException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def get_type4py_predictions(python_code: str):
    # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
    response = requests.post("http://localhost:5001/api/predict?tc=0", python_code)
    json_response = response.json()

    if json_response["error"] is not None:
        raise Type4PyException(json_response["error"])

    functions_predictions = []
    for class_obj in json_response["response"]["classes"]:
        functions_predictions += class_obj["funcs"]

    functions_predictions += json_response["response"]["funcs"]

    filter_fields = ["q_name", "params_p", "ret_type_p"]
    type_predictions = list(
        map(
            lambda f: {key: f[key] for key in f if key in filter_fields},
            functions_predictions,
        )
    )
    return type_predictions


# get_type4py_predictions_example()
