"""Execute a Jupyter notebook from a fresh kernel using jupyter_client.

Usage:
    python scripts/run_notebook.py notebooks/data_understanding.ipynb
"""
import json
import sys
import time
from pathlib import Path

import jupyter_client


def run_notebook(nb_path: Path | str, timeout: int = 3600) -> None:
    nb_path = Path(nb_path).resolve()
    print(f"\n========================================================")
    print(f"Executing: {nb_path.name}")
    print(f"========================================================")
    nb_dir = nb_path.parent

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    km = jupyter_client.KernelManager(kernel_name="python3")
    # Start kernel with cwd set to notebook directory
    km.start_kernel(cwd=str(nb_dir))
    kc = km.client()
    kc.start_channels()
    kc.wait_for_ready(timeout=60)
    print("Fresh kernel ready.")

    execution_count = 0
    t0_total = time.perf_counter()

    try:
        for idx, cell in enumerate(nb["cells"]):
            if cell.get("cell_type") != "code":
                continue

            source = "".join(cell.get("source", []))
            if not source.strip():
                continue

            execution_count += 1
            first_line = source.strip().splitlines()[0][:70]
            print(f"  [{execution_count}] Cell {idx}: {first_line} ...", end=" ", flush=True)
            t0 = time.perf_counter()

            # Execute code
            msg_id = kc.execute(source)

            # Collect outputs from IOPub
            cell_outputs = []
            errored = False
            error_details = None

            while True:
                try:
                    msg = kc.get_iopub_msg(timeout=timeout)
                except Exception as e:
                    raise TimeoutError(f"Timed out waiting for cell {idx} output: {e}")

                # Ensure message belongs to our execution
                if msg.get("parent_header", {}).get("msg_id") != msg_id:
                    continue

                msg_type = msg["header"]["msg_type"]
                content = msg["content"]

                if msg_type == "status":
                    if content["execution_state"] == "idle":
                        break
                elif msg_type == "stream":
                    cell_outputs.append({
                        "name": content["name"],
                        "output_type": "stream",
                        "text": content["text"].splitlines(keepends=True)
                    })
                elif msg_type in ("display_data", "execute_result"):
                    data = content["data"]
                    out = {
                        "output_type": msg_type,
                        "data": data,
                        "metadata": content.get("metadata", {})
                    }
                    if msg_type == "execute_result":
                        out["execution_count"] = execution_count
                    cell_outputs.append(out)
                elif msg_type == "error":
                    errored = True
                    error_details = content
                    cell_outputs.append({
                        "output_type": "error",
                        "ename": content["ename"],
                        "evalue": content["evalue"],
                        "traceback": content["traceback"]
                    })

            # Check shell reply for execution status
            reply = kc.get_shell_msg(timeout=timeout)
            status = reply["content"]["status"]
            elapsed = time.perf_counter() - t0

            cell["outputs"] = cell_outputs
            cell["execution_count"] = execution_count

            if errored or status != "ok":
                print(f"FAILED ({elapsed:.2f}s)")
                print(f"\n--- Error in Cell {idx} ---")
                if error_details:
                    print("\n".join(error_details.get("traceback", [])))
                raise RuntimeError(f"Cell {idx} failed in {nb_path.name}")
            else:
                print(f"OK ({elapsed:.2f}s)")

        total_elapsed = time.perf_counter() - t0_total
        print(f"Completed {nb_path.name} in {total_elapsed:.1f}s")

    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)
        print("Kernel shut down.")

    # Save notebook with outputs
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"Saved executed notebook to {nb_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/run_notebook.py <notebook_path>")
    run_notebook(sys.argv[1])
