EVALUATION_QUEUE_NAME = "evaluation"
EVALUATION_JOB_TIMEOUT = 300
PROCESS_EVALUATION_TASK_FUNCTION = (
    "llm_eval_platform.workers.evaluation_worker.process_evaluation_task"
)