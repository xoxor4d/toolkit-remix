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

__all__ = ["TestConversionNotifier"]

import uuid
from unittest.mock import MagicMock, patch

from lightspeed.trex.alpha_cutout.modifier import AlphaCardToMeshJob, ConversionReport, MeshReport
from lightspeed.trex.alpha_cutout.widget.notifier import ConversionNotifier
from lightspeed.trex.alpha_cutout.widget.report_text import summarize_report
from omni.flux.job_queue.core.enums import JobState
from omni.flux.job_queue.core.job import JobOutputs
from omni.kit.notification_manager import NotificationStatus
from omni.kit.test import AsyncTestCase

_MODULE = "lightspeed.trex.alpha_cutout.widget.notifier"


def _queue(job, state: JobState, outputs: JobOutputs | None) -> MagicMock:
    queue = MagicMock()
    queue.get_job_snapshot.return_value = MagicMock(state=state, has_outputs=outputs is not None, state_reason=None)
    queue.get_job.return_value = job
    queue.get_job_outputs.return_value = outputs
    return queue


class TestConversionNotifier(AsyncTestCase):
    """Test the notification posted when a conversion job finishes."""

    async def test_summary_lists_a_few_meshes_and_counts_the_rest(self):
        # Arrange
        meshes = tuple(MeshReport(f"/Root/XForms/card{index}/mesh", 4, 2, 40, 20) for index in range(6))
        report = ConversionReport((*meshes[:5], MeshReport("/Root/XForms/trunk/mesh", 8, 12, 0, 0, "opaque")))

        # Act
        summary = summarize_report(report)

        # Assert
        self.assertEqual(
            summary.splitlines(),
            [
                "XForms/card0/mesh: 2 -> 20 faces, 4 -> 40 vertices",
                "XForms/card1/mesh: 2 -> 20 faces, 4 -> 40 vertices",
                "XForms/card2/mesh: 2 -> 20 faces, 4 -> 40 vertices",
                "XForms/card3/mesh: 2 -> 20 faces, 4 -> 40 vertices",
                "and 2 more meshes",
            ],
        )

    async def test_finished_conversion_job_posts_its_report_once(self):
        # Arrange
        job = AlphaCardToMeshJob(name="cutout")
        report = ConversionReport((MeshReport("/mesh_AAAAAAAAAAAAAAAA/mesh", 4, 2, 264, 132),))
        queue = _queue(job, JobState.DONE, JobOutputs({job.REPORT: report}))
        with patch(f"{_MODULE}.get_job_queue", return_value=queue), patch(f"{_MODULE}.post_notification") as post:
            notifier = ConversionNotifier()

            # Act
            notifier.notify_if_finished(job.job_id)
            notifier.notify_if_finished(job.job_id)
            notifier.destroy()

        # Assert
        post.assert_called_once()
        self.assertEqual(
            post.call_args.args, ("Alpha Card to Mesh converted:\nmesh: 2 -> 132 faces, 4 -> 264 vertices",)
        )
        self.assertIs(post.call_args.kwargs["status"], NotificationStatus.INFO)

    async def test_skipped_job_posts_a_warning_with_the_reasons(self):
        # Arrange
        job = AlphaCardToMeshJob(name="cutout")
        report = ConversionReport((MeshReport("/mesh_AAAAAAAAAAAAAAAA/mesh", 4, 2, 0, 0, "The texture is opaque."),))
        queue = _queue(job, JobState.SKIPPED, JobOutputs({job.REPORT: report}, skip_reason="No mesh was converted."))
        with patch(f"{_MODULE}.get_job_queue", return_value=queue), patch(f"{_MODULE}.post_notification") as post:
            notifier = ConversionNotifier()

            # Act
            notifier.notify_if_finished(job.job_id)
            notifier.destroy()

        # Assert
        self.assertEqual(post.call_args.args, ("Alpha Card to Mesh skipped:\nmesh: Skipped: The texture is opaque.",))
        self.assertIs(post.call_args.kwargs["status"], NotificationStatus.WARNING)

    async def test_running_jobs_and_other_job_types_are_ignored(self):
        # Arrange
        other_job = MagicMock()
        running = _queue(AlphaCardToMeshJob(name="cutout"), JobState.IN_PROGRESS, None)
        other = _queue(other_job, JobState.DONE, JobOutputs())
        with patch(f"{_MODULE}.post_notification") as post:
            with patch(f"{_MODULE}.get_job_queue", return_value=running):
                notifier = ConversionNotifier()

                # Act
                notifier.notify_if_finished(uuid.uuid4())
            with patch(f"{_MODULE}.get_job_queue", return_value=other):
                notifier.notify_if_finished(uuid.uuid4())
            notifier.destroy()

        # Assert
        post.assert_not_called()
        other.get_job_outputs.assert_not_called()
