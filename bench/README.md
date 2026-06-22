# bench

Where a benchmark agent's run actually happens. Each run gets its own folder here (its prompt, code, results, and logs), and the folder starts empty.

Position in the project: the "consumer" side. An agent running here reads the knowledge through the `knowledge-mcp` server (it holds no knowledge itself), and after the run you collect its results and logs with the `operator/` scripts.

Keep this clean between runs so a new run cannot see an old one (no cross-run leakage).
