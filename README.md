# GeoNature Benchmark

Performance benchmarking tools for [GeoNature](https://github.com/PnX-SI/GeoNature) instances. This repository contains scripts to measure and compare the performance of a GeoNature application under various load conditions.

## Prerequisites

- Python 3.10 or higher
- A running GeoNature instance to benchmark
- Access to GeoNature credentials (optional, for authenticated tests)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/PnX-SI/geonature_benchmark.git
cd geonature_benchmark
```

### 2. Create a Virtual Environment

Create an isolated Python environment to manage dependencies:

```bash
# Create the virtual environment
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Running Benchmarks

#### 1. Basic Benchmark Run (with Web Interface)

Start a benchmark against a local GeoNature instance:

```bash
GEONATURE_LOGIN=admin GEONATURE_PASSWORD=secret locust -f run_benchmark.py --host=http://127.0.0.1:8000
```

This will open the Locust web interface at `http://127.0.0.1:8089` where you can:
- Set the number of users to simulate
- Set spawn rate (users per second)
- Start/stop the load test
- Monitor real-time statistics

#### 2. Headless Benchmark Run (with CSV Export)

Run benchmark without web interface and export results to CSV:

```bash
mkdir -p results/run1
locust -f run_benchmark.py --host=http://127.0.0.1:8000 \
       --csv=results/run1/stats --headless -u 10 -r 2 --run-time 5m
```

With authentication:

```bash
GEONATURE_LOGIN=admin GEONATURE_PASSWORD=secret \
locust -f run_benchmark.py --host=http://127.0.0.1:8000 \
       --csv=results/run1/stats --headless -u 10 -r 2 --run-time 5m
```

#### 3. Running Specific Tests with Tags

You can run only specific test categories using tags:

```bash
# Only synthese tests
locust -f run_benchmark.py --host=http://127.0.0.1:8000 \
       --csv=results/run1/stats --headless -u 10 -r 2 --run-time 5m --tags synthese

# Only geometry-related synthese tests
locust -f run_benchmark.py --host=http://127.0.0.1:8000 \
       --csv=results/run1/stats --headless -u 10 -r 2 --run-time 5m --tags synthese geometry

# Multiple specific tags
locust -f run_benchmark.py --host=http://127.0.0.1:8000 \
       --csv=results/run1/stats --headless -u 10 -r 2 --run-time 5m --tags synthese occtax
```

#### Common Locust Options

| Option | Description | Example |
|--------|-------------|---------|
| `-u N` | Number of simulated users | `-u 50` |
| `-r N` | Spawn rate (users per second) | `-r 5` |
| `--run-time` | Test duration | `--run-time 5m` or `--run-time 300s` |
| `--headless` | Run without web interface | `--headless` |
| `--tags TAG1 TAG2` | Run only tasks with these tags | `--tags synthese export` |
| `--csv=path/stats` | Export CSV results | `--csv=results/run1/stats` |
| `--host=URL` | GeoNature instance URL | `--host=http://127.0.0.1:8000` |

#### Available Test Tags

The benchmark includes comprehensive tests for all major GeoNature modules:

| Tag | Description |
|-----|-------------|
| `home` | General statistics tests |
| `gn_meta` | Metadata (acquisition frameworks, datasets) |
| `synthese` | All synthese module tests |
| `synthese geometry` | Geometric filter tests |
| `synthese area` | Administrative area filter tests (commune, departement, region) |
| `synthese taxon` | Taxonomic filter tests |
| `synthese regulation` | Regulation/protection status filter tests |
| `synthese export` | Export functionality tests (CSV, Excel, etc.) |
| `occtax` | OccTax module tests |
| `ref_geo` | Geographic reference data tests |
| `validation` | Validation module tests |
| `restricted` | Tests with restricted user permissions |

### Comparing Benchmark Results

After running multiple benchmarks, compare them using the `compare_benchmarks.py` script:

#### Compare Two or More Runs

```bash
python3 compare_benchmarks.py results/run1/stats.csv results/run2/stats.csv
```

Compare multiple runs:

```bash
python3 compare_benchmarks.py results/run1/stats.csv results/run2/stats.csv results/run3/stats.csv
```

#### Output

The comparison script generates:

1. **Console Report** showing:
   - Comparison table of average response times per task
   - Performance variations (% difference) vs baseline
   - Top 5 slowest tasks
   - Top 5 fastest tasks

2. **Generated Files**:
   - `task_comparison.png` - Bar chart comparing average response times
   - `task_comparison_detailed.csv` - Detailed statistics for all tasks
   - `task_comparison_pivot.csv` - Pivot table for Excel analysis

#### Example Output

```
==================================================
COMPARAISON PAR TÂCHE — TEMPS MOYEN (ms)
==================================================

📊 TEMPS MOYEN PAR TÂCHE

                              run1        run2
[synthese] obs bbox         245.50     268.30
[synthese] obs regulation   180.20     165.50

📈 VARIATIONS PAR RAPPORT À 'run1'

  vs run2:
    📈 [synthese] obs bbox               : +9.3% (+22.80 ms)
    📉 [synthese] obs regulation         : -8.2% (-14.70 ms)
```

## Benchmark Results

Results are generated interactively through the Locust web interface or exported as HTML/CSV reports:

- **Response times**: Min, max, average, and percentile values (50th, 95th, 99th)
- **Request/failure rates**: Total requests, failures, and success percentages
- **RPS (Requests Per Second)**: Current and average throughout the test
- **Performance comparison**: Before/after performance across benchmark runs


## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and suggestions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/PnX-SI/geonature_benchmark).

## Related Projects

- [GeoNature](https://github.com/PnX-SI/GeoNature) - The main GeoNature application
- [Locust](https://locust.io/) - Load testing framework documentation
