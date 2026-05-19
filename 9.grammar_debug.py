from pathlib import Path
import importlib.util
import sys


def load_stage_module(module_name: str, filename: str):
    if module_name in sys.modules:
        return sys.modules[module_name]
    module_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


predict = load_stage_module("predict", "6.predict_set_builder.py")
grammar = predict.grammar

trans_check = {}
# i = 1

# for key in grammar:
#     for item in grammar[key]:
#         trans_check[i] = item
#         i += 1

# print(trans_check)


# for key in grammar:
#     for item in grammar[key]:
#         for k in item:
#             trans_check[k] = 1
#             # i += 1

# for key in trans_check:
#     print(key)

