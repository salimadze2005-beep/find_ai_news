def significance(scores, weights):
    if set(weights) != set(type(scores).model_fields) or abs(sum(weights.values()) - 1) > 1e-6 or any(v < 0 for v in weights.values()):
        raise ValueError("Invalid scoring weights")
    return round(sum(getattr(scores, name) * weight for name, weight in weights.items()), 2)
