import requests
from pprint import pprint


def get_type4_py_predictions_example():
    with open("src/example/example.py") as f:
        # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
        response = requests.post("http://localhost:5001/api/predict?tc=0", f.read())
        jsonResponse = response.json()

        functionPredictions = jsonResponse["response"]["funcs"]

        returnTypePredictions = []
        for functionPrediction in functionPredictions:
            # returnTypePredictions.append(functionPrediction["params_p"]["a"])
            # returnTypePredictions.append(functionPrediction["params_p"]["b"])
            returnTypePredictions.append(functionPrediction["ret_type_p"])
            # returnTypePredictions.append("--------")

        return returnTypePredictions


def get_type4_py_predictions(file_path: str):
    with open(file_path) as f:
        # r = requests.post("https://type4py.com/api/predict?tc=0", f.read())
        response = requests.post("http://localhost:5001/api/predict?tc=0", f.read())
        jsonResponse = response.json()

        functionPredictions = jsonResponse["response"]["funcs"]

        returnTypePredictions = []
        for functionPrediction in functionPredictions:
            # returnTypePredictions.append(functionPrediction["params_p"]["a"])
            # returnTypePredictions.append(functionPrediction["params_p"]["b"])
            returnTypePredictions.append(functionPrediction["ret_type_p"])
            # returnTypePredictions.append("--------")

        return returnTypePredictions


# pprint(get_type4_py_predictions())
