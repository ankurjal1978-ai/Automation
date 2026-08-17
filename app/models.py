from dataclasses import dataclass, asdict


@dataclass
class Contact:
    first_name: str
    last_name: str
    email: str
    company: str
    title: str
    website: str
    industry: str
    country: str
    campaign: str
    status: str = "pending"

    def to_dict(self):
        return asdict(self)
