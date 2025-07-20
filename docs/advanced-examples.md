# Advanced Examples

Complex use cases and power-user examples for Skaha and the CANFAR Science Platform.

## Massively Parallel Processing

Lets assume you have a large dataset of 1000 FITS files that you want to process in parallel. You have a Python script that can process a single FITS file, and you want to run this script in parallel on 100 different Skaha sessions.


```python title="batch_processing.py"
from skaha.helpers import distributed
from regex import findall
from your.code import process_datafile

datafiles = findall("/path/to/data/files/*.fits")

for datafile in distributed.chunk(datafiles):
    process_datafile(datafile)
```

### Launching Analysis with Python API

```python title="Large-Scale Parallel Processing"
from skaha.session import AsyncSession

async with AsyncSession() as session:
    sessions = await session.create(
        name="fits-processing",
        image="images.canfar.net/your/analysis-container:latest",
        kind="headless",
        cores=8,
        ram=32,
        cmd="python",
        args=["/path/to/batch_processing.py"],
        replicas=100,
    )
    return sessions
```

### Launching Analysis with CLI

```bash title="Large-Scale Parallel Processing"
skaha create --cores 8 --memory 32 --replicas 100 --name fits-processing headless images.canfar.net/your/analysis-container:latest -- python /path/to/batch_processing.py
```

## Varying File Sizes

In both cases, the `distributed.block` function will ensure that each session only processes 10 FITS files. e.g. the first session will process files 0-9, the second session will process files 10-19, and so on.

If your datafiles increase in size, e.g. the first 10 files are small, the next 10 are larger, you can use the `distributed.stripe` function instead. This will ensure that each session processes files 0,10,20,..., the second session will process files 1,11,21,..., and so on. This saves you from having to write complex logic to determine the memory allocation for each session.

