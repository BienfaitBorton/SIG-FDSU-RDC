"""Metriques de calibration technique; aucune valeur n'est une validation nationale."""
from dataclasses import dataclass
from typing import Iterable
@dataclass(frozen=True)
class CalibrationMetrics:
    precision:float; recall:float; false_positive_rate:float; false_negative_rate:float; true_positive:int; true_negative:int; false_positive:int; false_negative:int
def calculate_calibration(expected:Iterable[bool], predicted:Iterable[bool]):
    pairs=tuple(zip(expected,predicted)); tp=sum(a and b for a,b in pairs); tn=sum(not a and not b for a,b in pairs); fp=sum(not a and b for a,b in pairs); fn=sum(a and not b for a,b in pairs)
    div=lambda a,b: round(a/b,4) if b else 0.0
    return CalibrationMetrics(div(tp,tp+fp),div(tp,tp+fn),div(fp,fp+tn),div(fn,fn+tp),tp,tn,fp,fn)

def synthetic_ground_truth_cases():
    """Cas techniques minimaux et controles, sans pretention nationale."""
    return (
        {"case":"exact_identifier","expected_match":True}, {"case":"direct_provenance","expected_match":True},
        {"case":"different_entities","expected_match":False}, {"case":"homonym","expected_match":False},
        {"case":"near_but_distinct","expected_match":False}, {"case":"same_name_different_province","expected_match":False},
        {"case":"identifier_conflict","expected_match":False}, {"case":"same_operator","expected_match":True},
        {"case":"different_operator","expected_match":False}, {"case":"missing_coordinates","expected_match":False},
    )
