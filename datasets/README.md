# Datasets

Each dataset includes a `header.json` file, describing its schema, and a `download.py` script, including the function `download` that downloads a specific version `$v` to the `/versions/$v/` directory.

Each version should minimally include a `index.jsonl` file, where each line is a single datum.

Additionally, it may include a `split.json` file to declare as many splits as wanted, with whatever names. The `split.json` format is an object, with keys as names of the splits, and values as arrays of indexes from the `index.jsonl` file.
