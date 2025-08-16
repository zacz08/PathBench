import structures
import torch
import dill
import algorithms.configuration.maps.dense_map
from typing import NamedTuple

class Size(NamedTuple):
    width: int
    height: int

class _PointMetaClass(type(NamedTuple), type(torch.Tensor)):
    pass

class Point(NamedTuple, torch.Tensor, metaclass=_PointMetaClass):
    x: int
    y: int


DenseMap = algorithms.configuration.maps.dense_map.DenseMap

convert_classes = {
    "Size": lambda s: structures.Size(s.width, s.height),
    "Point": lambda p: structures.Point(p.x, p.y),
    "DenseMap": lambda d: algorithms.configuration.maps.dense_map.DenseMap(d.grid)
}
names = ("structures.Point", "structures.Size", "algorithms.configuration.maps.dense_map.DenseMap")

def recursive_replace_loaded_objects(obj, depth: int = 3):
    """
    Safely walk loaded objects and replace legacy types.
    - Skip numpy/torch arrays and primitives
    - Recurse into dict/list/tuple/set
    - For generic objects, only attempt safe setattr; skip read-only / dangerous attrs
    - Preserve convert_classes behavior
    """
    # ---- fast returns / safety ----
    if depth <= 0:
        return obj

    import numpy as np
    try:
        import torch  # optional
    except Exception:
        torch = None

    def _is_primitive(x):
        return isinstance(x, (int, float, bool, str, bytes, type(None)))

    def _is_np(x):
        return isinstance(x, (np.ndarray, np.generic))

    def _is_torch(x):
        return torch is not None and isinstance(x, torch.Tensor)

    # primitives / arrays: do not descend
    if _is_primitive(obj) or _is_np(obj) or _is_torch(obj):
        return obj

    # ---- convert_classes at object-level (preserve original behavior) ----
    try:
        cls_name = obj.__class__.__qualname__
    except Exception:
        cls_name = None

    try:
        if cls_name and cls_name in convert_classes:
            return convert_classes[cls_name](obj)
    except Exception:
        # if conversion fails, fall back to original object
        return obj

    # ---- containers ----
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            obj[k] = recursive_replace_loaded_objects(v, depth - 1)
        return obj

    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = recursive_replace_loaded_objects(obj[i], depth - 1)
        return obj

    if isinstance(obj, tuple):
        return tuple(recursive_replace_loaded_objects(v, depth - 1) for v in obj)

    if isinstance(obj, set):
        # sets are unordered; rebuild
        return set(recursive_replace_loaded_objects(v, depth - 1) for v in obj)

    # ---- generic object: walk safe attributes ----
    # common read-only / dangerous attrs to skip
    skip_attrs = {
        # numpy-ish / array-ish
        "dtype", "shape", "strides", "size", "ndim", "itemsize", "nbytes", "base",
        "ctypes", "flags", "flat", "T", "real", "imag",
        # torch-ish
        "grad", "grad_fn", "data",
        # common meta
        "__dict__", "__weakref__", "__slots__", "__class__", "__module__",
    }

    # iterate attributes defensively
    for attribute in dir(obj):
        if attribute.startswith("__") and attribute.endswith("__"):
            continue
        if attribute in skip_attrs:
            continue

        # get current value
        try:
            attr_val = getattr(obj, attribute)
        except Exception:
            continue

        # builtins module values: skip (cheap heuristic from original code)
        try:
            if getattr(attr_val.__class__, "__module__", "") == "builtins":
                continue
        except Exception:
            pass

        # class-level convert for attribute
        try:
            attr_cls_name = getattr(attr_val.__class__, "__qualname__", None)
            if attr_cls_name and attr_cls_name in convert_classes:
                try:
                    new_val = convert_classes[attr_cls_name](attr_val)
                    try:
                        setattr(obj, attribute, new_val)
                    except Exception:
                        pass
                    attr_val = new_val  # continue processing new value below
                except Exception:
                    # conversion failed; keep old value
                    pass
        except Exception:
            pass

        # recurse
        try:
            new_val = recursive_replace_loaded_objects(attr_val, depth - 1)
        except Exception:
            continue

        # write back if possible
        try:
            setattr(obj, attribute, new_val)
        except Exception:
            # read-only or descriptor; ignore
            pass

    return obj

def load(fname):
    old_classes = tuple([eval(i) for i in names])
    exec(", ".join(i for i in names) + " = " + ", ".join(i.split(".")[-1] for i in names))

    loaded_obj = dill.load(open(fname, "rb"), ignore=True)

    exec(", ".join(i for i in names) + " = old_classes")

    return recursive_replace_loaded_objects(loaded_obj)
