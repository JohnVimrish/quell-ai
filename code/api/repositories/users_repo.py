from dataclasses import dataclass
from api.repositories.base import BaseRepository

@dataclass
class User:
    id: int | None
    email: str
    password_hash: str

class UsersRepository(BaseRepository):
    def create(self, email: str, password_hash: str):
        rows = self.execute("users_create", [email, password_hash])
        return rows[0] if rows else None

    def get_by_email(self, email: str):
        rows = self.execute("users_by_email", [email])
        return rows[0] if rows else None
