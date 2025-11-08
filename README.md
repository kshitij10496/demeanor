# demeaner

Collection of experiments inspired from The Misbehaviour of Markets by Benoit Mendelbrot.

- What is the frequency distribution of the point changes of S&P500?

Intraday price change = Close - Open

Day-over-day price change = Today - Yesterday

# DowJones

Fetch historical price change data for the Dow Jones Industrial Average (DJIA) index as mentioned in the Risk, Ruin and Reward Chapter of the book.

We source the numbers from the Yahoo Finance API.

## Web Application

A Flask web application is available to serve the analysis as a service.

### Running the Web App

```bash
uv run python app.py
```

The application will be available at `http://localhost:5000`

### Features

- Select from 4 major market indices (DJIA, SP500, NASDAQ, NIFTY50)
- View comprehensive analysis including:
  - Summary statistics (data points, date range, mean, standard deviation)
  - Distribution comparison table (observed vs expected frequencies)
  - Z-score time series plot
- Date-based caching for improved performance

### CLI Usage

To run the analysis from the command line:

```bash
uv run python main.py
```

This will analyze all indices and save results to the `output/` directory.

## Testing

The web application includes comprehensive tests for all route handlers.

### Running Tests

```bash
uv run pytest test_app.py -v
```

### Test Coverage

The test suite includes 23 tests covering:
- **Index Route** - Form rendering, ticker options display
- **Analyze Route** - Valid/invalid inputs, result rendering, error handling
- **Plot Route** - Image serving, file existence checks
- **Caching** - Date-based caching behavior
- **Integration** - Full workflow testing

All tests use mocking to avoid external API calls and filesystem dependencies during testing.
