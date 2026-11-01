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

__all__ = ["ConversionNotifier"]

import asyncio
import threading
import uuid

from lightspeed.common.constants import WindowNames
from lightspeed.trex.alpha_cutout.modifier import AlphaCardToMeshJob
from omni import ui
from omni.flux.job_queue.core import get_job_queue
from omni.flux.job_queue.core.enums import TERMINAL_JOB_STATES
from omni.flux.utils.common import EventSubscription
from omni.kit.notification_manager import NotificationButtonInfo, NotificationStatus, post_notification

from .report_text import summarize_report

_TITLE = "Alpha Card to Mesh"
_DURATION_SECONDS = 10


def _show_job_queue(*_) -> None:
    """Show and focus the Job Queue window."""
    ui.Workspace.show_window(WindowNames.JOB_QUEUE.value, True)
    window = ui.Workspace.get_window(WindowNames.JOB_QUEUE.value)
    if window:
        window.focus()


class ConversionNotifier:
    """Post a notification with the geometry counts when an Alpha Card to Mesh job finishes.

    Queue events arrive on worker threads; they are coalesced and handled on the UI loop, like the queue widget
    does, and every finished job is reported once.
    """

    def __init__(self):
        """Subscribe to job changes on the UI loop."""
        self._loop = asyncio.get_event_loop()
        self._lock = threading.Lock()
        self._pending: set[uuid.UUID] = set()
        self._dispatch_scheduled = False
        self._notified: set[uuid.UUID] = set()
        self._subscription: EventSubscription | None = get_job_queue().subscribe_job_changed(self._on_job_changed)

    def destroy(self) -> None:
        """Stop listening to the queue."""
        self._subscription = None

    def _on_job_changed(self, job_id: uuid.UUID) -> None:
        """Queue one changed job and schedule a single drain on the UI loop."""
        with self._lock:
            self._pending.add(job_id)
            if self._dispatch_scheduled:
                return
            self._dispatch_scheduled = True
        self._loop.call_soon_threadsafe(self._dispatch)

    def _dispatch(self) -> None:
        """Report every finished conversion job that was not reported yet."""
        with self._lock:
            job_ids = self._pending
            self._pending = set()
            self._dispatch_scheduled = False
        if self._subscription is None:
            return
        for job_id in job_ids:
            self.notify_if_finished(job_id)

    def notify_if_finished(self, job_id: uuid.UUID) -> None:
        """Post the report of a conversion job once it reached a terminal state with outputs.

        Args:
            job_id: Changed job identifier.
        """
        queue = get_job_queue()
        if job_id in self._notified:
            return
        snapshot = queue.get_job_snapshot(job_id)
        if snapshot.state not in TERMINAL_JOB_STATES:
            return
        self._notified.add(job_id)
        job = queue.get_job(job_id)
        if not isinstance(job, AlphaCardToMeshJob):
            return
        if not snapshot.has_outputs:
            post_notification(
                f"{_TITLE} failed: {snapshot.state_reason or snapshot.state.value.lower()}",
                status=NotificationStatus.WARNING,
                duration=_DURATION_SECONDS,
                button_infos=[NotificationButtonInfo("Open Job Queue", on_complete=_show_job_queue)],
            )
            return
        outputs = queue.get_job_outputs(job_id)
        summary = summarize_report(outputs[job.REPORT])
        if outputs.skip_reason is None:
            text, status = f"{_TITLE} converted:\n{summary}", NotificationStatus.INFO
        else:
            text, status = f"{_TITLE} skipped:\n{summary}", NotificationStatus.WARNING
        post_notification(
            text,
            status=status,
            duration=_DURATION_SECONDS,
            button_infos=[NotificationButtonInfo("Open Job Queue", on_complete=_show_job_queue)],
        )
