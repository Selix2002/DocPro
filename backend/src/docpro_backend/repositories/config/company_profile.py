from sqlalchemy.orm import Session

from docpro_backend.schema import CompanyProfile

from ..base import BaseRepository


class CompanyProfileRepository(BaseRepository[CompanyProfile]):
    model = CompanyProfile

    def get(self) -> CompanyProfile | None:
        return self._session.query(CompanyProfile).first()

    def save(
        self,
        name: str,
        city: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> CompanyProfile:
        profile = self.get()
        if profile is None:
            profile = CompanyProfile(name=name, city=city, email=email, phone=phone)
            self._session.add(profile)
        else:
            profile.name = name
            profile.city = city
            profile.email = email
            profile.phone = phone
        self._session.flush()
        return profile
