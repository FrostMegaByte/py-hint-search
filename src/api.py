import requests


def get_type4py_predictions_example():
    with open("example/example.py") as f:
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


def get_type4py_predictions(file_path: str):
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
