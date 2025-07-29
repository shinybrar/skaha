# Advanced Examples

Complex use cases and power-user examples for Skaha and the CANFAR Science Platform.

## Massively Parallel Processing

Let's assume you have a large dataset of 1000 FITS files that you want to process in parallel. You have a Python script that can process a single FITS file, and you want to run this script in parallel on 100 different Skaha sessions.

```python title="batch_processing.py"
from skaha.helpers import distributed
from glob import glob
from your.code import process_datafile

# Find all FITS files to process
datafiles = glob("/path/to/data/files/*.fits")

# Each replica processes its assigned chunk of files
# The chunk function automatically handles 1-based REPLICA_ID values
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

## Distributed Processing Strategies

Skaha provides two main strategies for distributing data across replicas:

### Chunking Strategy (`distributed.chunk`)

The `chunk` function divides your data into contiguous blocks, with each replica processing a consecutive chunk. The function uses 1-based replica IDs (matching Skaha's `REPLICA_ID` environment variable):

```python title="Chunking Example"
from skaha.helpers import distributed

# With 1000 files and 100 replicas:
# - Replica 1 processes files 0-9
# - Replica 2 processes files 10-19  
# - Replica 3 processes files 20-29
# - And so on...

datafiles = glob("/path/to/data/*.fits")
for datafile in distributed.chunk(datafiles):
    process_datafile(datafile)
```

### Striping Strategy (`distributed.stripe`)

The `stripe` function distributes data in a round-robin fashion, which is useful when file sizes vary significantly:

```python title="Striping Example"
from skaha.helpers import distributed

# With 1000 files and 100 replicas:
# - Replica 1 processes files 0, 100, 200, 300, ...
# - Replica 2 processes files 1, 101, 201, 301, ...
# - Replica 3 processes files 2, 102, 202, 302, ...
# - And so on...

datafiles = glob("/path/to/data/*.fits")
for datafile in distributed.stripe(datafiles):
    process_datafile(datafile)
```

### When to Use Each Strategy

- **Use `chunk`** when files are similar in size and you want each replica to process a contiguous block of data
- **Use `stripe`** when file sizes vary significantly, as it distributes the workload more evenly across replicas

### Edge Cases

Both functions handle edge cases gracefully:

- **More replicas than files**: Each file goes to a different replica, remaining replicas get no work
- **Single replica**: All data goes to that replica
- **Empty dataset**: All replicas receive empty iterators

```python title="Edge Case Example"
# With 3 files and 5 replicas using chunk():
# - Replica 1 gets file1.fits
# - Replica 2 gets file2.fits  
# - Replica 3 gets file3.fits
# - Replicas 4 and 5 get no files (empty iterator)

small_dataset = ["file1.fits", "file2.fits", "file3.fits"]
my_files = list(distributed.chunk(small_dataset))
if my_files:  # Check if replica has work to do
    for datafile in my_files:
        process_datafile(datafile)
else:
    print("No work assigned to this replica")
```

