from __future__ import annotations


HSR_SUCCESS_LOG_STATUSES = frozenset(
    {
        "HSR 任务结束",
        "HSR 用户任务完成",
        "HSR 失败任务补跑完成",
        "HSR 本轮无需执行，已跳过",
        "HSR 人工排查通过",
    }
)


def general_log_result(status: str) -> str:
    """Map HSR success statuses to the host's generic history contract."""

    return "Success!" if status in HSR_SUCCESS_LOG_STATUSES else status
