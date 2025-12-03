import os
import pytest
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.apps import apps
from django_rls.settings_type import DjangoRLSSettings

@pytest.fixture
def clean_migrations():
    """Cleanup generated migrations after test"""
    # Setup: clean before test just in case
    for app_label in ["test_app", "regular_app"]:
        app_config = apps.get_app_config(app_label)
        migrations_dir = os.path.join(app_config.path, "migrations")
        if os.path.exists(migrations_dir):
            for f in os.listdir(migrations_dir):
                if f != "__init__.py" and f.endswith(".py"):
                    try:
                        os.remove(os.path.join(migrations_dir, f))
                    except PermissionError:
                        pass # Ignore open files on windows if any

    yield

    # Teardown: clean after test
    for app_label in ["test_app", "regular_app"]:
        app_config = apps.get_app_config(app_label)
        migrations_dir = os.path.join(app_config.path, "migrations")
        if os.path.exists(migrations_dir):
            for f in os.listdir(migrations_dir):
                if f != "__init__.py" and f.endswith(".py"):
                    try:
                        os.remove(os.path.join(migrations_dir, f))
                    except PermissionError:
                        pass

@pytest.mark.django_db
def test_makemigrations_auto_adds_rls(clean_migrations):
    # This should create 0001_initial.py
    call_command("makemigrations", "test_app", interactive=False)
    
    app_config = apps.get_app_config("test_app")
    migrations_dir = os.path.join(app_config.path, "migrations")
    
    files = [f for f in os.listdir(migrations_dir) if f.startswith("0001_")]
    assert len(files) == 1
    
    with open(os.path.join(migrations_dir, files[0]), "r") as f:
        content = f.read()
        
        # TenantModel has tenant_id -> should have RLS
        assert "CREATE POLICY" in content
        assert "test_app_tenantmodel_rls_policy" in content
        
        # MixedModel has tenant_id -> should have RLS
        assert "test_app_mixedmodel_rls_policy" in content
        
        # NoRLSModel -> should NOT have RLS
        assert "test_app_norlsmodel_rls_policy" not in content

@pytest.mark.django_db
def test_makemigrations_interactive_selection_all_fields(clean_migrations):
    """Test that interactive selection works when user selects all available fields."""
    with patch('django_rls.management.commands.makemigrations.questionary.checkbox') as mock_checkbox:
        # Track calls to return appropriate values per model
        call_responses = {
            "MixedModel": ["tenant_id", "user_id"],  # Has both
            "TenantModel": ["tenant_id"],  # Only has tenant_id
            "UserModel": ["user_id"],  # Only has user_id
        }
        
        def checkbox_side_effect(*args, **kwargs):
            # Extract model name from the prompt text
            prompt_text = args[0] if args else ""
            for model_name, fields in call_responses.items():
                if model_name in prompt_text:
                    mock = MagicMock()
                    mock.ask.return_value = fields
                    return mock
            # Default: return all available (shouldn't happen)
            mock = MagicMock()
            mock.ask.return_value = []
            return mock
        
        mock_checkbox.side_effect = checkbox_side_effect
        
        call_command("makemigrations", "test_app")
        
        app_config = apps.get_app_config("test_app")
        migrations_dir = os.path.join(app_config.path, "migrations")
        files = [f for f in os.listdir(migrations_dir) if f.startswith("0001_")]
        
        with open(os.path.join(migrations_dir, files[0]), "r") as f:
            content = f.read()
            # Verify RLS policies were created
            assert "CREATE POLICY" in content
            # Verify questionary was called (interactive mode was used)
            assert mock_checkbox.called

