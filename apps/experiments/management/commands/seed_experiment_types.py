"""Idempotent experiment-type seeding for dev / staging / demo.

Covers the lab's working set: classic reliability stress tests under
RA, electrical characterisation under TM, and the FA + MA categories
that the SPA's demo flow exercises. Safe to re-run; uses update_or_create
keyed on name.

The catalogue here is intentionally Western-industry standard so the
demo reads cleanly to anyone familiar with JEDEC / JESD22 / MIL-STD
reliability vocabulary.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.experiments.models import ExperimentType, LabCategory

# (name, category, description). Order is display-stable; the unique
# constraint on name keeps re-runs idempotent across deploys.
SEED_TYPES: list[tuple[str, str, str]] = [
    # --- Reliability Analysis (RA) ---
    ("TCT", LabCategory.RA, "Temperature Cycling Test (JESD22-A104)"),
    ("HAST", LabCategory.RA, "Highly Accelerated Stress Test (JESD22-A110)"),
    ("HTOL", LabCategory.RA, "High Temperature Operating Life (JESD22-A108)"),
    ("THB", LabCategory.RA, "Temperature Humidity Bias (JESD22-A101)"),
    ("BTC", LabCategory.RA, "Bias Temperature Cycling"),
    # --- Test & Measurement (TM) ---
    ("CP", LabCategory.TM, "Chip Probe / Wafer Sort"),
    ("FT", LabCategory.TM, "Final Test"),
    # --- Failure Analysis (FA) ---
    ("SEM", LabCategory.FA, "Scanning Electron Microscopy"),
    ("FIB", LabCategory.FA, "Focused Ion Beam Cross-section"),
    # --- Material Analysis (MA) ---
    ("EDX", LabCategory.MA, "Energy Dispersive X-ray Spectroscopy"),
    ("XRD", LabCategory.MA, "X-ray Diffraction"),
]


class Command(BaseCommand):
    help = (
        "Seed (or refresh) the standard reliability-lab experiment-type "
        "catalogue. Idempotent — re-running updates descriptions in place "
        "but never duplicates rows."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        created = 0
        updated = 0
        with transaction.atomic():
            for name, category, description in SEED_TYPES:
                _, was_created = ExperimentType.objects.update_or_create(
                    name=name,
                    defaults={
                        "lab_category": category,
                        "description": description,
                        "is_active": True,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Experiment types seeded: {created} created, {updated} updated, "
                f"{len(SEED_TYPES)} total."
            )
        )
