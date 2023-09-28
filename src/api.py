import requests
from pprint import pprint


def get_type4py_predictions_example():
    with open("src/example/example.py") as f:
        # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
        response = requests.post("http://localhost:5001/api/predict?tc=0", f.read())
        json_response = response.json()

        functions_predictions = json_response["response"]["funcs"]

        filter_fields = ["name", "params_p", "ret_type_p"]
        type_predictions = list(
            map(
                lambda f: {key: f[key] for key in f if key in filter_fields},
                functions_predictions,
            )
        )
        return type_predictions

        # returnTypePredictions = []
        # for function_prediction in functions_predictions:
        #     # returnTypePredictions.append(functionPrediction["params_p"]["a"])
        #     # returnTypePredictions.append(functionPrediction["params_p"]["b"])
        #     returnTypePredictions.append(function_prediction["ret_type_p"])
        #     # returnTypePredictions.append("--------")

        # return returnTypePredictions


def get_type4_py_predictions(file_path: str):
    with open(file_path) as f:
        # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
        response = requests.post("http://localhost:5001/api/predict?tc=0", f.read())
        json_response = response.json()

        functions_predictions = json_response["response"]["funcs"]

        filter_fields = ["name", "params_p", "ret_type_p"]
        type_predictions = list(
            map(
                lambda f: {key: f[key] for key in f if key in filter_fields},
                functions_predictions,
            )
        )
        return type_predictions

        # returnTypePredictions = []
        # for functionPrediction in functionPredictions:
        #     # returnTypePredictions.append(functionPrediction["params_p"]["a"])
        #     # returnTypePredictions.append(functionPrediction["params_p"]["b"])
        #     returnTypePredictions.append(functionPrediction["ret_type_p"])
        #     # returnTypePredictions.append("--------")

        # return returnTypePredictions


pprint(get_type4py_predictions_example())
