# Do the stuff that needs to be done to load the migrations env; we call functions in migrations.py that does the
# actual work - we do it this way in case people want to write their own alembic env.py file instead of using this one
from opinionated.fastapi.migrations import load_alembic, run_alembic_migrations

# run setup, find models, set up db engine, set up logging, etc
load_alembic()

# run the actual migrations
run_alembic_migrations()
