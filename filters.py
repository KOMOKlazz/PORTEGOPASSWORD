from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject


class IsAdmin(BaseFilter):
    """
    Пропускает апдейт дальше по роутеру только если его отправил админ.
    admin_id приходит из workflow_data (передан в dp.start_polling(admin_id=...)).
    Если фильтр не проходит, aiogram просто передаёт апдейт следующему роутеру —
    поэтому весь admin_panel.router безопасно вешать на этот фильтр.
    """

    async def __call__(self, event: TelegramObject, admin_id: int) -> bool:
        user = getattr(event, "from_user", None)
        return user is not None and user.id == admin_id