from app.db import AsyncSession
from app.db.models import CoreConfig
from app.db.crud import create_core_config, modify_core_config, remove_core_config, get_core_configs
from app.models.admin import AdminDetails
from app.models.core import CoreCreate, CoreResponseList, CoreResponse
from app.backend import core_manager
from app.operation import BaseOperator
from app.utils.logger import get_logger


logger = get_logger("core-operator")


class CoreOperation(BaseOperator):
    async def create_core(self, db: AsyncSession, new_core: CoreCreate, admin: AdminDetails) -> CoreResponse:
        try:
            db_core = await create_core_config(db, new_core)
            await core_manager.update_core(db_core)
        except Exception as e:
            await db.rollback()
            self.raise_error(message=e, code=400)

        logger.info(f'Core config "{db_core.id}" created by admin "{admin.username}"')

        return CoreResponse.model_validate(db_core)

    async def get_all_cores(self, db: AsyncSession, offset: int, limit: int) -> CoreResponseList:
        db_cores, count = await get_core_configs(db, offset, limit)
        return CoreResponseList(cores=db_cores, count=count)

    async def modify_core(
        self, db: AsyncSession, core_id: int, modified_core: CoreCreate, admin: AdminDetails
    ) -> CoreConfig:
        db_core = await self.get_validated_core_config(db, core_id)
        db_core = await modify_core_config(db, db_core, modified_core)
        try:
            db_core = await modify_core_config(db, db_core, modified_core)
            await core_manager.update_core(db_core)
        except Exception as e:
            await db.rollback()
            self.raise_error(message=e, code=400)

        logger.info(f'Core config "{db_core.name}" modified by admin "{admin.username}"')
        return db_core

    async def delete_core(self, db: AsyncSession, core_id: int, admin: AdminDetails) -> None:
        if core_id == 1:
            self.raise_error(message="Cannot delete default core config", code=403)

        db_core = await self.get_validated_core_config(db, core_id)

        await remove_core_config(db, db_core)

        logger.info(f'core config "{db_core.name}" deleted by admin "{admin.username}"')
