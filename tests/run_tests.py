from __future__ import annotations

import asyncio
import os
import json
import traceback

from core.persistence import init_db
from tests.test_system import (
    test_event_bus,
    test_attendance_ledger_plugin,
    test_student_analytics_plugin,
    test_anomaly_notifier_plugin,
    test_space_optimizer_plugin,
    test_classifier_and_embedding,
    test_orchestrator_graph,
)
from tests.test_plugins.test_student_analytics import test_student_analytics_risk_levels
from tests.test_plugins.test_anomaly_notifier import test_anomaly_notifier_cooldown_and_thresholds


async def run_all():
    print("=== STARTING CAMPUSLANDS INTELIGENTE TEST SUITE ===")

    # Respaldar mock_academic_data.json si existe
    backup_path = "simulation/mock_academic_data.json.bak"
    has_backup = os.path.exists("simulation/mock_academic_data.json")
    if has_backup:
        os.rename("simulation/mock_academic_data.json", backup_path)

    # Setup database and academic mock data
    await init_db()
    data = {
        "estudiantes": {
            "test_est_1": {
                "nombre": "Test Student 1",
                "promedio_notas_historico": [4.0, 4.5],
                "tendencia_declarada": "mejora",
            }
        }
    }
    os.makedirs("simulation", exist_ok=True)
    with open("simulation/mock_academic_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f)

    tests = [
        ("EventBus PubSub", test_event_bus),
        ("Attendance Ledger Plugin", test_attendance_ledger_plugin),
        ("Student Analytics Plugin (Basic)", test_student_analytics_plugin),
        ("Anomaly Notifier Plugin (Basic)", test_anomaly_notifier_plugin),
        ("Space Optimizer Plugin", test_space_optimizer_plugin),
        ("Classifier & Embedding Engine", test_classifier_and_embedding),
        ("Cognitive Orchestrator Graph", test_orchestrator_graph),
        ("Student Analytics Risk Levels", test_student_analytics_risk_levels),
        ("Anomaly Notifier Thresholds & Cooldown", test_anomaly_notifier_cooldown_and_thresholds),
    ]

    failed = False
    for name, test_func in tests:
        try:
            print(f"Running test: {name} ...", end=" ", flush=True)
            await test_func()
            print("PASSED")
        except Exception as e:
            print("FAILED")
            traceback.print_exc()
            failed = True

    # Cleanup mock data
    try:
        os.remove("simulation/mock_academic_data.json")
    except Exception:
        pass

    # Restaurar el respaldo original
    if has_backup:
        os.rename(backup_path, "simulation/mock_academic_data.json")

    if failed:
        print("\n=== TEST RUN FAILED ===")
        exit(1)
    else:
        print("\n=== ALL TESTS PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    asyncio.run(run_all())
