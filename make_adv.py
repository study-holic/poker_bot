"""Pickles the adversary bots (adv_<name>.pkl) and the incumbent v4
(v4.pkl, from model.Model) with protocol 4. Run from the repo root:

    .venv/Scripts/python.exe make_adv.py
"""
import pickle

from adv_bots import ADVERSARIES


def dump(obj, path):
    blob = pickle.dumps(obj, protocol=4)
    pickle.loads(blob)
    with open(path, "wb") as f:
        f.write(blob)
    print("wrote", path, len(blob), "bytes")


if __name__ == "__main__":
    for name, cls in ADVERSARIES.items():
        dump(cls(), f"adv_{name}.pkl")
    from model import Model
    dump(Model(), "v4.pkl")
