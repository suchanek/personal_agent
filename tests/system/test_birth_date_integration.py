#!/usr/bin/env python3
"""
Test Birth Date and Delta Year Integration

Simple test to verify that the birth_date and delta_year fields are properly integrated
across the user management system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.user_model import User
from datetime import datetime


def test_user_model_birth_date_and_delta_year():
    """Test User model with birth_date and delta_year fields."""
    print("Testing User model with birth_date and delta_year...")
    
    # Test creating user with birth_date and delta_year
    user = User(
        user_id="test_user",
        user_name="Test User",
        birth_date="1990-05-15",
        delta_year=6
    )
    
    print(f"✓ Created user: {user}")
    print(f"✓ Birth date: {user.birth_date}")
    print(f"✓ Delta year: {user.delta_year}")
    
    # Test to_dict includes both fields
    user_dict = user.to_dict()
    assert "birth_date" in user_dict
    assert "delta_year" in user_dict
    assert user_dict["birth_date"] == "1990-05-15"
    assert user_dict["delta_year"] == 6
    print(f"✓ to_dict() includes birth_date: {user_dict['birth_date']}")
    print(f"✓ to_dict() includes delta_year: {user_dict['delta_year']}")
    
    # Test from_dict includes both fields
    user2 = User.from_dict(user_dict)
    assert user2.birth_date == "1990-05-15"
    assert user2.delta_year == 6
    print(f"✓ from_dict() preserves birth_date: {user2.birth_date}")
    print(f"✓ from_dict() preserves delta_year: {user2.delta_year}")
    
    # Test profile summary includes both fields
    summary = user.get_profile_summary()
    print(f"✓ Profile summary: {summary}")
    
    # Test updating both fields
    result = user.update_profile(birth_date="1985-12-25", delta_year=10)
    assert result["success"]
    assert "birth_date" in result["updated_fields"]
    assert "delta_year" in result["updated_fields"]
    assert user.birth_date == "1985-12-25"
    assert user.delta_year == 10
    print(f"✓ Updated birth_date: {user.birth_date}")
    print(f"✓ Updated delta_year: {user.delta_year}")
    
    print("✓ All User model tests passed!")


def test_birth_date_validation():
    """Test birth_date validation."""
    print("\nTesting birth_date validation...")
    
    # Test valid date
    user = User(user_id="test", user_name="Test User", birth_date="1990-01-01")
    print("✓ Valid date accepted")
    
    # Test invalid format
    try:
        user = User(user_id="test", user_name="Test User", birth_date="invalid-date")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Invalid format rejected: {e}")
    
    # Test future date
    try:
        future_date = str(datetime.now().year + 1) + "-01-01"
        user = User(user_id="test", user_name="Test User", birth_date=future_date)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Future date rejected: {e}")
    
    # Test very old date
    try:
        user = User(user_id="test", user_name="Test User", birth_date="1800-01-01")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Very old date rejected: {e}")
    
    print("✓ All birth_date validation tests passed!")


def test_delta_year_validation():
    """Test delta_year validation."""
    print("\nTesting delta_year validation...")
    
    # Test valid delta_year
    user = User(user_id="test", user_name="Test User", birth_date="1990-01-01", delta_year=6)
    print("✓ Valid delta_year accepted")
    
    # Test negative delta_year
    try:
        user = User(user_id="test", user_name="Test User", delta_year=-5)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Negative delta_year rejected: {e}")
    
    # Test very large delta_year
    try:
        user = User(user_id="test", user_name="Test User", delta_year=200)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Very large delta_year rejected: {e}")
    
    # Test delta_year that results in future date
    try:
        current_year = datetime.now().year
        birth_year = current_year - 10
        future_delta = 15  # This would put memory year in the future
        user = User(user_id="test", user_name="Test User", 
                   birth_date=f"{birth_year}-01-01", delta_year=future_delta)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Future memory year rejected: {e}")
    
    # Test valid scenario: 6-year-old born in 1960 writing memories as if in 1966
    user = User(user_id="test", user_name="Test User", 
               birth_date="1960-01-01", delta_year=6)
    print("✓ Valid scenario: 6-year-old born in 1960 writing memories from 1966")
    
    print("✓ All delta_year validation tests passed!")


def test_delta_year_last_seen():
    """Test that update_last_seen respects delta_year."""
    print("\nTesting delta_year-aware last_seen updates...")
    
    # Test user with delta_year - should get adjusted timestamp
    user = User(user_id="test", user_name="Test User", 
               birth_date="1960-01-01", delta_year=6)
    
    # Update last_seen
    user.update_last_seen()
    
    # Parse the last_seen timestamp
    last_seen_dt = datetime.fromisoformat(user.last_seen)
    
    # Should be 1966 (1960 + 6)
    expected_year = 1966
    assert last_seen_dt.year == expected_year, f"Expected year {expected_year}, got {last_seen_dt.year}"
    print(f"✓ Delta_year user last_seen year: {last_seen_dt.year} (expected: {expected_year})")
    
    # Test user without delta_year - should get current year
    user_normal = User(user_id="test2", user_name="Test User 2")
    user_normal.update_last_seen()
    
    last_seen_normal = datetime.fromisoformat(user_normal.last_seen)
    current_year = datetime.now().year
    assert last_seen_normal.year == current_year, f"Expected current year {current_year}, got {last_seen_normal.year}"
    print(f"✓ Normal user last_seen year: {last_seen_normal.year} (expected: {current_year})")
    
    print("✓ All delta_year last_seen tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Birth Date and Delta Year Integration Test")
    print("=" * 60)
    
    try:
        test_user_model_birth_date_and_delta_year()
        test_birth_date_validation()
        test_delta_year_validation()
        test_delta_year_last_seen()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("Birth date and delta year fields have been successfully integrated!")
        print("Users can now write memories from a specific age perspective!")
        print("Last seen timestamps respect the delta_year setting!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
