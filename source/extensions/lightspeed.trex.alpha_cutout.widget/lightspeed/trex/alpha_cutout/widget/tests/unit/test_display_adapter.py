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

__all__ = ["TestAlphaCardToMeshDisplayAdapter"]

import datetime
import uuid

from lightspeed.trex.alpha_cutout.modifier import AlphaCardToMeshJob
from lightspeed.trex.alpha_cutout.modifier.report import ConversionReport, MeshReport
from lightspeed.trex.alpha_cutout.widget.display_adapter import AlphaCardToMeshDisplayAdapter
from lightspeed.trex.asset_modifiers.widget.display_adapter import AssetModifierDisplayAdapter
from omni.flux.job_queue.core.enums import ApplyDisposition, ApplyOperation, JobState
from omni.flux.job_queue.core.job import JobOutputs
from omni.flux.job_queue.core.models import QueueJobDetailsSnapshot, QueueJobSnapshot
from omni.flux.job_queue.widget import get_display_adapter_registry
from omni.flux.job_queue.widget.display_adapter_registry import DisplayAdapterRegistry
from omni.flux.job_queue.widget.enums import JobDetailSectionPlacement
from omni.kit.test import AsyncTestCase


def _details(job: AlphaCardToMeshJob, outputs: JobOutputs | None) -> QueueJobDetailsSnapshot:
    now = datetime.datetime.now(datetime.UTC)
    snapshot = QueueJobSnapshot(
        graph_id=uuid.uuid4(),
        graph_name="cutout",
        graph_position=0,
        job_id=job.job_id,
        job_name=job.name,
        job_type=type(job).__name__,
        position=0,
        submitted_at=now,
        state=JobState.DONE,
        started_at=now,
        completed_at=now,
        state_reason=None,
        progress=None,
        error=None,
        apply_disposition=ApplyDisposition.NOT_APPLICABLE,
        apply_operation=ApplyOperation.IDLE,
        apply_handler_id=None,
        apply_reason=None,
        apply_error=None,
        has_outputs=outputs is not None,
    )
    return QueueJobDetailsSnapshot(snapshot, (), job.output_ports, (), (), (), None, outputs)


class TestAlphaCardToMeshDisplayAdapter(AsyncTestCase):
    """Test the Job Queue presentation of the conversion job."""

    async def test_extension_registers_the_adapter_for_the_exact_job_type(self):
        # Act
        adapter = get_display_adapter_registry().get_adapter(AlphaCardToMeshJob(name="cutout"))

        # Assert
        self.assertIs(type(adapter), AlphaCardToMeshDisplayAdapter)

    async def test_registry_prefers_the_adapter_over_the_generic_modifier_adapter(self):
        # Arrange
        registry = DisplayAdapterRegistry()
        registry.register(AssetModifierDisplayAdapter)
        registry.register(AlphaCardToMeshDisplayAdapter)

        # Act
        adapter = registry.get_adapter(AlphaCardToMeshJob(name="cutout"))

        # Assert
        self.assertIs(type(adapter), AlphaCardToMeshDisplayAdapter)
        self.assertEqual(adapter.get_source_name(AlphaCardToMeshJob(name="cutout")), "Asset Modifiers")

    async def test_detail_sections_list_every_mesh_of_the_report(self):
        # Arrange
        adapter = AlphaCardToMeshDisplayAdapter()
        job = AlphaCardToMeshJob(name="cutout", prim_paths=("/RootNode/meshes/mesh_AAAAAAAAAAAAAAAA/mesh",))
        report = ConversionReport(
            (
                MeshReport("/ReferenceTarget/XForms/card/mesh", 4, 2, 1200, 2124),
                MeshReport("/ReferenceTarget/XForms/trunk/mesh", 8, 12, 0, 0, "The texture is opaque."),
            )
        )

        # Act
        (section,) = adapter.get_detail_sections(job, _details(job, JobOutputs({job.REPORT: report})), "")

        # Assert
        self.assertEqual(section.title, "Converted meshes")
        self.assertIs(section.placement, JobDetailSectionPlacement.AFTER_OUTPUTS)
        self.assertEqual([field.label for field in section.fields], ["XForms/card/mesh", "XForms/trunk/mesh"])
        self.assertEqual(section.fields[0].value, "2 -> 2,124 faces, 4 -> 1,200 vertices")
        self.assertEqual(section.fields[1].value, "Skipped: The texture is opaque.")
        self.assertEqual(section.fields[1].tooltip, "/ReferenceTarget/XForms/trunk/mesh")

    async def test_detail_sections_are_empty_before_the_job_completed(self):
        # Arrange
        adapter = AlphaCardToMeshDisplayAdapter()
        job = AlphaCardToMeshJob(name="cutout")

        # Act
        sections = adapter.get_detail_sections(job, _details(job, None), "")

        # Assert
        self.assertEqual(sections, ())
