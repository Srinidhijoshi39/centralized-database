"""
Basic tests for the Centralized Trading Database application
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import app
        import backup_manager
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")

def test_environment_variables():
    """Test that environment variables are properly loaded"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # These should have default values even if not set
    assert os.getenv('DB_HOST', 'localhost') is not None
    assert os.getenv('DB_PORT', '5432') is not None

@patch('psycopg2.pool.SimpleConnectionPool')
def test_app_creation(mock_pool):
    """Test that the Flask app can be created without database connection"""
    mock_pool.return_value = MagicMock()
    
    try:
        import app
        assert app.app is not None
        assert app.app.name == 'app'
    except Exception as e:
        pytest.fail(f"Failed to create Flask app: {e}")

def test_table_map():
    """Test that table mapping is correctly defined"""
    import app
    
    expected_tables = {
        'master_bot_data': 'master_bot_data',
        'client_bot_signups': 'client_bot_signups',
        'daily_trading_sessions': 'user_session_data'
    }
    
    assert app.TABLE_MAP == expected_tables

def test_backup_manager_creation():
    """Test that BackupManager can be instantiated"""
    from backup_manager import BackupManager
    
    try:
        backup_mgr = BackupManager()
        assert backup_mgr is not None
        assert hasattr(backup_mgr, 'create_backup')
        assert hasattr(backup_mgr, 'cleanup_old_backups')
    except Exception as e:
        pytest.fail(f"Failed to create BackupManager: {e}")

def test_required_files_exist():
    """Test that all required files exist in the project"""
    required_files = [
        'app.py',
        'backup_manager.py',
        'backup_scheduler.py',
        'requirements.txt',
        '.env.example',
        'README.md',
        'LICENSE',
        '.gitignore'
    ]
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for file_name in required_files:
        file_path = os.path.join(project_root, file_name)
        assert os.path.exists(file_path), f"Required file {file_name} is missing"

def test_templates_directory():
    """Test that templates directory exists and contains required files"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(project_root, 'templates')
    
    assert os.path.exists(templates_dir), "Templates directory is missing"
    
    required_templates = [
        'database_viewer.html',
        'view_data.html',
        'session_details.html'
    ]
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        assert os.path.exists(template_path), f"Template {template} is missing"

if __name__ == '__main__':
    pytest.main([__file__])