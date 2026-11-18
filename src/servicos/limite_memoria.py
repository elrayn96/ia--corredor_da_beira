"""Limite de memória do processo de busca, instalado antes de carregar a instância."""

import os

LIMITE_MEMORIA_BYTES = 2 * 1024**3
_job_windows = None


def aplicar_limite(limite=LIMITE_MEMORIA_BYTES):
    """Deve ser chamado no processo de trabalho, nunca na janela principal."""
    if limite <= 0:
        raise ValueError("O limite de memória deve ser positivo.")
    if os.name == "nt":
        _aplicar_no_windows(limite)
        return

    import resource

    actual, maximo = resource.getrlimit(resource.RLIMIT_AS)
    alvo = min(v for v in (limite, actual, maximo) if v != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (alvo, alvo))


def _aplicar_no_windows(limite):
    import win32api
    import win32job

    global _job_windows
    novo = _job_windows is None
    job = win32job.CreateJobObject(None, "") if novo else _job_windows
    classe = win32job.JobObjectExtendedLimitInformation
    info = win32job.QueryInformationJobObject(job, classe)
    info["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY
    previo = info["ProcessMemoryLimit"]
    info["ProcessMemoryLimit"] = min(previo, limite) if previo else limite
    win32job.SetInformationJobObject(job, classe, info)
    if novo:
        win32job.AssignProcessToJobObject(job, win32api.GetCurrentProcess())
        _job_windows = job
