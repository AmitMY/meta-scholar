# Meta Scholar

Our goal is to standardize the contributions of publications, like datasets, tasks, evaluation metrics, etc...
We believe every contribution should have the same fundamental structure, in order to be easy to work with and to advance science faster.

## Publications
Every `json` file contains the basic metadata for a publication, including title, authors, etc... The name of the file is used as the `id` of the publication.

## Datasets
#### `header.json`
Includes metadata on the dataset, including what are the types of fields it contains and their names, and a list of versions.
#### `dataset.py`
If exists, should include a `download` method that creates the following directory structure: `versions/{version}`.
The `download` method should create an `index.json` file, containing `data`, which is an object containing data from all of the dataset splits.
Further, it should create `split.json` to indicate the default data split, with the keys as the split name, and the values as arrays of ids in the split.

