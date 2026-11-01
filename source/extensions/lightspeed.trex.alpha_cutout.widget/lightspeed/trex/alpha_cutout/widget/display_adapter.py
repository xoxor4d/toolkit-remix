"""
* SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
* SPDX-License-Identifier: Apache-2.0
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* https://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
"""

from __future__ import annotations

__all__ = ["AlphaCardToMeshDisplayAdapter"]

from lightspeed.trex.alpha_cutout.modifier import AlphaCardToMeshJob
from lightspeed.trex.alpha_cutout.modifier.report import ConversionReport
from lightspeed.trex.asset_modifiers.widget.display_adapter import AssetModifierDisplayAdapter
from omni.flux.job_queue.core.models import QueueJobDetailsSnapshot
from omni.flux.job_queue.widget.display_adapter_base import JobDetailField, JobDetailSection
from omni.flux.job_queue.widget.enums import JobDetailSectionPlacement

from .report_text import mesh_label, mesh_value

_SECTION_ID = "converted_meshes"
_SECTION_TITLE = "Converted meshes"


class AlphaCardToMeshDisplayAdapter(AssetModifierDisplayAdapter):
    """Present the Alpha Card to Mesh job with the geometry counts of every mesh it handled."""

    name = "alpha_card_to_mesh"
    job_type = AlphaCardToMeshJob
    display_name = "Alpha Card to Mesh"
    active_status_label = "Cutting meshes"

    def get_detail_sections(
        self,
        job: AlphaCardToMeshJob,
        details: QueueJobDetailsSnapshot,
        context_name: str,
    ) -> tuple[JobDetailSection, ...]:
        """List the face and vertex counts of every mesh before and after the cut.

        Args:
            job: The conversion job.
            details: Public queue details with the persisted outputs, when the job completed.
            context_name: USD context retained for the adapter contract.

        Returns:
            One section after the outputs, or nothing before the job completed.
        """
        report = details.outputs.get(job.REPORT) if details.outputs is not None else None
        if type(report) is not ConversionReport or not report.meshes:
            return ()
        fields = tuple(
            JobDetailField(f"{_SECTION_ID}.{index}", mesh_label(item), mesh_value(item), item.prim_path)
            for index, item in enumerate(report.meshes)
        )
        return (JobDetailSection(_SECTION_ID, _SECTION_TITLE, fields, JobDetailSectionPlacement.AFTER_OUTPUTS),)