@pytest.mark.django_db
def test_makemigrations_interactive_selection_partial(clean_migrations):
    """Test that interactive selection works when user selects only some fields."""
    with patch('django_rls.management.commands.makemigrations.questionary.checkbox') as mock_checkbox:
        # For MixedModel (which has both tenant_id and user_id), select only tenant_id
        call_responses = {
            "MixedModel": ["tenant_id"],  # Select only tenant_id, not user_id
            "TenantModel": ["tenant_id"],
            "UserModel": ["user_id"],
        }
        
        def checkbox_side_effect(*args, **kwargs):
            prompt_text = args[0] if args else ""
            for model_name, fields in call_responses.items():
                if model_name in prompt_text:
                    mock = MagicMock()
                    mock.ask.return_value = fields
                    return mock
            mock = MagicMock()
            mock.ask.return_value = []
            return mock
        
        mock_checkbox.side_effect = checkbox_side_effect
        
        call_command("makemigrations", "test_app", interactive=True)
        
        # Verify questionary was called for interactive selection
        assert mock_checkbox.called
        # Verify it was called for MixedModel specifically
        call_args_list = [str(call) for call in mock_checkbox.call_args_list]
        assert any("MixedModel" in str(call) for call in mock_checkbox.call_args_list)

@pytest.mark.django_db
def test_makemigrations_interactive_selection_none(clean_migrations):
    """Test that interactive selection works when user selects no fields."""
    with patch('django_rls.management.commands.makemigrations.questionary.checkbox') as mock_checkbox:
        # Mock user selecting no fields (empty list) for all models
        mock_checkbox.return_value.ask.return_value = []
        
        call_command("makemigrations", "test_app", interactive=True)
        
        app_config = apps.get_app_config("test_app")
        migrations_dir = os.path.join(app_config.path, "migrations")
        files = [f for f in os.listdir(migrations_dir) if f.startswith("0001_")]
        
        with open(os.path.join(migrations_dir, files[0]), "r") as f:
            content = f.read()
            # If no fields selected, no RLS policies should be created
            assert "CREATE POLICY" not in content
            # Verify questionary was called
            assert mock_checkbox.called

@pytest.mark.django_db
def test_makemigrations_skips_non_tenant_app(clean_migrations):
    # regular_app is NOT in TENANT_APPS, so RLS should NOT be added
    call_command("makemigrations", "regular_app", interactive=False)
    
    app_config = apps.get_app_config("regular_app")
    migrations_dir = os.path.join(app_config.path, "migrations")
    
    files = [f for f in os.listdir(migrations_dir) if f.startswith("0001_")]
    assert len(files) == 1
    
    with open(os.path.join(migrations_dir, files[0]), "r") as f:
        content = f.read()
        
        # Should have CreateModel operations
        assert "Create model RegularModel" in content or "RegularModel" in content
        assert "Create model AnotherModel" in content or "AnotherModel" in content
        
        # Should NOT have any RLS policies
        assert "CREATE POLICY" not in content
        assert "ENABLE ROW LEVEL SECURITY" not in content
        assert "regular_app_regularmodel_rls_policy" not in content
        assert "regular_app_anothermodel_rls_policy" not in content

@pytest.mark.django_db
def test_makemigrations_mixed_apps_only_tenant_app_gets_rls(clean_migrations):
    # Create migrations for both apps at once
    call_command("makemigrations", "test_app", "regular_app", interactive=False)
    
    # Check tenant app (test_app) - should have RLS
    tenant_app_config = apps.get_app_config("test_app")
    tenant_migrations_dir = os.path.join(tenant_app_config.path, "migrations")
    tenant_files = [f for f in os.listdir(tenant_migrations_dir) if f.startswith("0001_")]
    assert len(tenant_files) == 1
    
    with open(os.path.join(tenant_migrations_dir, tenant_files[0]), "r") as f:
        tenant_content = f.read()
        assert "CREATE POLICY" in tenant_content
    
    # Check regular app (regular_app) - should NOT have RLS
    regular_app_config = apps.get_app_config("regular_app")
    regular_migrations_dir = os.path.join(regular_app_config.path, "migrations")
    regular_files = [f for f in os.listdir(regular_migrations_dir) if f.startswith("0001_")]
    assert len(regular_files) == 1
    
    with open(os.path.join(regular_migrations_dir, regular_files[0]), "r") as f:
        regular_content = f.read()
        assert "CREATE POLICY" not in regular_content

