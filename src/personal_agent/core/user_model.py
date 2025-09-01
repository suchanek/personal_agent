"""
User Model

Comprehensive user dataclass for the Personal Agent system.
Provides a 'ground truth' user profile with extended information.

Author: Eric G. Suchanek, PhD
Last Revision: 2025-08-31 23:36:24
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class User:
    """
    Comprehensive user model with extended profile information.

    Provides a 'ground truth' representation of a user with core identity
    fields and extended profile information including contact details
    and cognitive state tracking.
    """

    # Core identity fields (existing)
    user_id: str
    user_name: str
    user_type: str = "Standard"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())

    # Extended profile fields (new)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[str] = None  # ISO format date string (YYYY-MM-DD)
    delta_year: Optional[int] = (
        None  # Years from birth when writing memories (e.g., 6 for writing as 6-year-old)
    )
    cognitive_state: int = 100  # 0-100 scale, default to 100

    def __post_init__(self):
        """Validate fields after initialization."""
        self.validate_cognitive_state()
        if self.email:
            self.validate_email()
        if self.phone:
            self.validate_phone()
        if self.birth_date:
            self.validate_birth_date()
        if self.delta_year is not None:
            self.validate_delta_year()

    def validate_cognitive_state(self) -> bool:
        """
        Ensure cognitive_state is within valid 0-100 range.

        Returns:
            True if valid

        Raises:
            ValueError: If cognitive_state is out of range
        """
        if not isinstance(self.cognitive_state, int):
            raise ValueError("Cognitive state must be an integer")

        if not (0 <= self.cognitive_state <= 100):
            raise ValueError("Cognitive state must be between 0 and 100")

        return True

    def validate_email(self) -> bool:
        """
        Validate email format.

        Returns:
            True if valid

        Raises:
            ValueError: If email format is invalid
        """
        if not self.email:
            return True

        # Basic email validation regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.email):
            raise ValueError(f"Invalid email format: {self.email}")

        return True

    def validate_phone(self) -> bool:
        """
        Validate phone number format (flexible format support).

        Returns:
            True if valid

        Raises:
            ValueError: If phone format is invalid
        """
        if not self.phone:
            return True

        # Remove common separators and spaces
        cleaned_phone = re.sub(r"[\s\-\(\)\+\.]", "", self.phone)

        # Check if it contains only digits (after cleaning)
        if not cleaned_phone.isdigit():
            raise ValueError(
                f"Phone number must contain only digits and common separators: {self.phone}"
            )

        # Check reasonable length (7-15 digits)
        if not (7 <= len(cleaned_phone) <= 15):
            raise ValueError(f"Phone number must be between 7-15 digits: {self.phone}")

        return True

    def validate_birth_date(self) -> bool:
        """
        Validate birth date format and reasonableness.

        Returns:
            True if valid

        Raises:
            ValueError: If birth date format is invalid or unreasonable
        """
        if not self.birth_date:
            return True

        try:
            # Parse the date string in ISO format (YYYY-MM-DD)
            birth_datetime = datetime.fromisoformat(self.birth_date)

            # Check if the date is not in the future
            if birth_datetime.date() > datetime.now().date():
                raise ValueError(
                    f"Birth date cannot be in the future: {self.birth_date}"
                )

            # Allow dates back to year 1 AD (no year 0 in Gregorian calendar)
            if birth_datetime.year < 1:
                raise ValueError(
                    f"Birth date cannot be before year 1 AD: {self.birth_date}"
                )

            return True

        except ValueError as e:
            if "Birth date cannot" in str(e):
                # Re-raise our custom validation errors
                raise e
            else:
                # Handle datetime parsing errors
                raise ValueError(
                    f"Invalid birth date format. Expected YYYY-MM-DD, got: {self.birth_date}"
                )

    def validate_delta_year(self) -> bool:
        """
        Validate delta_year (years from birth when writing memories).

        Returns:
            True if valid

        Raises:
            ValueError: If delta_year is invalid
        """
        if self.delta_year is None:
            return True

        if not isinstance(self.delta_year, int):
            raise ValueError("Delta year must be an integer")

        if self.delta_year < 0:
            raise ValueError(f"Delta year cannot be negative: {self.delta_year}")

        # Check reasonable upper bound (150 years)
        if self.delta_year > 150:
            raise ValueError(
                f"Delta year cannot be more than 150 years: {self.delta_year}"
            )

        # If birth_date is provided, validate that delta_year + birth_year doesn't exceed current year
        if self.birth_date:
            try:
                birth_datetime = datetime.fromisoformat(self.birth_date)
                memory_year = birth_datetime.year + self.delta_year
                current_year = datetime.now().year

                if memory_year > current_year:
                    raise ValueError(
                        f"Delta year {self.delta_year} from birth year {birth_datetime.year} "
                        f"results in memory year {memory_year}, which is in the future"
                    )
            except ValueError as e:
                if "results in memory year" in str(e):
                    # Re-raise our custom validation error
                    raise e
                # If birth_date parsing fails, we'll let that be handled by validate_birth_date

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User to dictionary for JSON storage.

        Returns:
            Dictionary representation of the user
        """
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_type": self.user_type,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "birth_date": self.birth_date,
            "delta_year": self.delta_year,
            "cognitive_state": self.cognitive_state,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Create User from dictionary (for loading from JSON).

        Args:
            data: Dictionary containing user data

        Returns:
            User instance
        """
        # Handle backward compatibility - set defaults for missing fields
        return cls(
            user_id=data["user_id"],
            user_name=data.get("user_name", data["user_id"]),
            user_type=data.get("user_type", "Standard"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_seen=data.get("last_seen", datetime.now().isoformat()),
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            birth_date=data.get("birth_date"),
            delta_year=data.get("delta_year"),
            cognitive_state=data.get("cognitive_state", 50),
        )

    def update_last_seen(self):
        """Update the last_seen timestamp, respecting delta_year if set."""
        current_time = datetime.now()
        
        # If delta_year is set and we have a birth_date, adjust the year
        if self.delta_year is not None and self.delta_year > 0 and self.birth_date:
            try:
                birth_datetime = datetime.fromisoformat(self.birth_date)
                memory_year = birth_datetime.year + self.delta_year
                
                # Create timestamp with memory year but current month/day/time
                adjusted_time = current_time.replace(year=memory_year)
                self.last_seen = adjusted_time.isoformat()
            except (ValueError, OverflowError):
                # If there's any issue with date calculation, fall back to current time
                self.last_seen = current_time.isoformat()
        else:
            # Normal case: use current time
            self.last_seen = current_time.isoformat()

    def update_profile(self, **kwargs) -> Dict[str, Any]:
        """
        Update user profile fields with validation.

        Args:
            **kwargs: Fields to update

        Returns:
            Dictionary with update results
        """
        updated_fields = []
        errors = []

        # Define updatable fields
        updatable_fields = {
            "user_name",
            "user_type",
            "email",
            "phone",
            "address",
            "birth_date",
            "delta_year",
            "cognitive_state",
        }

        for field, value in kwargs.items():
            if field not in updatable_fields:
                errors.append(f"Field '{field}' is not updatable")
                continue

            try:
                # Set the field
                setattr(self, field, value)

                # Validate specific fields
                if field == "cognitive_state":
                    self.validate_cognitive_state()
                elif field == "email" and value:
                    self.validate_email()
                elif field == "phone" and value:
                    self.validate_phone()
                elif field == "birth_date" and value:
                    self.validate_birth_date()
                elif field == "delta_year" and value is not None:
                    self.validate_delta_year()

                updated_fields.append(field)

            except ValueError as e:
                # Revert the field if validation failed
                errors.append(f"Validation error for '{field}': {str(e)}")

        # Update last_seen if any fields were successfully updated
        if updated_fields:
            self.update_last_seen()

        return {
            "success": len(updated_fields) > 0,
            "updated_fields": updated_fields,
            "errors": errors,
        }

    def get_profile_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the user's profile completeness.

        Returns:
            Dictionary with profile completion information
        """
        total_fields = (
            6  # email, phone, address, birth_date, delta_year, cognitive_state
        )
        completed_fields = 0

        if self.email:
            completed_fields += 1
        if self.phone:
            completed_fields += 1
        if self.address:
            completed_fields += 1
        if self.birth_date:
            completed_fields += 1
        if self.delta_year is not None:
            completed_fields += 1
        # cognitive_state always has a value (default 50)
        completed_fields += 1

        return {
            "completion_percentage": (completed_fields / total_fields) * 100,
            "completed_fields": completed_fields,
            "total_fields": total_fields,
            "missing_fields": [
                field
                for field, value in [
                    ("email", self.email),
                    ("phone", self.phone),
                    ("address", self.address),
                    ("birth_date", self.birth_date),
                    ("delta_year", self.delta_year),
                ]
                if not value
            ],
        }

    def __str__(self) -> str:
        """String representation of the user."""
        # Include core fields and key optional fields for readability
        parts = [f"id={self.user_id}", f"name={self.user_name}", f"type={self.user_type}"]
        
        if self.email:
            parts.append(f"email={self.email}")
        if self.cognitive_state != 100:  # Only show if not default
            parts.append(f"cognitive_state={self.cognitive_state}")
        if self.delta_year is not None:
            parts.append(f"delta_year={self.delta_year}")
            
        return f"User({', '.join(parts)})"

    def __repr__(self) -> str:
        """Detailed string representation of the user."""
        return (
            f"User("
            f"user_id='{self.user_id}', "
            f"user_name='{self.user_name}', "
            f"user_type='{self.user_type}', "
            f"created_at='{self.created_at}', "
            f"last_seen='{self.last_seen}', "
            f"email={repr(self.email)}, "
            f"phone={repr(self.phone)}, "
            f"address={repr(self.address)}, "
            f"birth_date={repr(self.birth_date)}, "
            f"delta_year={repr(self.delta_year)}, "
            f"cognitive_state={self.cognitive_state}"
            f")"
        )
