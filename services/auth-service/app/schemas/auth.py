from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "usuario@example.com",
                "password": "Strong-password1",
            }
        }
    }

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, password: str) -> str:
        requirements = (
            (any(character.islower() for character in password), "lowercase letter"),
            (any(character.isupper() for character in password), "uppercase letter"),
            (any(character.isdigit() for character in password), "number"),
        )
        missing = [label for present, label in requirements if not present]
        if missing:
            raise ValueError(
                "Password must include a lowercase letter, an uppercase letter, and a number"
            )
        return password


class LoginRequest(RegisterRequest):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr


class RegisterResponse(UserResponse):
    access_token: str
    token_type: str = "bearer"
