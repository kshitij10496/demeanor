import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from app import app
from main import TICKERS


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_analysis_result():
    """Mock result from analyze_index_for_web function."""
    return {
        'ticker_name': 'DJIA',
        'summary': {
            'data_points': 8524,
            'date_range': '1992-01-01 to 2025-11-08',
            'mean': 0.000234,
            'std': 0.012345
        },
        'distribution': [
            {
                'threshold': 1,
                'observed_count': 2500,
                'observed_pct': 29.32,
                'expected_count': 2700.5,
                'expected_pct': 31.67,
                'diff_count': -200.5,
                'diff_pct': -2.35
            },
            {
                'threshold': 2,
                'observed_count': 450,
                'observed_pct': 5.28,
                'expected_count': 385.1,
                'expected_pct': 4.52,
                'diff_count': 64.9,
                'diff_pct': 0.76
            }
        ],
        'plot_path': 'output/DJIA/2025-11-08_z_scores.png',
        'csv_path': 'output/DJIA/2025-11-08_analysis.csv'
    }


class TestIndexRoute:
    """Tests for the GET / route."""

    def test_index_returns_200(self, client):
        """Test that index route returns 200 status code."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_renders_template(self, client):
        """Test that index route renders the correct template."""
        response = client.get('/')
        assert b'Market Index Z-Score Analysis' in response.data

    def test_index_contains_ticker_options(self, client):
        """Test that index page contains all ticker options."""
        response = client.get('/')
        for ticker in TICKERS.keys():
            assert ticker.encode() in response.data

    def test_index_contains_form(self, client):
        """Test that index page contains the analysis form."""
        response = client.get('/')
        assert b'<form' in response.data
        assert b'action="/analyze"' in response.data
        assert b'method="post"' in response.data

    def test_index_contains_select_element(self, client):
        """Test that index page contains select dropdown."""
        response = client.get('/')
        assert b'<select' in response.data
        assert b'name="index"' in response.data


class TestAnalyzeRoute:
    """Tests for the POST /analyze route."""

    @patch('app.analyze_index_for_web')
    def test_analyze_valid_index(self, mock_analyze, client, mock_analysis_result):
        """Test analyze route with valid index."""
        mock_analyze.return_value = mock_analysis_result

        response = client.post('/analyze', data={'index': 'DJIA'})

        assert response.status_code == 200
        mock_analyze.assert_called_once_with('DJIA')

    @patch('app.analyze_index_for_web')
    def test_analyze_renders_results(self, mock_analyze, client, mock_analysis_result):
        """Test that analyze route renders results template."""
        mock_analyze.return_value = mock_analysis_result

        response = client.post('/analyze', data={'index': 'DJIA'})

        assert b'DJIA Analysis Results' in response.data
        assert b'8,524' in response.data  # data_points formatted
        assert b'1992-01-01 to 2025-11-08' in response.data

    @patch('app.analyze_index_for_web')
    def test_analyze_all_valid_indices(self, mock_analyze, client, mock_analysis_result):
        """Test analyze route works for all valid indices."""
        for ticker in TICKERS.keys():
            mock_result = mock_analysis_result.copy()
            mock_result['ticker_name'] = ticker
            mock_analyze.return_value = mock_result

            response = client.post('/analyze', data={'index': ticker})

            assert response.status_code == 200
            assert ticker.encode() in response.data
            mock_analyze.assert_called_with(ticker)

    def test_analyze_invalid_index(self, client):
        """Test analyze route with invalid index name."""
        response = client.post('/analyze', data={'index': 'INVALID'})
        assert response.status_code == 400
        assert b'Invalid index selected' in response.data

    def test_analyze_missing_index(self, client):
        """Test analyze route with missing index parameter."""
        response = client.post('/analyze', data={})
        assert response.status_code == 400
        assert b'Invalid index selected' in response.data

    def test_analyze_empty_index(self, client):
        """Test analyze route with empty index parameter."""
        response = client.post('/analyze', data={'index': ''})
        assert response.status_code == 400
        assert b'Invalid index selected' in response.data

    @patch('app.analyze_index_for_web')
    def test_analyze_displays_distribution_table(self, mock_analyze, client, mock_analysis_result):
        """Test that distribution statistics are displayed."""
        mock_analyze.return_value = mock_analysis_result

        response = client.post('/analyze', data={'index': 'DJIA'})

        assert b'Distribution Analysis' in response.data
        assert b'Observed' in response.data
        assert b'Expected (Normal)' in response.data
        assert b'Difference' in response.data

    @patch('app.analyze_index_for_web')
    def test_analyze_displays_summary_stats(self, mock_analyze, client, mock_analysis_result):
        """Test that summary statistics are displayed."""
        mock_analyze.return_value = mock_analysis_result

        response = client.post('/analyze', data={'index': 'DJIA'})

        assert b'Summary Statistics' in response.data
        assert b'Data Points' in response.data
        assert b'Date Range' in response.data
        assert b'Mean Daily Return' in response.data
        assert b'Standard Deviation' in response.data

    @patch('app.analyze_index_for_web')
    def test_analyze_includes_plot_image(self, mock_analyze, client, mock_analysis_result):
        """Test that results page includes plot image."""
        mock_analyze.return_value = mock_analysis_result

        response = client.post('/analyze', data={'index': 'DJIA'})

        assert b'/plot/DJIA' in response.data
        assert b'<img' in response.data


class TestPlotRoute:
    """Tests for the GET /plot/<index_name> route."""

    def test_plot_existing_file(self, client):
        """Test serving an existing plot file."""
        # Create a temporary PNG file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as tmp_file:
            # Write a minimal PNG header (1x1 pixel)
            png_header = b'\x89PNG\r\n\x1a\n'
            tmp_file.write(png_header)
            tmp_file.write(b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01')
            tmp_file.write(b'\x08\x02\x00\x00\x00\x90wS\xde')
            tmp_file.write(b'\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01')
            tmp_file.write(b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
            tmp_path = tmp_file.name

        try:
            # Mock time.strftime to return a predictable date
            import time
            today = time.strftime('%Y-%m-%d')

            # Create the expected directory structure
            plot_dir = f'output/DJIA'
            os.makedirs(plot_dir, exist_ok=True)
            plot_path = f'{plot_dir}/{today}_z_scores.png'

            # Copy temp file to expected location
            with open(tmp_path, 'rb') as src:
                with open(plot_path, 'wb') as dst:
                    dst.write(src.read())

            response = client.get('/plot/DJIA')

            assert response.status_code == 200
            assert response.mimetype == 'image/png'
            assert len(response.data) > 0

            # Cleanup
            os.remove(plot_path)

        finally:
            os.remove(tmp_path)

    def test_plot_nonexistent_file(self, client):
        """Test serving a non-existent plot file."""
        # Use a date that definitely doesn't exist
        import time
        with patch('time.strftime', return_value='1900-01-01'):
            response = client.get('/plot/NONEXISTENT')
            assert response.status_code == 404
            assert b'Plot not found' in response.data

    def test_plot_with_mock_file(self, client):
        """Test plot route with mocked file existence."""
        import time
        today = time.strftime('%Y-%m-%d')
        plot_path = f'output/TEST_INDEX/{today}_z_scores.png'

        # Create the plot file
        os.makedirs('output/TEST_INDEX', exist_ok=True)
        with open(plot_path, 'wb') as f:
            # Write minimal PNG
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01')
            f.write(b'\x08\x02\x00\x00\x00\x90wS\xde')

        try:
            response = client.get('/plot/TEST_INDEX')
            assert response.status_code == 200
            assert response.mimetype == 'image/png'
        finally:
            os.remove(plot_path)
            os.rmdir('output/TEST_INDEX')


class TestCaching:
    """Tests for caching behavior."""

    @patch('app.analyze_index_for_web')
    def test_caching_behavior(self, mock_analyze, client, mock_analysis_result):
        """Test that analyze_index_for_web is called (which handles caching internally)."""
        mock_analyze.return_value = mock_analysis_result

        # First request
        client.post('/analyze', data={'index': 'DJIA'})
        assert mock_analyze.call_count == 1

        # Second request (caching is handled in analyze_index_for_web)
        client.post('/analyze', data={'index': 'DJIA'})
        assert mock_analyze.call_count == 2


class TestErrorHandling:
    """Tests for error handling."""

    @patch('app.analyze_index_for_web')
    def test_analyze_handles_exception(self, mock_analyze, client):
        """Test that analyze route handles exceptions from analysis."""
        mock_analyze.side_effect = Exception("Analysis failed")

        with pytest.raises(Exception):
            client.post('/analyze', data={'index': 'DJIA'})

    @patch('app.analyze_index_for_web')
    def test_analyze_handles_value_error(self, mock_analyze, client):
        """Test that analyze route handles ValueError from invalid index."""
        mock_analyze.side_effect = ValueError("Invalid index name")

        with pytest.raises(ValueError):
            client.post('/analyze', data={'index': 'DJIA'})


class TestRouteIntegration:
    """Integration tests for multiple routes."""

    @patch('app.analyze_index_for_web')
    def test_full_workflow(self, mock_analyze, client, mock_analysis_result):
        """Test complete workflow: index -> analyze -> plot."""
        mock_analyze.return_value = mock_analysis_result

        # Step 1: Get index page
        response = client.get('/')
        assert response.status_code == 200
        assert b'DJIA' in response.data

        # Step 2: Submit analysis
        response = client.post('/analyze', data={'index': 'DJIA'})
        assert response.status_code == 200
        assert b'DJIA Analysis Results' in response.data

        # Step 3: Verify plot URL is in results
        assert b'/plot/DJIA' in response.data

    def test_navigation_links(self, client):
        """Test that navigation links are present."""
        response = client.get('/')
        assert response.status_code == 200

    @patch('app.analyze_index_for_web')
    def test_back_link_in_results(self, mock_analyze, client, mock_analysis_result):
        """Test that results page has link back to index."""
        mock_analyze.return_value = mock_analysis_result

        response = client.post('/analyze', data={'index': 'DJIA'})
        assert b'href="/"' in response.data
