"""
Pruebas de Evaluación de Dataset y Rendimiento
Rol: Juan José (Dataset Engineering, Stress Testing & UI)
"""

import os
import json
from src.tools.threat_inspector import inspect_threat

def test_scam_dataset_structure():
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scam_dataset_30.json")
    assert os.path.exists(dataset_path), "El archivo scam_dataset_30.json debe existir"
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    assert len(cases) >= 15, "El dataset debe contener al menos 15 casos iniciales"
    for case in cases:
        assert "id" in case
        assert "category" in case
        assert "expected_verdict" in case
        assert "text" in case

def test_evaluate_dataset_precision():
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scam_dataset_30.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    correct = 0
    for case in cases:
        res = inspect_threat(case["text"])
        # Los casos de control deben ser BAJO
        if case["category"] == "LEGITIMO_CONTROL":
            if res["threat_level"] == "BAJO":
                correct += 1
        else:
            # Los casos maliciosos deben ser detectados como MEDIO o CRÍTICO
            if res["threat_level"] in ["MEDIO", "CRÍTICO"]:
                correct += 1
                
    accuracy = correct / len(cases)
    print(f"\nExactitud preliminar de reglas heurísticas: {accuracy * 100:.1f}%")
    assert accuracy >= 0.70, "La precisión inicial debe ser al menos del 70%"
