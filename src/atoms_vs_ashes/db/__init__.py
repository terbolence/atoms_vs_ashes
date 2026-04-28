# man_hours: 0.2
"""Database package.

Importing this package side-effect-registers the ORM models declared in
``models_analytics``, ``models_analytics_part2`` and small extension
modules on the same
``Base.metadata`` exposed by ``models``. Alembic's autogenerate and
``Base.metadata.create_all`` therefore see the full schema without the
calling code having to import the analytics modules explicitly.
"""

from atoms_vs_ashes.db import models  # noqa: F401
from atoms_vs_ashes.db import models_analytics  # noqa: F401
from atoms_vs_ashes.db import models_analytics_part2  # noqa: F401
from atoms_vs_ashes.db import models_natural_hazards_extra  # noqa: F401
from atoms_vs_ashes.db import models_scoring_definitions  # noqa: F401
