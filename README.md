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

### Basic Benchmark Run

Start a benchmark against a local GeoNature instance:

```bash
GEONATURE_LOGIN=admin GEONATURE_PASSWORD=secret locust -f run_benchmark.py --host=http://127.0.0.1:8000
```

This will open the Locust web interface at `http://127.0.0.1:8089` where you can:
- Set the number of users to simulate
- Set spawn rate (users per second)
- Start/stop the load test
- Monitor real-time statistics


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
