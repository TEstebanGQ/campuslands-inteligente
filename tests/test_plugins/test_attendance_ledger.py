from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import func, select

from core.persistence import Asistencia, get_sqlite_engine
from plugins.attendance_ledger import AttendanceLedgerPlugin


@pytest.mark.asyncio
async def test_attendance_ledger_registers_attendance() -> None:
    plugin = AttendanceLedgerPlugin()

    result = await plugin.execute(
        estudiante_id="attendance_normal_1",
        aula_id="304",
        estado_visual="atento",
    )

    assert result["registrado"] is True
    assert result["ya_existia"] is False
    assert result["estudiante_id"] == "attendance_normal_1"
    assert result["fecha"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_attendance_ledger_is_idempotent_for_same_student_and_day() -> None:
    plugin = AttendanceLedgerPlugin()
    estudiante_id = "attendance_idempotent_1"

    first_result = await plugin.execute(
        estudiante_id=estudiante_id,
        aula_id="304",
        estado_visual="atento",
    )
    second_result = await plugin.execute(
        estudiante_id=estudiante_id,
        aula_id="304",
        estado_visual="atento",
    )

    engine = get_sqlite_engine()
    async with engine.begin() as conn:
        result = await conn.execute(
            select(func.count()).select_from(Asistencia).where(
                Asistencia.estudiante_id == estudiante_id,
                Asistencia.fecha == date.today(),
            )
        )
        row_count = result.scalar_one()

    assert first_result["ya_existia"] is False
    assert second_result["ya_existia"] is True
    assert row_count == 1
