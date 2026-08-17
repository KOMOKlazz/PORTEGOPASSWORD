from aiogram.fsm.state import State, StatesGroup


class DraftPostStates(StatesGroup):
    waiting_post_link = State()
    waiting_button_text = State()
    waiting_button_url = State()