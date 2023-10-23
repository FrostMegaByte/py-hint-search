import requests


# def get_type4py_predictions(file_path: str):
#     with open(file_path) as f:
#         # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
#         response = requests.post("http://localhost:5001/api/predict?tc=0", f.read())
#         json_response = response.json()

#         functions_predictions = []
#         for class_obj in json_response["response"]["classes"]:
#             functions_predictions += class_obj["funcs"]

#         functions_predictions += json_response["response"]["funcs"]

#         filter_fields = ["name", "params_p", "ret_type_p"]
#         type_predictions = list(
#             map(
#                 lambda f: {key: f[key] for key in f if key in filter_fields},
#                 functions_predictions,
#             )
#         )
#         return type_predictions


def get_type4py_predictions(python_code: str):
    # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
    response = requests.post("http://localhost:5001/api/predict?tc=0", python_code)
    json_response = response.json()

    functions_predictions = []
    for class_obj in json_response["response"]["classes"]:
        functions_predictions += class_obj["funcs"]

    functions_predictions += json_response["response"]["funcs"]

    filter_fields = ["name", "params_p", "ret_type_p"]
    type_predictions = list(
        map(
            lambda f: {key: f[key] for key in f if key in filter_fields},
            functions_predictions,
        )
    )
    return type_predictions


# get_type4py_predictions_example()
