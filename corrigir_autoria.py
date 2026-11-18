"""Corrige os últimos N commits consecutivos da branch do Corredor da Beira."""
import argparse
import subprocess
import sys

BRANCH = "refs/heads/correcao/conformidade-enunciado"
ANTIGO = b"Halal Beats <halalbeats0@gmail.com>"
NOVO = b"naeemjulaya2-star <naeemjulaya2@gmail.com>"


def git(*args, data=None):
    return subprocess.run(["git", "--no-replace-objects", *args], input=data,
                          stdout=subprocess.PIPE, check=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n", type=int)
    parser.add_argument("--publicar", action="store_true")
    args = parser.parse_args()
    if args.n < 1:
        raise ValueError("O número de commits deve ser positivo.")
    remote = git("ls-remote", "--exit-code", "origin", BRANCH).split()[0].decode()
    if subprocess.run(["git", "cat-file", "-e", remote + "^{commit}"],
                      stderr=subprocess.DEVNULL).returncode:
        git("-c", "http.version=HTTP/1.1", "fetch", "--no-tags", "origin", BRANCH)
    chain = []
    oid = remote.encode()
    for _ in range(args.n):
        if not oid:
            raise ValueError("O intervalo ultrapassa a raiz do histórico.")
        raw = git("cat-file", "commit", oid.decode())
        head, body = raw.split(b"\n\n", 1)
        lines = head.split(b"\n")
        parents = [line[7:] for line in lines if line.startswith(b"parent ")]
        if len(parents) > 1 or any(line.startswith(b"gpgsig") for line in lines):
            raise ValueError("O intervalo inclui um merge ou um commit assinado.")
        if not any(line.startswith(b"author " + ANTIGO + b" ") for line in lines):
            raise ValueError("O commit " + oid[:10].decode() + " tem outro autor. Verifica N.")
        chain.append((oid, lines, body))
        oid = parents[0] if parents else None

    parent = oid
    for old, lines, body in reversed(chain):
        for i, line in enumerate(lines):
            if line.startswith(b"parent "):
                lines[i] = b"parent " + parent
            elif line.startswith((b"author " + ANTIGO + b" ", b"committer " + ANTIGO + b" ")):
                lines[i] = line.replace(ANTIGO, NOVO, 1)
        raw = b"\n".join(lines) + b"\n\n" + body
        parent = git("hash-object", "-t", "commit", "-w", "--stdin", data=raw).strip()
        if git("cat-file", "commit", parent.decode()) != raw:
            raise ValueError("Falhou a verificação do commit reescrito.")
        subject = body.split(b"\n", 1)[0].decode("utf-8", "replace")
        print(old[:8].decode(), "->", parent[:8].decode(), subject)
    if args.publicar:
        git("push", "--atomic", "--force-with-lease=" + BRANCH + ":" + remote,
            "origin", parent.decode() + ":" + BRANCH)
        print("Correcção publicada.")
    else:
        print("Pré-visualização concluída. Nenhuma branch foi alterada.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit("Operação interrompida: " + str(exc))
